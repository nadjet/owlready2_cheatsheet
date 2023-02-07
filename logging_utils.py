import sys
import logging


def init_logging(write_to_log_file=False, log_path="/", file_name=""):
    root_logger = logging.getLogger('')
    root_logger.setLevel(logging.INFO)
    sh = logging.StreamHandler(sys.stdout)
    log_formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s', datefmt='%a, %d %b %Y %H:%M:%S')
    sh.setFormatter(log_formatter)
    if write_to_log_file:
        file_handler = logging.FileHandler("{0}/{1}.log".format(log_path, file_name))
        file_handler.setFormatter(log_formatter)
        root_logger.addHandler(file_handler)
    else:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        root_logger.addHandler(console_handler)