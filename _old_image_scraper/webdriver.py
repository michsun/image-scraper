import sys
import time
from selenium import webdriver
from selenium.common.exceptions import InvalidSessionIdException

class WebDriver:

    NUMBER_OF_INSTANCES = 0
    # TODO: Enable multithreading.
    
    def __init__(self, path, browser): 
        self.path = path
        self.browser = browser
        self.NUMBER_OF_INSTANCES += 1
        self.instance = self.NUMBER_OF_INSTANCES
        self.driver = self._initialise_driver()


    def _initialise_driver(self):
        print("> Initialising driver...")
        if (self.browser == "Chrome"):

            from selenium.webdriver.chrome.options import Options
            chrome_options = Options()
            chrome_options.add_argument('--headless')

            try: 
                driver = webdriver.Chrome(executable_path=self.path, options=chrome_options)
                driver.set_window_size(1920,1080)
                print("> \'{}\' Driver initialised. Webdriver instance={}".format(self.browser, self.instance))
                return driver
            except Exception as e:
                print(e)
                print("The webdriver cannot be located. Please check the path: \n", self.path)
                sys.exit()

        if (self.browser == "Safari"):
            driver = webdriver.Safari()
            print("Safari executed")
            #TODO: Complete safari webdriver execution
            sys.exit()

            
    def __del__(self):
        try:
            self.driver.close()
            print("A \'{}\' Driver has been deleted; WebDriver instance={} has been removed.".format(self.browser, self.instance))
        except InvalidSessionIdException as e:
            pass
    
    def get(self, url, sleep):
        self.driver.get(url)
        time.sleep(sleep) 

    def get_driver(self):
        return self.driver


# from constants import WEBDRIVER_PATH

# webdriver = WebDriver(WEBDRIVER_PATH, "Safari")
# driver = webdriver.get_driver()

