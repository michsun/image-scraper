# import sys
# sys.path.append('Users/michellesun/Dropbox/dev')
import os
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup
import tqdm

SEARCH_URL = "https://www.google.com/search?tbm=isch&q="
SPACE_ENCODING = "+"
# TODO: Add encoding as UTF-8


def open_url(url):
    try:
        html = urlopen(url)
    except HTTPError as e:
        print('HTTPError!')
        print(e)
        return None
    except URLError as e:
        print('The server could not be found!')
        return None
    else:
        return html

def make_soup(url):
    return BeautifulSoup(open_url(url).read(), 'lxml')

def print_html(url):
    print(make_soup(url))

def save_image(url, filePath, fileName):
    fullFillePath = os.path.join(filePath, fileName)
    if not os.path.isfile(fullFillePath):
        image = open_url(url)
        Path(filePath).mkdir(parents=True, exist_ok=True)
        output = open(fullFillePath, "wb")
        try:
            output.write(image.read())
        except AttributeError as e:
            os.remove(fullFillePath)
            raise Exception('No image saved') from e
        finally:
            output.close()
    else:
        print(fullFillePath, "already exists.")

def run():
    # Download and save source code 
    QUERY = "cats"
    # search_url = SEARCH_URL + QUERY
    search_url = "https://nl.pinterest.com/dianavandevis/coffee-paper-cups/"
    print_html(search_url)

if __name__ == "__main__":
    run()