import asyncio
import os
import re
import time
import urllib
from bs4 import BeautifulSoup

from typing import Dict, List

from webdriver import WebDriver

class ImageSearch:
    """Base class for image scrapers."""
    
    def __init__(self, name, query, driver_config : Dict, verbose=False):
        self._name : str = name
        self._query : str = query
        self._verbose : bool = verbose
        self._driver_config : Dict = driver_config
        self._driver : WebDriver = None # Webdriver instance
        self._debug_success : int = 0
        self._debug_fail : int = 0
    
    def generate_url(self, base_url, quote_via) -> str:
        """Returns the full search URL for the search engine."""
        return base_url + urllib.parse.urlencode({'q': self._query}, quote_via=quote_via)
        
    def initialise_webdriver(self, url) -> None:
        """Instantiates a WebDriver object."""
        self._driver = WebDriver(self._driver_config)
        self._driver.get(url)
        time.sleep(0.5)

    def get_details(self):
        deets = {
            "query": self._query,
            "image_urls": {"successful": self._debug_success, "fail": self._debug_fail }
        }
        return deets
    
    def format_message(self, msg : str):
        """Returns a formatted message string."""
        return f"[{self._name.upper()}] {msg}"


class GoogleSearch(ImageSearch):
    
    def __init__(self, driver_config : Dict, query, url=None, verbose=False):
        super().__init__(name="Google", query=query, driver_config=driver_config, verbose=verbose)
        self._quote_via = urllib.parse.quote_plus
        self._name : str = "Google"
        self._url : str = self.generate_url() if url is None else url
        
    def generate_url(self) -> str:
        """Returns the full search url for the search engine."""
        base_url = "https://www.google.com/search?tbm=isch&"
        return super().generate_url(base_url, self._quote_via)
    
    def count_images(self, source_html) -> int:
        """Returns count of images."""
        bs = BeautifulSoup(source_html, 'lxml')
        image_elements = bs.find_all("div", {"class": "BUooTd"})
        return len(image_elements)
    
    async def initialise_source_html(self) -> str:
        """Initialises the class webdriver object and returns the source html."""
        super().initialise_webdriver(self._url)
        print(self.format_message(f"Initialising {self._name} web page..."))
        
        await self._driver.scroll_to_bottom()
        # Clicks on "Show more results" to grab more images
        xpath = "//*[@id=\"islmp\"]/div/div/div/div[1]/div[2]/div[2]/input"
        await self._driver.click_and_get_elements(click_by="xpath", click_condition=xpath)
        await self._driver.scroll_to_bottom()
        
        print(self.format_message(f"Initialising {self._name} web page complete."))
        return self._driver.get_page_source()
    
    async def get_search_image_urls(self) -> List[str]:
        """Scrapes Google Search and returns a list of urls for the images."""
        print(self.format_message(f"Starting search for images of '{self._query}'..."))
        super().initialise_webdriver(self._url)
        
        source_html = await self.initialise_source_html()
        n_detected = self.count_images(source_html)
        
        print(self.format_message(f"Number of google images detected = {n_detected}"))
        # Clicks on images and get full resolution images
        img_xpath = "//*[@id=\"Sva75c\"]/div/div/div[3]/div[2]/c-wiz/div/div[1]/div[1]/div[2]/div[1]/a/img"
        click_class = "BUooTd"
        print(self.format_message(f"Clicking on images and attempting to retrieve urls..."))
        image_elements, exceptions = await self._driver.click_and_get_elements(click_by="class name",
                                                              click_condition=click_class,
                                                              save_xpath=img_xpath,
                                                              save_attr="src",
                                                              save_condition_regex="(^https?://)(?!encrypted-tbn0.gstatic.com)",
                                                              description=self.format_message("Clicking images"))

        image_urls = [ re.search('src="(.*?)"', element).group(1) for element in image_elements if re.search('src="(.*?)"', element) is not None ]
        
        unique_err = list(set(exceptions))
        err_summary = { err_string : exceptions.count(err_string) for err_string in unique_err }
        min_width = 8
        width = max(map(len,unique_err))
        width = max(width, min_width)
        
        print(f"\n {'EXCEPTION TYPE':<{width}} | {'TOTAL':<{width}}")
        print(" {}+{}".format('='*(width+1),'='*(width+1)))
        for k,v in err_summary.items():
            print(f" {k:>{width}} | {v:<{width}}")
        print("")
        
        print(self.format_message(f"Image urls retrieval complete. Number of image urls successfully retrieved = {len(image_urls)}"))
        self._debug_success = len(image_urls)
        self._debug_fail = n_detected - self._debug_success

        return image_urls
        

class PinterestSearch(ImageSearch):
    
    def __init__(self, driver_config : Dict, query=None, url=None, verbose=False):
        super().__init__(name="Pinterest", query=query, driver_config=driver_config, verbose=verbose)
        self._quote_via = urllib.parse.quote
        self._source_html = None
        self._url : str = self.generate_url() if url is None else url
    
    def generate_url(self) -> str:
        """Returns the full search url for the search engine."""
        base_url = "https://www.pinterest.com/search/pins/?"
        return super().generate_url(base_url, self._quote_via)
    
    async def initialise_source_html(self, scroll=True, expectation=None) -> str:
        super().initialise_webdriver(self._url)
        print(self.format_message(f"Initialising {self._name} web page..."))

        if expectation is not None:
            await self._driver.scroll_to_element(expectation)
        elif scroll:
            await self._driver.scroll_to_bottom()
        
        print(self.format_message(f"Initialising {self._name} web page complete."))
        return self._driver.get_page_source()
    
    async def get_board_image_urls(self, board_name=None, save_source=False):
        print(self.format_message(f"Fetching pinterest board image urls..."))
        expectation = ("xpath", "//section[@data-test-id='secondaryBoardGrid']")
        self._source_html = await self.initialise_source_html(expectation=expectation)
        
        if board_name == None:
            bs = BeautifulSoup(self._source_html, "lxml")
            board_name = bs.find('h1').text
            board_name = board_name.lower().replace(' ','_')
        self._query = board_name
        
        return await self.get_search_image_urls(board=True)
    
    async def get_search_image_urls(self, board=False):
        """Scrapes Pinterest Search and returns a list of urls for the images."""
        if self._source_html is None:
            print(self.format_message(f"Starting search for images of '{self._query}'..."))
            self._source_html = await self.initialise_source_html()
        
        bs = BeautifulSoup(self._source_html, "lxml")
        if board:
            bs = bs.find('div', {'class': "Collection"})
        image_elements = bs.find_all('img', {'src': re.compile("https://i.pinimg.com/236x/*")})
        urls = [ e.attrs['src'] for e in image_elements ]
        image_urls = [ os.path.splitext(url)[0].replace('/236x/','/originals/').split('-')[0] + os.path.splitext(url)[1] for url in urls ]
        
        print(self.format_message(f"Image urls retrieval complete. Number of image urls successfully retrieved = {len(image_urls)}"))
        self._debug_success = len(image_urls)
        
        return image_urls


class UnsplashSearch(ImageSearch):
    # TODO
    def __init__(self, query, driver_config, verbose):
        super().__init__(query, driver_config, verbose)
        self._quote_via = urllib.parse.quote # TODO: Check urllib, unsplash is '-'
        

def main():
    pass
    
if __name__ == "__main__":
    # run()
    pass