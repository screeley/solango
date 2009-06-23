#
# Copyright 2008 Optaros, Inc.
#

"""
This module provides unified logging via the logging module.
"""
import logging
import logging.config
from solango.settings import LOGGING_CONF

class LogManager:
    """
    A helper class which instantiates and configures the default Logger.
    """
    def __init__(self):
        """
        Instantiate the default logger.
        """
        if not logging.getLogger().handlers:
            logging.config.fileConfig(LOGGING_CONF)
        self.logger = logging.getLogger('solango')
    
log_manager = LogManager()
logger = log_manager.logger
