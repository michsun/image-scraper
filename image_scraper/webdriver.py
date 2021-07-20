import asyncio
import re
import sys
import time

from typing import Dict
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from config import Config

TEST_LIMIT = 50

class WaitTest:
    """A custom Wait condition object to be passed in selenium WebDriverWait object."""
    
    def __init__(self, locator, attribute, value): 
        self._locator = locator
        self._attribute = attribute
        self._value = value

    def __call__(self, driver):
        element = driver.find_element_by_xpath(self._locator)
        pattern = re.compile(self._value)
        if pattern.search(element.get_attribute(self._attribute)):
            return element
        else:
            return False


class WebDriver(Config): 
    
    # Config variables
    # self.browser
    # self.path
    # self.iterate_sleep
    # self.load_sleep
    # self.webdriverwait_sleep
    
    def __init__(self, driver_config : Dict):
        """Initialises the Driver class."""
        super().__init__(driver_config)
        self.driver = self._initialise_driver() # Selenium webdriver object
        
    def __del__(self):
        """Deconstructs the Driver class."""
        self.driver.close()
    
    
    def _initialise_driver(self):
        """Initialises a selenium webdriver."""
        print("> Initialising selenium webdriver...")
        if (self.browser == "Chrome"):
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            # chrome_options.add_argument("--incognito")
            chrome_options.add_argument('--disk-cache-size=0')
            
            try:
                driver = webdriver.Chrome(executable_path=self.path, options=chrome_options)
                driver.set_window_size(1920, 1080)
                driver.delete_all_cookies()
                return driver
            except Exception as e:
                print(f"WebDriver Error: The webdriver cannot be located. Please check the path {self.path}")
                print(e)
                sys.exit()
        else:
            raise Exception("Driver is not of Chrome type")
    
    
    def get(self, url) -> None:
        """Executes driver.get(url)"""
        self.driver.get(url)
    
        
    def get_page_source(self) -> str:
        """Returns the source html for the driver."""
        return self.driver.page_source
    
    
    async def scroll_to_top(self) -> None:
        """Scrolls to the top of the page."""
        self.driver.execute_script("window.scroll(0, 0);")
        await asyncio.sleep(self.load_sleep)
    
    
    async def scroll_to_bottom(self) -> None:
        """Scrolls to the bottom of the page."""
        new_height = self.driver.execute_script("return document.body.scrollHeight")
        prev_height = 0
        # TODO: Implement verbose
        print("> Scrolling to the bottom of the page...")
        while((new_height != prev_height) and (new_height < self.scroll_limit)):
            prev_height = new_height
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(self.load_sleep) # TODO: Check optimal sleep value
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            print("  Page height: ",new_height, sep='',end='\r',flush=True)
        print("\n> Scroll complete")
        
    async def scroll_to_element(self, expectation) -> None:
        """Scrolls down the page until an expected element has been detected."""
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import NoSuchElementException
        
        print("> Scrolling down the page to an element...")
        detected = False
        count = 0
        while not detected:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(self.iterate_sleep)
            try: 
                element = self.driver.find_element(expectation[0], expectation[1])
                detected = True
            except NoSuchElementException as e:
                count += 1
                if count < self.undetect_limit:
                    pass
                else:
                    print("Webdriver Error: Exceeded undetect limit for the expectation.")
                    print(e.msg)
                    sys.exit()
            except Exception as e:
                print(e)
                sys.exit(1)
        print("Element found: ", end='')
        element = self.driver.find_element(expectation[0],expectation[1])
        print(element.get_attribute("outerHTML").replace(element.get_attribute("innerHTML"),''))
        print("> Scroll complete")    
    
    async def click_and_get_elements(self, click_by, click_condition, save_xpath=None, save_attr=None, save_condition_regex=None) -> None:
        """Clicks on an identified element and gets elements as string if condition is given."""
        
        BY = ["id", "xpath", "link text", "partial link text", "name", "tag name", "class name", "css selector"]
        if click_by not in BY:
            raise ValueError("click_by: must be one of %r." % BY)
        
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.common.exceptions import ElementNotInteractableException, ElementClickInterceptedException, TimeoutException
        
        click_elements = self.driver.find_elements(click_by, click_condition)
        save_elements = list()
        exceptions = list()
        print("> Clicking on links...")
        
        # if len(click_elements) > TEST_LIMIT:
        #     click_elements = click_elements[:TEST_LIMIT]
        for element in tqdm(click_elements):
            try:
                if not element.is_displayed() or not element.is_enabled():
                    self.driver.execute_script("arguments[0].scrollIntoView();", element)
                    print("> Scroll executed")
                    await asyncio.sleep(self.load_sleep)
                element.click()
                await asyncio.sleep(self.iterate_sleep)
                if (save_xpath and save_attr and save_condition_regex):
                    try:
                        found_element = WebDriverWait(self.driver, self.webdriverwait_sleep).until(
                            WaitTest(save_xpath, save_attr, save_condition_regex)
                        )
                        save_elements += [found_element.get_attribute("outerHTML").replace(found_element.get_attribute("innerHTML"),'')]
                    except TimeoutException:
                        err = sys.exc_info()[0]
                        err_str = "{} : Did not find element".format(err.__name__)
                        exceptions.append(err_str)
            except ElementNotInteractableException as e:
                err = sys.exc_info()[0]
                err_str = err.__name__
                exceptions.append(err_str)
            except ElementClickInterceptedException as e:
                err = sys.exc_info()[0]
                err_str = err.__name__
                exceptions.append(err_str)
            except Exception as e:
                err = sys.exc_info()[0]
                err_str = err.__name__
                exceptions.append(err_str)
                
        if (save_xpath and save_attr and save_condition_regex):
            return save_elements, exceptions
        # return exceptions
        # print(element.get_attribute("outerHTML").replace(element.get_attribute("innerHTML"),''))