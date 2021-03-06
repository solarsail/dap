import logging
from sdap import config

conf_dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s [%(levelname)s] %(name)s | %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': logging.DEBUG,
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        'sdap': {
            'level': config.log_level(),
            'handlers': ['console']
        }
    }
}
