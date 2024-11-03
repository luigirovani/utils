import colorlog
import logging

FT_COLOUR_PATERN= '%(log_color)s%(levelname)s %(reset)s - %(light_black)s %(asctime)s%(reset)s - %(message)s'

def get_logger(file_name='log.log', level_stdout=logging.INFO, level_file=logging.DEBUG, fmt=FT_COLOUR_PATERN) -> logging.Logger:

    logger = logging.Logger('root', level=logging.INFO)

    stdout_handler = colorlog.StreamHandler()
    stdout_handler.setLevel(level_stdout)  
    stdout_formater = colorlog.ColoredFormatter(fmt)
    stdout_handler.setFormatter(stdout_formater)
    logger.addHandler(stdout_handler)

    file_handler = logging.FileHandler(file_name, encoding='utf-8', mode='a')
    file_handler.setLevel(level_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)

    return logger
