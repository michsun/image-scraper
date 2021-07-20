import unittest
import image_scraper.config as config

class TestConfig(unittest.TestCase):
    
    def test_update_dictionary(self):
        dictionary = {'a': 1, 'a2': 2, 'b': {'one':1, 'two':2, 'three':3 }, 'c': {'level1': {'level2': False}}}  
        new_values = {'a':10, 'b': {'two': 200}, 'c': {'level1': {'level2': True}}}
        expected = {'a': 10, 'a2': 2, 'b': {'one': 1, 'two': 200, 'three': 3 }, 'c': {'level1': {'level2': True }}}
        
        result = config.update_dictionary(prev=dictionary, new=new_values)
        self.assertEqual(result, expected)
        
        dictionary = {'a': 2, 'b': {'sub': True}}
        new_values = {'c':3 }
        self.assertRaises(KeyError, config.update_dictionary, dictionary, new_values)
        
if __name__ == "__main__":
    unittest.main()