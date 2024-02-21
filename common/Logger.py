import os
import sys
import logging
import logging.handlers as handlers


class Logger:
    LOG_FORMAT = "%(asctime)-15s %(name)s %(levelname)-8s %(message)s"

    def __init__(self, log_name: str = 'logs.txt'):
        logger_name = os.uname().nodename
        logger = logging.getLogger(logger_name)
        logging.basicConfig(filename=log_name, encoding='utf-8', level=logging.INFO, format=self.LOG_FORMAT)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(self.LOG_FORMAT))
        logger.addHandler(handler)
        # M - minutes, 24*60*15 - 15 days
        logger.addHandler(handlers.TimedRotatingFileHandler(log_name, when='M', interval=24*60*15, backupCount=1))
        self.log = logger
