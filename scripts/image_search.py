"""
Process:
1. User inputs search query and selects the appropriate search engine
2. URL for the appropriate search engine is generated
"""
import asyncio
import os
import re
import time
import urllib
from bs4 import BeautifulSoup

from typing import Dict

from webdriver import WebDriver

class ImageSearch:
    """Base class for image scrapers."""
    
    def __init__(self, query, driver_config : Dict, verbose=False):
        self._query : str = query
        self._verbose : bool = verbose
        self._driver_config : Dict = driver_config
        self._driver : WebDriver = None # Webdriver instance
        self._debug_success : int = 0
        self._debug_fail : int = 0
    
    def generate_url(self, base_url, quote_via) -> str:
        """Returns the full search URL for the search engine."""
        return base_url + urllib.parse.urlencode({'q': self._query}, quote_via=quote_via)
        
    def _create_webdriver(self) -> None:
        """Instantiates a WebDriver object."""
        self._driver = WebDriver(self._driver_config)
        self._driver.get(self._url)
        time.sleep(0.5)

    def get_details(self):
        deets = {
            "query": self._query,
            "image_urls": {"successful": self._debug_success, "fail": self._debug_fail }
        }
        return deets


class GoogleSearch(ImageSearch):
    
    def __init__(self, driver_config : Dict, query, url=None, verbose=False):
        super().__init__(query, driver_config, verbose)
        self._quote_via = urllib.parse.quote_plus
        if url is None:
            self._url : str = self.generate_url()
        else:
            self._url : str = None
        
    def generate_url(self) -> str:
        """Returns the full search url for the search engine."""
        base_url = "https://www.google.com/search?tbm=isch&"
        return super().generate_url(base_url, self._quote_via)
    
    def count_images(self, source_html) -> int:
        """Returns count of images."""
        bs = BeautifulSoup(source_html, 'lxml')
        image_elements = bs.find_all("div", {"class": "BUooTd"})
        return len(image_elements)
    
    async def get_search_image_urls(self):
        """Scrapes Google Search and returns a list of urls for the images."""
        super()._create_webdriver()
        
        self._driver.scroll_to_bottom()
        # Clicks on "Show more results" to grab more images
        xpath = "//*[@id=\"islmp\"]/div/div/div/div[1]/div[2]/div[2]/input"
        await self._driver.click_and_get_elements(click_by="xpath", click_condition=xpath)
        await self._driver.scroll_to_bottom()
        
        source_html = self._driver.get_page_source()
        n_detected = self.count_images(source_html)
        print(f"> Number of images found: {n_detected}")
        # Clicks on images and get full resolution images
        img_xpath = "//*[@id=\"Sva75c\"]/div/div/div[3]/div[2]/c-wiz/div/div[1]/div[1]/div[2]/div[1]/a/img"
        click_class = "BUooTd"
        image_elements  = await self._driver.click_and_get_elements(click_by="class name",
                                                              click_condition=click_class,
                                                              save_xpath=img_xpath,
                                                              save_attr="src",
                                                              save_condition_regex="(^https?://)(?!encrypted-tbn0.gstatic.com)")

        image_urls = [ re.search('src="(.*?)"', element).group(1) for element in image_elements ] # Implement re.search() check before .group(1)
        
        self._debug_success = len(image_urls)
        self._debug_fail = n_detected - self._debug_success

        return image_urls
        

class PinterestSearch(ImageSearch):
    
    def __init__(self, driver_config : Dict, query=None, url=None, verbose=False):
        super().__init__(query=query, driver_config=driver_config, verbose=verbose)
        self._quote_via = urllib.parse.quote
        if url is None:
            self._url : str = self.generate_url()
        else:
            self._url : str = url
        self.source_html = None
    
    def generate_url(self) -> str:
        """Returns the full search url for the search engine."""
        base_url = "https://www.pinterest.com/search/pins/?"
        return super().generate_url(base_url, self._quote_via)
    
    async def initialise_source_html(self, scroll=True, expectation=None) -> str:
        super()._create_webdriver()

        if expectation is not None:
            await self._driver.scroll_to_element(expectation)
        elif scroll:
            await self._driver.scroll_to_bottom()
        return self._driver.get_page_source()
    
    async def get_board_image_urls(self, board_name=None, save_source=False):
        print("> Fetching pinterest board images...")
        expectation = ("xpath", "//section[@data-test-id='secondaryBoardGrid']")
        self.source_html = await self.initialise_source_html(expectation=expectation)
        
        if board_name == None:
            bs = BeautifulSoup(self.source_html, "lxml")
            board_name = bs.find('h1').text
            board_name = board_name.lower().replace(' ','_')
        self._query = board_name
        
        return await self.get_search_image_urls(board=True)
    
    async def get_search_image_urls(self, board=False):
        """Scrapes Pinterest Search and returns a list of urls for the images."""
        if self.source_html is None:
            self.source_html = await self.initialise_source_html()
        
        bs = BeautifulSoup(self.source_html, "lxml")
        if board:
            bs = bs.find('div', {'class': "Collection"})
        image_elements = bs.find_all('img', {'src': re.compile("https://i.pinimg.com/236x/*")})
        urls = [ e.attrs['src'] for e in image_elements ]
        print(f"> Number of images found: {len(urls)}")
        image_urls = [ os.path.splitext(url)[0].replace('/236x/','/originals/').split('-')[0] + os.path.splitext(url)[1] for url in urls ]
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