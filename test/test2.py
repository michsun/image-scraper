import sys
import os
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
import time
from tqdm import tqdm
from bs4 import BeautifulSoup
import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

# Tested on ChromeDriver 89.0.4389.23

CHROMEDRIVER_PATH = "drivers/chromedriver"
GOOGLE_SEARCH_URL = "https://www.google.com/search?tbm=isch&q="
GOOGLE_SPACE_ENCODING = '+'
PINTEREST_SEARCH_URL = "https://nl.pinterest.com/search/pins/?q="
PINTEREST_SEARCH_TERM = "typed&term_meta[]={query}%7Ctyped"
PINTEREST_SPACE_ENCODING = "%20"


class Driver:

    def __init__(self): 
        chrome_options = Options()
        chrome_options.add_argument('--headless')

        try:
            self.driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH,options=chrome_options)
        except Exception as e:
            print("The webdriver cannot be located. Please check the path ", CHROMEDRIVER_PATH)
            sys.exit()
        self.driver.set_window_size(1920,1080)
    
    def __del__(self):
        self.driver.close()
    
    def get(self, url, sleep):
        self.driver.get(url)
        time.sleep(sleep)
    

def save_image_from_url(url, savePath, fileName=None):
    """ Saves an image given a url.

    :fileName: name of the image file to be saved. Defaults to the given name derived from the url.
    """
    if fileName is None: 
        # TODO: Double check fileName for google images
        fileName = url.split('/')[-1].split('?')[0]
    fullFilePath = os.path.join(savePath, fileName)

    if not os.path.isfile(fullFilePath):
        try: 
            image = urlopen(url)
            Path(savePath).mkdir(parents=True, exist_ok=True) # makes directory if it doesn't exist
            try:
                while open(fullFilePath, 'wb') as output:
                    output.write(image.read())
                return 1,0,0
            except Exception as e:
                print(e)
                pass
        except HTTPError as e:
            # TODO: Log all images unable to be saved
            # TODO: Silent mode
            print(e)
            return 0,1,0  
                
        # image = open_url(url)
        # if image is not None:
        #     Path(savePath).mkdir(parents=True, exist_ok=True)
        #     output = open(fullFilePath, "wb")
        #     try:
        #         output.write(image.read())
        #     except AttributeError as e:
        #         os.remove(fullFilePath)
        #         raise Exception('No image saved') from e
        #     finally:
        #         output.close()
        # else:
        #     print("Unable to get image from ", url)
    else:
        print(fullFilePath, "already exists.")
        return 0, 0, 1
    
    return


def save_image_urls(urls, savePath):
    print("Downloading images...")
    success = 0
    fail = 0
    repeat = 0
    for url in tqdm(urls):
        s, f, r = save_image_from_url(url, savePath)
        success += s
        fail += f
        repeat += r
    print("Downloading images complete.")
    print("Successful: {} \nFailures  : {} \nRepeats   : {}".format(success, fail, repeat))


def full_search_url(query, searchURL, spaceEncoding):
    """  Creates a full search URL for the given query
    """
    return searchURL + query.replace(' ',spaceEncoding)


def scroll_to_bottom(driver):
    # Scrolls to the bottom of the page
    new_height = driver.execute_script("return document.body.scrollHeight")
    prev_height = 0
    print("Scrolling to the bottom of the page...")
    while(new_height != prev_height):
        prev_height = new_height
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        print("  Page height: ",new_height, sep='',end='\r',flush=True)
    print("\nScroll complete")


def get_google_image_urls(source_html):
    bs = BeautifulSoup(source_html, 'lxml')
    sub_pages = bs.find_all('a', {'href':re.compile('/imgres*')})
    page_urls = [ pg.attrs['href'] for pg in sub_pages]
    
    google_url = "https://www.google.com"
    image_urls = list()

    # TODO: Create separate driver class and functions
    chrome_options = Options()
    chrome_options.add_argument('--headless')

    try:
        driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH,options=chrome_options)
    except Exception as e:
        print("The webdriver cannot be located. Please check the path ", CHROMEDRIVER_PATH)
        sys.exit()

    print("Grabbing image urls...")
    for url in tqdm(page_urls):

        driver.get(google_url+url)
        # input from here
        time.sleep(0.3)
        
        try: 
            image_urls.append(driver.find_element_by_id('imi').get_attribute('src'))
        except Exception as e:
            print(e)
            pass
    print("Image url gathering complete.")

    driver.close()

    return image_urls



def get_google_source_html(url):
    """ Downloads the source html for the google images url. 
    """
    chrome_options = Options()
    chrome_options.add_argument('--headless')

    try:
        driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH,options=chrome_options)
    except Exception as e:
        print("The webdriver cannot be located. Please check the path ", CHROMEDRIVER_PATH)
        sys.exit()
    driver.set_window_size(1920,1080)
    driver.get(url)

    # body = driver.find_element_by_tag_name("body")
    # print("Loading images page: ")
    # while(not EC.visibility_of_element_located((By.CLASS_NAME, 'OuJzKb'))): # Multiclass: 'OuJzKb Yu2Dnd'
    #     body.send_keys(Keys.END)
    #     time.sleep(0.5)
    # print("End of page reached. \nConfirmation: ", driver.find_element_by_class_name('OuJzKb').get_attribute("innerHTML"))

    # Scrolls to bottom of page
    scroll_to_bottom(driver)
    
    # Ensures images are clicked
    elements = driver.find_elements_by_class_name("BUooTd")
    print("Clicking on images...")
    for image in tqdm(elements):
        image.click()
        time.sleep(0.3)
    print("Images link load complete")

    source = driver.page_source
    driver.close()

    return source


def find_pinterest_resource_from_resourceResponses(resourceResponses, name):
    print(len(resourceResponses))
    for obj in resourceResponses:
        if obj["name"] == name:
            return obj


def get_pinterest_pin_urls(source_html, resourceType):
    """ Download images from pins and pinterest boards. 
    
    :resourceType: 
    """
    bs = BeautifulSoup(source_html, 'lxml')
    script = bs.find('script', {'id': 'initial-state'}).decode_contents()
    # sub_pages = bs.find_all('div', {'data-test-pin-id':re.compile('[0-9]')})
    # pins = [ pg.attrs['data-test-pin-id'] for pg in sub_pages]
    
    # pin_url = "https://nl.pinterest.com/pin/"
    import json
    js = json.loads(script)

    # Navigates json grab urls
    resources = js["resourceResponses"]
    resource = find_pinterest_resource_from_resourceResponses(resources, resourceType)
    data = resource["response"]["data"]
    image_urls = [ d["images"]["orig"]["url"] for d in data ]
    
    return image_urls


def get_pinterest_image_urls_from_search(source_html):
    bs = BeautifulSoup(source_html, 'lxml')
    image_elements = bs.find_all('img', {'src': re.compile("https://i.pinimg.com/236x/*")})
    urls = [ e.attrs['src'] for e in image_elements ]
    print(len(urls), " image urls found")
    image_urls = [ os.path.splitext(url)[0].replace('/236x/','/originals/').split('-')[0] + os.path.splitext(url)[1] for url in urls ]
    print(len(image_urls), " urls converted")
    sys.exit()
    return image_urls


def get_pinterest_source_html(url):
    chrome_options = Options()
    chrome_options.add_argument('--headless')

    try:
        driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH,options=chrome_options)
    except Exception as e:
        print("The webdriver cannot be located. Please check the path ", CHROMEDRIVER_PATH)
        sys.exit()
    driver.set_window_size(1920,1080)
    driver.get(url)

    # Scroll to the end of the page
    scroll_to_bottom(driver)
    
    source = driver.page_source
    driver.close()
    
    return source
    

# url = full_search_url(query, GOOGLE_SEARCH_URL, GOOGLE_SPACE_ENCODING)

# source = get_pinterest_source_html(URL)

# with open('test.html','w') as file:
#     file.write(source)
# image_urls = get_google_image_urls(source)
# save_image_urls(image_urls, "images/"+query)

query = "coffee"
url = full_search_url(query, PINTEREST_SEARCH_URL, PINTEREST_SPACE_ENCODING)
source = get_pinterest_source_html(url)

# with open('pinterest-test2.html','w') as file:
#     file.write(source)

image_urls = get_pinterest_image_urls_from_search(source)
save_image_urls(image_urls, "images/"+query)



# image_urls = get_pinterest_pin_urls(source, "BoardFeedResource")
# save_image_urls(image_urls, "images/coffee-paper-cups")
