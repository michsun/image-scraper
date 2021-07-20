import json

from typing import Dict

class Config:
    
    def __init__(self, dictionary):
        for k, v in dictionary.items():
            setattr(self, k, v)
        
def reset_defaults():
    default_config = {
        "image": {
            "save_path": "images/",
            "create_subfolder": True
        },
        "webdriver": {
            "browser": "Chrome",
            "path": "drivers/chromedriver",
        },
        "search": {
            "Google": {
                "scroll_limit": 200000,
                "undetect_limit": 10,
                "load_sleep": 2,
                "iterate_sleep": 0.2,
                "webdriverwait_sleep": 2
            },
            "Pinterest": {
                "scroll_limit": 200000,
                "undetect_limit": 10,
                "load_sleep": 3,
                "iterate_sleep": 0.2,
                "webdriverwait_sleep": 2
            }
        }
    }
    json_config = json.loads(json.dumps(default_config))
    with open("scripts/config.json", 'w', encoding='utf-8') as file:
        json.dump(json_config, file, sort_keys=True, ensure_ascii=False, indent=4)


def update_json(new : Dict):
    with open("scripts/config.json", 'r', encoding='utf-8') as file:
        prev = json.load(file)
   
def update_dictionary(prev: Dict, new: Dict):
    prev_updated = prev
    for k,v in new.items():
        if type(prev[k]) == dict and type(v) == dict:
            print("Ran!")
            prev_updated[k] = update_dictionary(prev=prev[k], new=v)
        else:
            prev_updated[k] = v
    return prev_updated

if __name__ == "__main__":
    # update_value()
    pass