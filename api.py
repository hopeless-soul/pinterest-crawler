import asyncio
import sys

# 1. Top-level fix (Must be before any other imports)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.config import Config
from src.scraper import Scraper

# 2. Context Manager to ensure the loop is correct during startup
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # This double-checks the loop inside the running worker
    if sys.platform == "win32":
        loop = asyncio.get_event_loop()
        print(f"--- Active Event Loop: {type(loop).__name__} ---")
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
    return {
        "status": "online",
        "loop": type(asyncio.get_event_loop()).__name__,
        "platform": sys.platform,
    }


@app.get("/scrape")
async def scrape_pinterest(
    q: str = Query(..., description="Search keyword"),
    limit: int = Query(10, ge=1, le=100),
    quality: str = Query("orig"),
    download: bool = Query(False),
):
    try:
        configs = Config(
            search_keyword=q,
            file_length=limit,
            image_quality=quality,
            download=download,
        )

        pinterest = Scraper(configs)
        print(f"--- API Request Received: Searching for '{q}' ---")

        # This will now work because the Proactor loop supports subprocesses
        results = await pinterest.get_urls_async()

        if download:
            pinterest.download_images(results)

        return {"success": True, "keyword": q, "count": len(results), "data": results}

    except Exception as e:
        print(f"Internal Error: {str(e)}")
        # Log the full error to console for debugging
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # If running directly via 'python api.py'
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
