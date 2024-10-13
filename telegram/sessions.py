from pathlib import Path
from typing import Union, List

def get_sessions(path:Union[str, Path] ='sessions') -> List[str]:
    return [
        str(session) 
        for session in Path(path).glob('*.session')
    ]




