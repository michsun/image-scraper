import codecs

source = codecs.open('pinterest-search.html','r').read()
get_pinterest_image_urls_from_search(source)