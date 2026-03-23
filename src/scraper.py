import os
import time
import json
import random
import urllib.request
import asyncio
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright as async_pw  # Added async import


class Scraper:
    def __init__(self, config):
        self.config = config
        self.results_data = []  # List of dicts: {"id": "...", "url": "..."}
        self.seen_ids = set()

    async def get_urls_async(self):
        """
        Asynchronous version for use in FastAPI/Async environments.
        Uses background interception to gather Pin metadata.
        """
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            async def handle_response(response):
                if "BaseSearchResource" in response.url and response.status == 200:
                    try:
                        resp_json = await response.json()
                        resource_data = resp_json.get("resource_response", {}).get(
                            "data", []
                        )

                        items = (
                            resource_data.get("results", [])
                            if isinstance(resource_data, dict)
                            else resource_data
                        )

                        for pin in items:
                            pin_id = str(pin.get("id"))
                            img_url = (
                                pin.get("images", {})
                                .get(self.config.image_quality, {})
                                .get("url")
                            )

                            if pin_id and img_url and pin_id not in self.seen_ids:
                                self.seen_ids.add(pin_id)
                                self.results_data.append(
                                    {
                                        "id": pin_id,
                                        "url": img_url,
                                        "title": pin.get("title", "No Title"),
                                    }
                                )
                    except:
                        pass

            page.on("response", handle_response)
            print(f"Browsing (Async): {self.config.search_url}")
            await page.goto(self.config.search_url)

            target = int(self.config.file_length)
            timeout_limit = 60
            start_time = asyncio.get_event_loop().time()

            while (
                len(self.results_data) < target
                and (asyncio.get_event_loop().time() - start_time) < timeout_limit
            ):
                await page.mouse.wheel(0, 4000)
                await asyncio.sleep(2)  # Non-blocking sleep
                print(f"Captured {len(self.results_data)} unique pins...")

            await browser.close()
            self._save_to_json()
            return self.results_data[:target]

    def get_urls(self):
        """
        Original Synchronous version for CLI usage.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            def handle_response(response):
                if "BaseSearchResource" in response.url and response.status == 200:
                    try:
                        resp_json = response.json()
                        resource_data = resp_json.get("resource_response", {}).get(
                            "data", []
                        )
                        items = (
                            resource_data.get("results", [])
                            if isinstance(resource_data, dict)
                            else resource_data
                        )

                        for pin in items:
                            pin_id = str(pin.get("id"))
                            img_url = (
                                pin.get("images", {})
                                .get(self.config.image_quality, {})
                                .get("url")
                            )

                            if pin_id and img_url and pin_id not in self.seen_ids:
                                self.seen_ids.add(pin_id)
                                self.results_data.append(
                                    {
                                        "id": pin_id,
                                        "url": img_url,
                                        "title": pin.get("title", "No Title"),
                                    }
                                )
                    except:
                        pass

            page.on("response", handle_response)
            print(f"Browsing: {self.config.search_url}")
            page.goto(self.config.search_url)

            target = int(self.config.file_length)
            timeout_limit = 60
            start_time = time.time()

            while (
                len(self.results_data) < target
                and (time.time() - start_time) < timeout_limit
            ):
                page.mouse.wheel(0, 4000)
                time.sleep(2)  # Blocking sleep (fine for sync CLI)
                print(f"Captured {len(self.results_data)} unique pins...")

            browser.close()
            self._save_to_json()
            return self.results_data[:target]

    def _save_to_json(self):
        output_dir = "results"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        clean_name = self.config.search_keyword.replace(" ", "_")
        filename = f"results_{clean_name}.json"
        file_path = os.path.join(output_dir, filename)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.results_data, f, indent=4, ensure_ascii=False)
            print(f"Full metadata saved to: {file_path}")
        except Exception as e:
            print(f"Failed to save JSON to {file_path}: {e}")

    def download_images(self, data_list):
        folder = os.path.join("photos", self.config.search_keyword.replace(" ", "-"))
        if not os.path.exists(folder):
            os.makedirs(folder)

        for item in data_list:
            url = item["url"]
            ext = url.split(".")[-1].split("?")[0]
            filename = f"{item['id']}.{ext}"
            path = os.path.join(folder, filename)

            if not os.path.exists(path):
                try:
                    time.sleep(random.uniform(0.5, 1.2))
                    urllib.request.urlretrieve(url, path)
                    print(f"Saved: {filename}")
                except Exception as e:
                    print(f"Failed {url}: {e}")