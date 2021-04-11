# Image Scraper



## How to install

To install the package using github, first clone the repository. 
```
git clone https://github.com/michsun/image-scraper
```

Then run the setup.py file from the project directory.

```
sudo python setup.py install
```
Alternatively, you can use pip to install the package.
```
pip install git+https://github.com/michsun/image-scraper.git#egg=imagescraper
```

## How to use in terminal

The package can be imported and used in a regular python script. 

To run the package in a terminal, make sure you are in directory of the cloned repository before running the following commands. 

To run a simple keyword search on google, you can run the following command.
```
python image_scraper -gs <query>
```

To search pinterest
```
python image_scraper -ps <query>
```
Will also work for both search engines
```
python image_scraper -gps <query>
```
For a search query that is more than one word, be sure to enclose the search term in quotations. 
```
python image_scraper -gs "three word search"
```
For pinterest, there is also a custom pinterest board scraper. 
```
python image_scraper -pb <pinterest_board_url>
```

## Disclaimer

[TODO]