from .colour_dict import COLOURS

MSG = '%(log_color)s%(message)s%(reset)s'

NAME_MSG = f'{COLOURS["S"]}%(name)s %(reset)s: %(log_color)s%(message)s'
NAME_LEVEL_MSG = f'{COLOURS["S"]}%(name)s %(log_color)s%(levelname)s %(reset)s: %(message)s'
NAME_TIME_MSG = f'{COLOURS["S"]}%(name)s %(light_black)s%(asctime)s%(reset)s: %(message)s'
NAME_LEVEL_TIME_MSG = f'{COLOURS["S"]}%(name)s %(log_color)s%(levelname)s %(light_black)s%(asctime)s%(reset)s: %(message)s'

LEVEL_MSG = '%(log_color)s%(levelname)s %(reset)s: %(message)s'
LEVEL_TIME_MSG = '%(log_color)s%(levelname)s %(light_black)s%(asctime)s%(reset)s: %(message)s'
LEVEL_NAME_MSG = f'%(log_color)s%(levelname)s {COLOURS["S"]}%(name)s %(reset)s: %(message)s'

TIME_MSG = '%(light_black)s%(asctime)s%(reset)s: %(log_color)s%(message)s'
TIME_LEVEL_MSG = '%(light_black)s%(asctime)s %(reset)s%(log_color)s%(levelname)s %(reset)s: %(message)s'
TIME_NAME_MSG = f'%(light_black)s%(asctime)s {COLOURS["S"]}%(name)s %(reset)s: %(message)s'




