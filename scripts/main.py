import json
import os
from re import search
import sys

from typing import Dict

from config import Config, reset_defaults
from image import ImagesDownloader
from image_search import GoogleSearch, PinterestSearch

from test_utils import timer

class ImageScraper:
    
    def __init__(self):
        self.config : Config = self._load_config()
        self.image_config : Dict = self.config.image
        self.search_config : Dict[str, Config] = self._create_search_config()
        self.webdriver_config : Config = self._create_webdriver_config()
        
    def _load_config(self) -> Config:
        """Loads config.json and creats appropriate config files."""
        with open("scripts/config.json", 'r', encoding='utf-8') as file:
            return Config(json.load(file))
            
    def _create_image_config(self) -> Config:
        """Creates a Config object for the ImageDownloader class."""
        try:
            image_config = Config(self.config.image)
            # TODO: Perform valid checks on image configurations.
            return image_config
        except AttributeError as e:
            print(e)
            sys.exit(1)
        except Exception as e:
            print(e)
            sys.exit(1)
            
    def _create_search_config(self) -> Dict[str, Config]:
        """Creates a Config object for the ImageSearch class."""
        try: 
            search_config = self.config.search
            search_config = { k: Config(v) for k,v in search_config.items() }
            return search_config
        except AttributeError as e:
            print(e)
            sys.exit(1)
        except Exception as e:
            print(e)
            sys.exit(1)

    def _create_webdriver_config(self) -> Config:
        """Creates a webdriver Config object."""
        try:
            webdriver_config = Config(self.config.webdriver)
            webdriver_path = webdriver_config.path
            # TODO: Add additional check for the webdriver.
            if webdriver_path == "":
                raise Exception("Load Error: The path for the webdriver has not been set. Please set your webdriver path in config.py")
            if not os.path.isfile(webdriver_config.path):
                raise Exception("Load Error: No file was found at webdriver path '{webdriver_config.path}' \nPlease download webdriver and set the path in config.py.")
            return webdriver_config
        except AttributeError as e:
            print(e)
            sys.exit(1)
        except Exception as e:
            print(e)
            sys.exit(1)
    
    def get_driver_config(self, search_engine) -> Dict:
        driver_config = self.config.webdriver
        driver_config.update(self.config.search[search_engine])
        return driver_config
    

def download_images(args, config : ImageScraper) -> None:
    if args.url:
        ImagesDownloader(config=config.image_config).download_image(image_url=args.url)
    if args.pinterest_board:
        driver_config = config.get_driver_config("Pinterest")
        pinterest = PinterestSearch(driver_config=driver_config, url=args.pinterest_board)
        image_urls = []
        image_urls += pinterest.get_board_image_urls()
        board_name = pinterest.get_details()["query"]
        
        downloader = ImagesDownloader(config=config.image_config, subfolder=board_name)
        downloader.download_queue(image_urls=image_urls)

def search_and_scrape(args, config) -> None:
    image_urls = []
    search_engines = []
    
    if args.search:
        if args.google:
            search_engines.append(GoogleSearch(args.search))
        if args.pinterest:
            search_engines.append(PinterestSearch(args.search))
        if len(search_engines) == 0:
            # Default search engine
            search_engines.append(GoogleSearch(args.search))
        
def parse(config):
    """Process command line arguments and execute the given command."""
    from argparse import ArgumentParser
    
    parser = ArgumentParser(description="Image Scraper command line utility.")
    subparsers = parser.add_subparsers(title="Commands")
    
    search_parser = subparsers.add_parser("search", aliases=["srch"],
                                          description="Searches for images and downloads them.",
                                          help="search and download images given a query")
    search_parser.add_argument('-g', '--google', help='search query on google', action='store_true',required='--search')
    search_parser.add_argument('-p', '--pinterest', help='search query on pinterest', action='store_true', required='--search')
    search_parser.add_argument('-s', '--search', help='query to search for on indicated search engine(s)', type=str, required=True)
    search_parser.set_defaults(func=search_and_scrape)

    download_parser = subparsers.add_parser("download", aliases=["dl"],
                                           description="Downloads images given a url",
                                           help="downloads images given url(s)")
    download_parser.add_argument('-pb', '--pinterest-board', help='scrape images from a pinterest board url', type=str, required=False)
    download_parser.add_argument('-url', '--url', help='image url to download', type=str,required=False)
    download_parser.add_argument('-v', '--verbose', help='verbose', action='store_true', required=False)
    download_parser.set_defaults(func=download_images)
    
    args = parser.parse_args()
    args.func(args, config)


def main():
    config = ImageScraper()
    parse(config)

if __name__ == "__main__":
    main()