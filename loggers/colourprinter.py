from typing import Dict, Union

COLOURS = {
    'RED': "\033[31m",          # Vermelho
    'YELLOW': "\033[33m",       # Amarelo
    'BLUE': "\033[34m",         # Azul
    'GREEN': "\033[32m",        # Verde
    'CYAN': "\033[36m",         # Ciano
    'BLACK': "\033[30m",        # Preto
    'WHITE': "\033[37m",        # Branco
    'PURPLE': "\033[38;5;129m", # Púrpura
    'GREY': "\033[38;5;240m",   # Cinza
    'MAGENTA': "\033[35m",      # Magenta
    'PINK': "\033[38;5;200m",   # Rosa
    'SANIC': "\033[38;2;255;13;104m", # SANIC COLOUR
    # PREFIX
    'R': "\033[31m",            # Vermelho
    'Y': "\033[33m",            # Amarelo
    'B': "\033[34m",            # Azul
    'G': "\033[32m",            # Verde
    'V': "\033[31m",            # Vermelho
    'C': "\033[36m",            # Ciano
    'M': "\033[35m",            # Magenta
    'P': "\033[38;5;129m", # Purpura
    'S': "\033[38;2;255;13;104m",  # SANIC COLOUR
    'LR': "\033[91m",           # Vermelho Claro
    'LY': "\033[93m",           # Amarelo Claro
    'LB': "\033[94m",           # Azul Claro
    'LG': "\033[92m",           # Verde Claro
    'LC': "\033[96m",           # Ciano Claro
    'LM': "\033[95m",           # Magenta Claro
    'LW': "\033[97m",           # Branco Claro
    'LP': "\033[38;5;177m",     # Purpura Claro
    'RESET': "\033[0m"          # Resetar cor
}

LOG_COLOURS = {
    60: COLOURS['S'],
    50: COLOURS['LR'],
    40: COLOURS['R'],
    30: COLOURS['Y'],
    20: COLOURS['G'],
    10: COLOURS['B'],            
    0:  COLOURS['C']            
}
        

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

