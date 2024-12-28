from datetime import datetime

try:
    import regex as re
except ImportError:
    import re

VALID_PHONE = re.compile(r'[+()\s-]')
EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    re.IGNORECASE
)
VALID_USERNAME_RE = re.compile(
    r'^[a-z](?:(?!__)\w){1,30}[a-z\d]$',
    re.IGNORECASE
)

DATA_PATTERN = re.compile(r'^(0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/\d{4}$')


def parse_phone(phone: str|int) -> str|None:
    if isinstance(phone, int):
        return str(phone)
    else:
        phone = VALID_PHONE.sub('', str(phone))
        if phone.isdigit():
            return phone

def parse_nuns(text: str) -> str:
    return re.sub(r'[^0-9]', '', str(text))

def valid_username(username: str) -> bool:
    return bool(VALID_USERNAME_RE.match(username))

def valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.match(email))

def get_date(data_str: str) -> datetime|None:
    if date := DATA_PATTERN.search(data_str):
        try:
            data_datetime = datetime.strptime(date.group(), "%d/%m/%Y")
            return data_datetime
        except ValueError:
            return None

