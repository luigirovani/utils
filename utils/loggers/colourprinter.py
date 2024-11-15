from typing import Dict, Union
from .consts import COLOURS, LOG_COLOURS  

class ColourPrinter:
    def __init__(self, colours:Dict[int, str]=COLOURS, log_colours:Dict[int, str]=LOG_COLOURS):
        self.colours = colours
        self.log_levels = log_colours

    def get_colour(self, level:int=None, colour:str=None):
        if colour:
            return self.colours.get(colour.upper(), '')
        elif level:
            return self.log_levels.get(level, '')
        else:
            return ''

    def print_stdout(self, msg:str, level:Union[int, str]=None, colour:str=None) -> None:
        print(self.get_colour(level, colour) + msg + self.colours['RESET'])

    def __call__(self, msg:str, level:Union[int, str]=None, colour:str=None) -> None:
        self.print_stdout(msg, level, colour)

colourprinter = ColourPrinter()

