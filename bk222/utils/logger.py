import logging

class Logger:
    # logger = logging.getLogger('Loggeraada')

    def __init__(self, name):
        # file_logger = logging.FileHandler('runtime.log', mode='w')
        # format = '[%(asctime)s] [%(levelname)s] %(message)s'
        # file_logger_format = logging.Formatter(format)
        # file_logger.setFormatter(file_logger_format)
        # Logger.logger.addHandler(file_logger)
        # Logger.logger.setLevel(logging.DEBUG)
        self.logger = logging.getLogger(name)
        console = logging.StreamHandler()
        format = logging.Formatter('[%(levelname)s] [%(name)s] %(message)s')
        console.setFormatter(format)
        self.logger.addHandler(console)
        self.logger.setLevel(logging.DEBUG)

    def info(self, m):
        self.logger.info(m)

    def warn(self, w):
        self.logger.warning(w)

    def error(self, e):
        self.logger.error(e)