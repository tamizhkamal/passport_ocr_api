import os
import logging
import logging.config

LOG_DIR = 'logs'
LOG_FILE = 'app.log'

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Add custom SUCCESS log level (between INFO=20 and WARNING=30)
SUCCESS_LEVEL_NUM = 25
logging.addLevelName(SUCCESS_LEVEL_NUM, 'SUCCESS')

def success(self, message, *args, **kwargs):
    if self.isEnabledFor(SUCCESS_LEVEL_NUM):
        self._log(SUCCESS_LEVEL_NUM, message, args, **kwargs)

logging.Logger.success = success

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, LOG_FILE),
            'formatter': 'standard',
            'level': 'DEBUG',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'DEBUG',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'DEBUG',
    },
}


def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)
