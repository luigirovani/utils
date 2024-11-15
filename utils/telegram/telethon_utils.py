import re
from typing import Union, Optional
from types import GeneratorType

USERNAME_RE = re.compile(
    r'@|(?:https?://)?(?:www\.)?(?:telegram\.(?:me|dog)|t\.me)/(@|\+|joinchat/)?'
)
TG_JOIN_RE = re.compile(
    r'tg://(join)\?invite='
)

VALID_USERNAME_RE = re.compile(
    r'^[a-z](?:(?!__)\w){1,30}[a-z\d]$',
    re.IGNORECASE
)

VALID_PHONE = re.compile(r'[+()\s-]')

def parse_phone(phone: Union[str, int]) -> Optional[str]:
    if isinstance(phone, int):
        return str(phone)
    else:
        phone = VALID_PHONE.sub('', str(phone))
        if phone.isdigit():
            return phone

def clean_phone(phone: Union[str, int]):
    """
    Removes characters that match the VALID_PHONE pattern and 
    returns only the characters that don't match.

    Args:
        text (str): The string to process.

    Returns:
        str: The filtered string.
    """
    if isinstance(phone, int):
        return str(phone)

    if phone.isdigit():
        return phone

    return ''.join(char for char in phone if not VALID_PHONE.match(char))

def is_list_like(obj):
    """
    Returns `True` if the given object looks like a list.

    Checking ``if hasattr(obj, '__iter__')`` and ignoring ``str/bytes`` is not
    enough. Things like ``open()`` are also iterable (and probably many
    other things), so just support the commonly known list-like objects.
    """
    return isinstance(obj, (list, tuple, set, dict, GeneratorType))



def parse_username(username):
    """
    Parses the given username or channel access hash, given
    a string, username or URL. Returns a tuple consisting of
    both the stripped, lowercase username and whether it is
    a joinchat/ hash (in which case is not lowercase'd).

    Returns ``(None, False)`` if the ``username`` or link is not valid.
    """
    username = username.strip()
    m = USERNAME_RE.match(username) or TG_JOIN_RE.match(username)
    if m:
        username = username[m.end():]
        is_invite = bool(m.group(1))
        if is_invite:
            return username, True
        else:
            username = username.rstrip('/')

    if VALID_USERNAME_RE.match(username):
        return username.lower(), False
    else:
        return None, False




