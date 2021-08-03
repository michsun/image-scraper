import concurrent.futures
import os
import re
import requests
import sys

from http.client import responses
from pathlib import Path
from tqdm import tqdm
from typing import Dict, List
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from config import Config
from utils import timer

class ImagesDownloader(Config):
    
    # Image config params
    # self.save_path
    
    def __init__(self, config : Dict, image_urls : List[str] = None, image_name : str = None, subfolder : str = None):
        super().__init__(config)
        self.image_names = image_name
        self.queue = image_urls
        self.save_path = os.path.join(self.save_path, subfolder.replace(' ','_')) if subfolder is not None else None
    
    # TODO: Extensive testing
    def get_full_file_path(self, image_url : str, r : requests.models.Response) -> str:
        """Finds or creates an adequate image filename and returns the full file path for the image."""
        file_name = re.search("[^/\\&\?]+\.\w{3,4}(?=([\?&].*$|$))", image_url)
        if file_name is not None:
            file_name = file_name.group(0)
        else:
            image_type = r.headers['Content-Type'].split('/')[1]
            file_name = image_url.split('/')[-1].split('?')[0] + "." + image_type
        full_file_path = os.path.join(self.save_path, file_name)
        # Detects and handles duplicate image filenames
        while(os.path.isfile(full_file_path)):
            name, ext = os.path.splitext(os.path.basename(full_file_path))
            copyval = re.search(r"\((.*)\)", name)
            if copyval is None:
                file_name = name + "(1)" + ext
            else: 
                copyval = int(copyval.group(1))+1
                file_name = re.sub(r"\((.*)\)", r"(%d)" % copyval, name) + ext
            full_file_path = os.path.join(self.save_path, file_name)
        return full_file_path
    
    def download_image(self, image_url, timeout=10, file_name=None) -> int:
        """Requests and downloads the image."""
        try:
            r = requests.get(image_url, timeout=timeout, verify=False)
        except requests.exceptions.ReadTimeout:
            if timeout < 20:
                return self.download_image(image_url=image_url, timeout=20, file_name=file_name)
            else:
                return 418
        except Exception as e:
            print(f"Fatal exception at {image_url}.")
            err = sys.exc_info()[0]
            err_str = err.__name__
            print(e)
            print(err)
            print(err_str)
            sys.exit(1)
        
        try:
            r.raise_for_status()
            image_bytes = r.content
            Path(self.save_path).mkdir(parents=True, exist_ok=True)
            full_file_path = self.get_full_file_path(image_url, r)
            try: 
                with open(full_file_path, 'wb') as image_file:
                    image_file.write(image_bytes)
            except Exception as e:
                print(e)
        # TODO: Exception log during debug
        except requests.exceptions.HTTPError as e:
            # print(e)
            pass
        except requests.exceptions.ConnectionError as e:
            # print(e)
            pass
        except requests.exceptions.Timeout as e:
            # print(e)
            pass
        except requests.exceptions.RequestException as e:
            print(e)
            pass
        finally:
            return r.status_code


    def download_queue(self, image_urls) -> None:
        """Creates threads to execute the image download."""
        print("> Downloading images in queue...")
        if image_urls is None or len(image_urls) == 0:
            raise Exception("Error: [ImageDownloader] image_urls queue is empty. ")
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            status_codes = list(tqdm(executor.map(self.download_image, image_urls), total=len(image_urls)))
        # TODO: If logging then create a csv
        print("> Executor complete")
        unique = list(set(status_codes))
        results = { responses[code] : status_codes.count(code) for code in unique }
        
        # TODO: Tabulate function in utils
        min_width = 8
        width = max(max(map(len, [responses[code] for code in unique])), min_width)
        print(f"\n {'STATUS':>{width}} | {'TOTAL IMAGES':<{width}}")
        print(" {}+{}".format('='*(width+1),'='*(width+1)))
        for k,v in results.items():
            print(f" {k:>{width}} | {v:<{width}}")
        
        print(f"\n> Successfully downloaded {results['OK']} images.")

        
def run():
    save_path = "images/test/"
    url = "https://i.pinimg.com/originals/bf/82/f6/bf82f6956a32819af48c2572243e8286.jpg"
    
    downloader = ImagesDownloader(save_path=save_path)
    downloader.download_image(image_url=url, file_name="test1.jpg")

if __name__ == "__main__":
    run()