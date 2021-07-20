import os
import sys
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
import time
from tqdm import tqdm
from bs4 import BeautifulSoup
import re

# Tested on ChromeDriver 89.0.4389.23
from webdriver import WebDriver
from constants import SCROLL_LIMIT, UNDETECT_LIMIT

def save_image_from_url(url, savePath, fileName=None):
    """ Saves a single image given a url.

    :fileName: name of the image file to be saved. Defaults to the given name derived from the url.
    """
    if fileName is None: 
        fileName = url.split('/')[-1].split('?')[0]
    fullFilePath = os.path.join(savePath, fileName)

    if os.path.isfile(fullFilePath):
        name, ext = os.path.splitext(fileName)
        copyval = re.search(r"\((.*)\)", name)
        if copyval is None:
            fileName = name + "(1)" + ext
        else:
            copyval = int(copyval)+1
            fileName = re.sub(r"\((.*)\)", r"(%d)" % copyval, name) + ext
        fullFilePath = os.path.join(savePath, fileName)

    try: 
        image = urlopen(url)
        Path(savePath).mkdir(parents=True, exist_ok=True) # makes directory if it doesn't exist
        try:
            with open(fullFilePath, 'wb') as output:
                output.write(image.read())
            return 1,0,0
        except Exception as e:
            print(e)
            return 0,1,0
    except HTTPError:
        # TODO: Log all images unable to be saved from 403 Forbidden: native and converted urls
        # TODO: Silent mode
        # print(e)
        return 0,1,0  
    except URLError:
        return 0,1,0
                    
def save_image_urls(urls, savePath):
    """Saves a list of images and prints the numbers of successes, failures, and repeats."""

    print("> Savings images...")
    success = 0
    fail = 0
    repeat = 0
    for url in tqdm(urls):
        s, f, r = save_image_from_url(url, savePath)
        success += s
        fail += f
        repeat += r
    print("> Savings images complete.")
    print("Successful: {} \nFailures  : {} \nRepeats   : {}".format(success, fail, repeat))


def full_search_url(query, searchURL, spaceEncoding):
    """  Creates a full search URL for the given query
    """
    return searchURL + query.replace(' ',spaceEncoding)


def scroll_to_element(driver, expectation):
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.common.exceptions import NoSuchElementException

    print("> Scrolling down the page...")
    detected = False
    count = 0
    while not detected:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.5)
        try:
            element = driver.find_element(expectation[0], expectation[1])
            detected = True
        except NoSuchElementException as e:
            count += 1
            if count < UNDETECT_LIMIT:
                pass
            else:
                print(e.msg) # Logging system
                print("Exceeded the UNDETECT_LIMIT for the expectation.")
                sys.exit()
        except Exception as e:
            print(e)
            sys.exit()
    
    print("Element found: ", end='')
    element = driver.find_element(expectation[0],expectation[1])
    print(element.get_attribute("outerHTML").replace(element.get_attribute("innerHTML"),''))
    print("> Scroll complete")


def scroll_to_bottom(driver):
    # Scrolls to the bottom of the page
    new_height = driver.execute_script("return document.body.scrollHeight")
    prev_height = 0
    print("> Scrolling to the bottom of the page...")
    while((new_height != prev_height) and (new_height < SCROLL_LIMIT)):
        prev_height = new_height
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        print("  Page height: ",new_height, sep='',end='\r',flush=True)
    print("\n> Scroll complete")
