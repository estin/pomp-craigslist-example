import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s %(levelname)s %(processName)s %(name)s %(message)s'  # noqa
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
        'django_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'default',
        },
        'dbimport_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'dbimport.log'),
            'formatter': 'default',
        },
        'crawler_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'crawler.log'),
            'formatter': 'default',
        },
        'exception_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'exceptions.log'),
            'formatter': 'default',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'django_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'dataview.dbimport': {
            'handlers': ['console', 'dbimport_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'pomp': {
            'handlers': ['console', 'crawler_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'craigslist': {
            'handlers': ['console', 'crawler_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'exceptions': {
            'handlers': ['console', 'exception_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
