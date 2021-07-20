import unittest
from image_scraper.config import *

class TestConfig(unittest.TestCase):
    
    def test_update_dictionary(self):
        dictionary = {'a': 1, 'a2': 2, 'b': {'one':1, 'two':2, 'three':3 }, 'c': {'level1': {'level2': False}}}  
        new_values = {'a':10, 'b': {'two': 200}, 'c': {'level1': {'level2': True}}}
        expected = {'a': 10, 'a2': 2, 'b': {'one': 1, 'two': 200, 'three': 3 }, 'c': {'level1': {'level2': True }}}
        
        result = update_dictionary(prev=dictionary, new=new_values)
        self.assertEqual(result, expected)
        
        
if __name__ == "__main__":
    unittest.main()