import yaml
import logging

with open('/etc/sdap/config.yml', 'r') as ymlfile:
    CONF = yaml.load(ymlfile)

def shared_db_name():
    return CONF['db']['shared_db']

_levels = {
    "NOTSET": logging.NOTSET,
    "DEBUG":  logging.DEBUG,
    "INFO":  logging.INFO,
    "WARNING":  logging.WARNING,
    "ERROR":  logging.ERROR,
    "CRITICAL":  logging.CRITICAL,
}

def log_level():
    level_str = CONF['log']['level']
    return _levels[level_str]

def use_cache():
    return CONF['redis']['enabled']
