import sys
import os
import time
import argparse
from tqdm import tqdm
from bs4 import BeautifulSoup
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException

# Tested on ChromeDriver 89.0.4389.23
from webdriver import WebDriver
from utils import *
from constants import WEBDRIVER_PATH, PINTEREST_SEARCH_URL, PINTEREST_SPACE_ENCODING, GOOGLE_SEARCH_URL, GOOGLE_SPACE_ENCODING

#TODO: Implement threading for this function
def get_google_image_urls(source_html):
    bs = BeautifulSoup(source_html, 'lxml')
    sub_pages = bs.find_all('a', {'href':re.compile('/imgres*')})
    page_urls = [ pg.attrs['href'] for pg in sub_pages]

    google_url = "https://www.google.com"
    image_urls = list()

    wd= WebDriver(WEBDRIVER_PATH, "Chrome")
    driver = wd.get_driver()
    print("Grabbing image urls...")
    for url in tqdm(page_urls):
        driver.get(google_url+url)
        time.sleep(0.3)
        try: 
            image_urls.append(driver.find_element_by_id('imi').get_attribute('src'))
        except NoSuchElementException:
            pass
        except Exception as e:
            print(e)
    print("Image url gathering complete.")

    driver.close()

    return image_urls


def get_google_source_html(url):
    """ Downloads the source html for the google images url. 
    """
    wd= WebDriver(WEBDRIVER_PATH, "Chrome")
    wd.get(url, 0.5)

    driver = wd.get_driver()


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
        try: 
            image.click()
        except ElementNotInteractableException as e:
            # The last three elements of this class are class="islrh" thus not clickable
            pass
        time.sleep(0.3)
    print("Images link load complete")

    source = driver.page_source

    # TODO: Fix driver.close() -> raises InvalidSessionException in webdriver.py
    driver.close()

    return source


# Pinterest exclusive
def find_pinterest_resource_from_resourceResponses(resourceResponses, name):
    print(len(resourceResponses))
    for obj in resourceResponses:
        if obj["name"] == name:
            return obj


# Pinterest exclusive
def get_pinterest_resource_urls(source_html, resourceType):
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
    
    print(len(image_urls), "image urls found")
    
    return image_urls


# Pinterest exclusive
def get_pinterest_image_urls_from_search(source_html, class_search=None):
    bs = BeautifulSoup(source_html, 'lxml')
    section = bs
    if class_search is not None:
        section = bs.find('div', {'class': class_search})
    
    image_elements = section.find_all('img', {'src': re.compile("https://i.pinimg.com/236x/*")})
    urls = [ e.attrs['src'] for e in image_elements ]
    print(len(urls), " image urls found")
    image_urls = [ os.path.splitext(url)[0].replace('/236x/','/originals/').split('-')[0] + os.path.splitext(url)[1] for url in urls ]
    print(len(image_urls), " urls converted")
    return image_urls


# Pinterest initialise
def get_pinterest_source_html(url, scroll=True, expectation=None):
    wd= WebDriver(WEBDRIVER_PATH, "Chrome")
    wd.get(url, 0.5)
    driver = wd.get_driver()

    # Scroll to the end of the page
    if expectation is not None:
        scroll_to_element(driver, expectation)
    elif scroll: # !!!
        scroll_to_bottom(driver)
    
    source = driver.page_source
    
    return source


def download_google_images(query, savePath=None, saveSource=False):
    print("> Scraping google images...")
    url = full_search_url(query, GOOGLE_SEARCH_URL, GOOGLE_SPACE_ENCODING)
    source = get_google_source_html(url)

    if saveSource:
        with open('google-{}.html'.format(query),'w') as file:
            file.write(source)
    if savePath is None:
        savePath = "images/"+query
    image_urls = get_google_image_urls(source)
    save_image_urls(image_urls, savePath)


def download_pinterest_board_images(url, boardName=None, savePath=None, saveSource=False):
    print("> Scraping pinterest board images from {}...".format(url))
    from selenium.webdriver.common.by import By
    expectation = (By.XPATH, "//section[@data-test-id='secondaryBoardGrid']")
    source = get_pinterest_source_html(url, expectation=expectation)

    if boardName is None:
        bs = BeautifulSoup(source, 'lxml')
        boardName = bs.find('h1').text
        boardName = boardName.lower().replace(' ','-')
    if saveSource:
        if saveSource:
            with open('pinterest-board-{}.html'.format(boardName), 'w') as file:
                file.write(source)
    if savePath is None:
        savePath = "images/"+boardName
    image_urls = get_pinterest_image_urls_from_search(source, class_search="Collection")
    # image_urls = get_pinterest_resource_urls(source, "BoardFeedResource")
    save_image_urls(image_urls, savePath)


def download_pinterest_images(query, saveName=None, savePath=None, saveSource=False):
    print("> Scraping pinterest images...")
    url = full_search_url(query, PINTEREST_SEARCH_URL, PINTEREST_SPACE_ENCODING)
    source = get_pinterest_source_html(url)
    
    if saveSource:
        with open('pinterest-{}.html'.format(query), 'w') as file:
            file.write(source)
    if savePath is None:
        savePath = "images/"+query
    image_urls = get_pinterest_image_urls_from_search(source)
    save_image_urls(image_urls, savePath)
    

def parse():
    parser = argparse.ArgumentParser()

    parser.add_argument('-g','--google_search',help='search query on google', action='store_true',required=False)
    parser.add_argument('-p','--pinterest_search',help='search query on pinterest', action='store_true', required=False)
    parser.add_argument('-pb','--pinboard_search',help='scrape images from a pinterest board url',type=str,required=False)
    parser.add_argument('-s','--search',help='query to search for on search engine',type=str,required=False)

    return parser.parse_args()


def main():
    args = parse()

    tic = time.time()
    if args.pinboard_search:
        url = args.pinboard_search
        download_pinterest_board_images(url)
    if args.search:
        query = args.search
        if args.google_search:
            download_google_images(query, saveSource=True)
        if args.pinterest_search:
            download_pinterest_images(query)
    toc = time.time()
        
    print("Scraping complete in", str(toc-tic),"s")

if __name__ == "__main__":
    # url = "https://nl.pinterest.com/dianavandevis/coffee-paper-cups/"
    # run_board(url)
    main()

    


# image_urls = get_pinterest_image_urls_from_search(source)
# save_image_urls(image_urls, "images/"+query)



# image_urls = get_pinterest_pin_urls(source, "BoardFeedResource")
# save_image_urls(image_urls, "images/coffee-paper-cups")
