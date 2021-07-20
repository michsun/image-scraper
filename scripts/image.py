import concurrent.futures
import os
import re
import requests
import tqdm

from pathlib import Path
from typing import Dict, List

from config import Config
from test_utils import timer

class ImagesDownloader(Config):
    
    # Image config params
    # self.save_path
    
    def __init__(self, config : Dict, image_urls : List[str] = None, image_names : List[str] = None, subfolder : str = None):
        super().__init__(config)
        if subfolder is not None:
            self.save_path = os.path.join(self.save_path, subfolder.replace(' ','_'))
        self.queue = image_urls
        self.image_names = image_names
    
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
    
    def download_image(self, image_url, file_name=None) -> None:
        """Requests and downloads the image."""
        # Requests and saves image
        try:
            r = requests.get(image_url, timeout=5)
            image_bytes = r.content
            Path(self.save_path).mkdir(parents=True, exist_ok=True)
            full_file_path = self.get_full_file_path(image_url, r)
            try: 
                with open(full_file_path, 'wb') as image_file:
                    image_file.write(image_bytes)
            except Exception as e:
                print(e)
        except requests.ConnectionError as e:
            print(f"> Error: Connection Error: at {image_url}")
            print(str(e))
        except requests.Timeout as e:
            print(f"> Error: Timeout: at {image_url}")
            print(str(e))
        except requests.RequestException as e:
            print(f"> Error: General Error: at {image_url}")
            print(str(e))

    def download_queue(self, image_urls) -> None:
        """Creates threads to execute the image download."""
        print("> Downloading images in queue...")
        if image_urls is None or len(image_urls) == 0:
            raise Exception("Error: [ImageDownloader] image_urls queue is empty. ")
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.download_image, url) for url in image_urls ]
        for future in concurrent.futures.as_completed(futures):
            print(future.result())
        print("> Executor complete")

        
def run():
    save_path = "images/test/"
    url = "https://i.pinimg.com/originals/bf/82/f6/bf82f6956a32819af48c2572243e8286.jpg"
    
    downloader = ImagesDownloader(save_path=save_path)
    downloader.download_image(image_url=url, file_name="test1.jpg")


if __name__ == "__main__":
    run()