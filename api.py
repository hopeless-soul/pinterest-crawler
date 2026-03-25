import asyncio
import sys

# 1. SET POLICY IMMEDIATELY (MUST be before ANY asyncio usage)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.config import Config
from src.scraper import Scraper


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    print(f"Event Loop: {type(loop).__name__}")
    yield


app = FastAPI(title="Pinterest Crawler Microservice", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "online", "platform": sys.platform}


@app.get("/scrape")
async def scrape_pinterest(
    q: str = Query(..., description="Search keyword"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0),
    quality: str = Query("orig"),
    download: bool = Query(False),
):
    try:
        configs = Config(
            search_keyword=q,
            file_length=limit,
            image_quality=quality,
            download=download,
            offset=offset,
        )
        pinterest = Scraper(configs)
        print(f"Searching: '{q}' (limit={limit}, offset={offset})")

        results = await pinterest.get_urls_async()
        print(f"Found {len(results)} pins")
        
        return {"success": True, "keyword": q, "count": len(results), "data": results}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # 2. DOUBLE-CHECK before running
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # 3. DISABLE RELOAD on Windows (reload breaks the event loop policy)
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # ← CRITICAL: Disable reload on Windows
        log_level="info"
    )