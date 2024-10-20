import os
import logging

def add_logging_level(name, num):
    """
    # This method was inspired by the answers to Stack Overflow post
    # https://stackoverflow.com/a/35804945

    Usage:
        add_logging_level('TRACE', logging.DEBUG - 5)
        logging.getLogger(__name__).setLevel("TRACE")
        logging.getLogger(__name__).trace('that worked')
        logging.trace('so did this')
        logging.TRACE
    """
    method = name.lower()

    def log_method(self, message, *args, **kwargs):
        if self.isEnabledFor(num):
            self._log(num, message, args, **kwargs) #yes, not '*args'
    def log_to_root(message, *args, **kwargs):
        logging.log(num, message, *args, **kwargs)

    if hasattr(logging, name): return # Already set
    logging.addLevelName(num, name)
    setattr(logging, name, num)
    setattr(logging.getLoggerClass(), method, log_method)
    setattr(logging, method, log_to_root)


def set_cid_logger(verbosity=2, log_filename=None):

    add_logging_level('TRACE', logging.DEBUG - 5)

    logger = logging.getLogger('cid')

    # File handler logs everything down to DEBUG level
    if log_filename and not os.environ.get('AWS_EXECUTION_ENV', '').startswith('AWS_Lambda'):
        fh = logging.FileHandler(log_filename)
        #fh.setLevel(logging.TRACE)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s:%(funcName)s:%(lineno)d - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    # Console handler logs everything down to WARNING level
    ch = logging.StreamHandler()
    #ch.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if verbosity:
        # Limit Logging level to DEBUG, base level is WARNING
        verbosity = min(verbosity, 3)
        level_map = {
            1: logging.ERROR,
            2: logging.WARNING,
            3: logging.INFO,
            4: logging.DEBUG,
            5: logging.TRACE,
        }
        logger.setLevel(level_map.get(2 + verbosity, logging.INFO))
        # Logging application start here due to logging configuration
        print(f'Logging level set to: {logging.getLevelName(logger.getEffectiveLevel())}')

    return logger
