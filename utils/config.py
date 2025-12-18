import json
import os

class ConfigManager:
    DEFAULT_CONFIG = {
        "api_key": "",
        "language": "ru",
        "model": "nova-3",
        "hotkey": "option+space",
        "exclusions": [
            "спасибо за просмотр",
            "подписывайтесь на канал",
            "субтитры сделал dimatorzok"
        ],
        "commands": {
            "новая строка": "\n",
            "новый список": "\n- ",
            "точка": ".",
            "запятая": ","
        }
    }

    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.settings = self.load()

    def load(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return {**self.DEFAULT_CONFIG, **json.load(f)}
        return self.DEFAULT_CONFIG.copy()

    def save(self):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4, ensure_ascii=False)

    def get(self, key):
        return self.settings.get(key)

    def set(self, key, value):
        self.settings[key] = value
        self.save()
