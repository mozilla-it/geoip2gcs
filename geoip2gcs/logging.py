import logging
import logging.config

from .config import Settings

log_config = {
    "version": 1,
    "formatters": {
        "console": {
            "format": "[%(levelname)s] %(message)s",
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "loggers": {
        "geoip2gcs": {
            "handlers": [
                "console",
            ],
            "level": "INFO",
        }
    },
}

settings = Settings()

if settings.debug:
    log_config["loggers"]["geoip2gcs"]["level"] = "DEBUG"

logging.config.dictConfig(log_config)
