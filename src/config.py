class Config:
    def __init__(self, search_keyword="Hello", file_length=10, image_quality="orig", download=True, offset=0):
        self.search_keyword = search_keyword
        self.file_length = file_length
        self.image_quality = image_quality  # e.g., 'orig', '736x', '474x'
        self.bookmarks = ""
        self.download = download
        self.offset = offset

    @property
    def search_url(self):
        # Base URL for Playwright to start the navigation
        return f"https://www.pinterest.com/search/pins/?q={self.search_keyword}"
