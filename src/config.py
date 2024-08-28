import logging
import os
from pathlib import Path

import toml

ROOT_PATH: Path = Path(__file__ + '/../..').resolve()


class BaseConfig:

    @classmethod
    def update_from_toml(cls, path: str, section: str = None):
        try:
            config = toml.load(path)
            items = config.get(section, {}) if section else config
            for key, value in items.items():
                if hasattr(cls, key.upper()):
                    setattr(cls, key.upper(), value)
        except Exception as err:
            logging.error(f'Error occurred while loading config file: {err}')


class Config(BaseConfig):
    DATABASES_DIR: Path = ROOT_PATH / 'database'  # 数据库路径
    HOST: str = "127.0.0.1"
    PORT: int = 12006
    PRODUCTION: bool = False
    CLIENT_ID: str = ""
    CLIENT_SECRET: str = ""
    BOT_TOKEN: str = ""
    REDIRECT_URI: str = ""
    LOG_LEVEL: int = 20


_toml_file_path = os.path.join(ROOT_PATH, 'config.toml')
if os.path.exists(_toml_file_path):
    Config.update_from_toml(_toml_file_path)
