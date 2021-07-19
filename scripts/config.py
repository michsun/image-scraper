import json

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
                "load_sleep": 1,
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


def test_open():
    with open("scripts/config.json", 'r', encoding='utf-8') as file:
        config = json.load(file)
        config = Config(config)
    attrs = vars(config)
    print(config.image)
    
    image_config = Config(config.image)
    webdriver_config = Config(config.webdriver)
    search_config = Config(config.search_config)
    
    print(image_config.save_path)
    print(webdriver_config.browser, webdriver_config.path)
    print(search_config.Google, search_config.Pinterest)

if __name__ == "__main__":
    reset_defaults()
    # test_open()