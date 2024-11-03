from pathlib import Path
from typing import Union, List
import sqlite3

from.telethon_utils import parse_phone

def is_sqlite_in_use(db_path: str):
    try:
        conn = sqlite3.connect(f'file:{db_path}?mode=exclusive', uri=True)
        conn.close()
        return False 
    except sqlite3.OperationalError:
        return True  

def get_sessions(
    path:Union[str, Path] ='sessions',
    parse_phone: bool = True,
    only_phones: bool = True
) -> List[str]:

    return [
        str(session) 
        for session in Path(path).glob('*.session')
    ]


