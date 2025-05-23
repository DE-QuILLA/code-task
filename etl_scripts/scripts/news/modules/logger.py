import logging


class LoggingMixin:
    def __init__(self, log_config=None):
        self._log_config = log_config

    @property
    def logger(self):
        logger = logging.getLogger(self.__class__.__name__)
        if not logger.hasHandlers():
            handler = self._log_config.get("handler", logging.StreamHandler())
            formatter = self._log_config.get(
                "format",
                logging.Formatter(
                    fmt="[%(asctime)s] - [%(levelname)s] from [%(name)s]: %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                ),
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(self._log_config.get("level", logging.DEBUG))
        return logger
