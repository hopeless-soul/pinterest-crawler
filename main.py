from src.config import Config
from src.scraper import Scraper
import json

def main():
    # 1. Setup Configuration
    configs = Config(
        search_keyword="Cyberpunk Aesthetic", 
        file_length=20, 
        image_quality="orig",
        download=False,
    )

    # 2. Initialize Scraper
    pinterest = Scraper(configs)

    # 3. Get Metadata (This fixes your AttributeError)
    print("Starting crawl...")
    results = pinterest.get_urls()

    if results:
        print(f"\nSuccessfully retrieved {len(results)} image links.")
        # Optional: Print the first result to verify structure
        print(f"Sample Entry: {results[0]}")

        # 4. Download the images using the retrieved list
        if configs.download:
            print("Download flag is ENABLED. Starting downloads...")
            pinterest.download_images(results)
        else:
            print("Skipping file download.")
            
    else:
        print("No results found. Check your connection or search term.")

if __name__ == "__main__":
    main()