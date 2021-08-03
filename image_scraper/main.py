import argparse
import asyncio
import json
import os
from re import search
import sys
import validators

from typing import Dict, List

from config import Config, reset_defaults, update_config_json
from image import ImagesDownloader
from image_search import GoogleSearch, PinterestSearch
from utils import timer
from webdriver import WebDriver

class ImageScraper:
    
    def __init__(self):
        self.config : Config = self._load_config()
        self.image_config : Dict = self.config.image
        self.search_config : Dict[str, Config] = self._create_search_config()
        self.webdriver_config : Config = self._create_webdriver_config()
        
    def _load_config(self) -> Config:
        """Loads config.json and creats appropriate config files."""
        with open("image_scraper/config.json", 'r', encoding='utf-8') as file:
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
                raise Exception("Load Error: The path for the webdriver has not been set. \n\nPlease set your webdriver path in config.py or using 'python image_search config -cd <path_to_webdriver>'")
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

   
def download_image_urls(config : ImageScraper, image_urls : List[str], subfolder : str=None):
    """Creates an ImagesDownloader object and executes downloader given a list of urls."""
    downloader = ImagesDownloader(config=config.image_config, subfolder=subfolder)
    downloader.download_queue(image_urls=image_urls)

def configure(args):
    """Subparser controller: Initialises/configures the image scraper."""
    if args.reset_defaults:
        reset_defaults()
        print("Successfully reset default configurations.")
    if args.chromedriver_path:
        test_config = {"browser": "Chrome", "path": args.chromedriver_path}
        print("Attempting to create a selenium driver...")
        WebDriver(driver_config=test_config)
        print("Test driver created successfully.")
        # If successful
        update_config_json({"webdriver": {"path": args.chromedriver_path}})
        print("\nChromedriver path updated. 'image_scraper' is now ready to use. Run 'python image_scraper -h' for help with commands.")

def download(args) -> None:
    """Subparser controller: Downloads images given url(s)."""
    config = ImageScraper()
    if args.url:
        ImagesDownloader(config=config.image_config).download_image(image_url=args.url)
    if args.pinterest_board:
        driver_config = config.get_driver_config("Pinterest")
        pinterest = PinterestSearch(driver_config=driver_config, url=args.pinterest_board)
        
        loop = asyncio.get_event_loop()
        image_urls = loop.run_until_complete(asyncio.gather(pinterest.get_board_image_urls()))
        
        image_urls = [ url for sublist in image_urls for url in sublist ]
        subfolder_name = args.name if args.name is not None else pinterest.get_details()["query"]
        download_image_urls(config=config, image_urls=image_urls, subfolder=subfolder_name)
    if args.from_file:
        image_urls = []
        subfolder_name = args.name if args.name is not None else os.path.splitext(os.path.basename(args.from_file))[0]
        with open(args.from_file) as file:
            for line in file:
                if validators.url(line.strip()):
                    image_urls.append(line.strip())
        download_image_urls(config=config, image_urls=image_urls, subfolder=subfolder_name) 
        
def scrape(args) -> None:
    """Subparser controller: Retrieves image urls from the search engine and downloads them in a file."""
    config = ImageScraper()
    search_engines = []
    if args.search:
        if args.google:
            driver_config = config.get_driver_config("Google")
            search_engines.append(GoogleSearch(query=args.search, driver_config=driver_config))
        if args.pinterest:
            driver_config = config.get_driver_config("Pinterest")
            search_engines.append(PinterestSearch(query=args.search, driver_config=driver_config))
        if len(search_engines) == 0:
            # Default search engine
            driver_config = config.get_driver_config("Google")
            search_engines.append(GoogleSearch(query=args.search, driver_config=driver_config))
        
        loop = asyncio.get_event_loop()
        image_urls = loop.run_until_complete(asyncio.gather(*(search.get_search_image_urls() for search in search_engines)))
        image_urls = [ url for sublist in image_urls for url in sublist ]
        
        if args.export_urls:
            file_name = "{}_image_urls.txt".format(args.search.lower().replace(' ','_'))
            with open(file_name,'w') as file:
                for url in image_urls:
                        file.write(f"{url}\n")
                print(f"Image urls save in file '{file_name}'.")

        download_image_urls(config=config, image_urls=image_urls, subfolder=args.search)

def file_path(string):
    """Checks if the string is a valid file."""
    if os.path.isfile(string):
        return string
    else:
        raise argparse.ArgumentTypeError(f"{string} is not a valid file.")

        
def main():
    """Process command line arguments and execute the given command."""    
    parser = argparse.ArgumentParser(description="Image Scraper command line utility.")
    subparsers = parser.add_subparsers(title="Commands")
    
    search_parser = subparsers.add_parser("scrape", aliases=["scrp"],
                                          description="Searches for images on a website and downloads them.",
                                          help="search and download images given a query")
    search_parser.add_argument('-g', '--google', help='search query on google', action='store_true',required=False)
    search_parser.add_argument('-p', '--pinterest', help='search query on pinterest', action='store_true', required=False)
    search_parser.add_argument('-e', '--export-urls', help='exports retrieved urls and saves as image_urls.txt', action='store_true', required=False)
    search_parser.add_argument('-s', '--search', help='query to search for on indicated search engine(s)', type=str, required=True)
    search_parser.set_defaults(func=scrape)

    download_parser = subparsers.add_parser("download", aliases=["dl"],
                                           description="Downloads images given a url",
                                           help="downloads images given url(s)")
    download_parser.add_argument('-f', '--from-file', help='download images from file with urls', type=file_path, required=False)
    download_parser.add_argument('-n', '--name', help='name of the subfolder to store downloaded images', type=str, required=False)
    download_parser.add_argument('-pb', '--pinterest-board', help='scrape images from a pinterest board url', type=str, required=False)
    download_parser.add_argument('-url', '--url', help='image url to download', type=str,required=False)
    download_parser.add_argument('-v', '--verbose', help='verbose', action='store_true', required=False)
    download_parser.set_defaults(func=download)
    
    config_parser = subparsers.add_parser("configure", aliases=["config"],
                                          description="ImageScraper Configuration",
                                          help="configure settings of the scraper.")
    config_parser.add_argument('-cd','--chromedriver-path', help='enter the chromedriver path to quickly configure the package', type=file_path, required=False)
    config_parser.add_argument('-r', '--reset-defaults', help='resets the configuration settings (warning: the webdriver path will need to be reset', action='store_true', required=False)
    # config_parser.add_argument('-s', '--setup', help='runs a quick config setup in the command line', action='store_true', required=False)
    config_parser.set_defaults(func=configure)
    
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()