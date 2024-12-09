from os import path
from functools import cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from logging.handlers import QueueHandler, QueueListener
import logging.config
import queue


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='./app/.env', env_file_encoding='utf-8')
    db_user: SecretStr
    db_pw: SecretStr
    host: SecretStr
    port: int
    service_name: SecretStr
    basic_user : SecretStr
    basic_pw : SecretStr



@cache
def get_settings():
    """
    Reading a file from disk is normally a costly (slow) operation
    so we  want to do it only once and then re-use the same settings object, instead of reading it for each request.
    And this is exactly why we need to use python in built wrapper functions - cache for caching the carrier credential
    """
    return Settings()

def log_queue_listener() -> QueueListener:
    log_file_path = path.join(path.dirname(path.abspath(__file__)), 'logging.ini')
    logging.config.fileConfig(log_file_path, disable_existing_loggers=False)
    log_que = queue.Queue(-1)
    queue_handler = QueueHandler(log_que)
    listener = QueueListener(log_que, *logging.getLogger().handlers, respect_handler_level=True)
    logger = logging.getLogger(__name__)
    logger.addHandler(queue_handler)
    return listener
