import re
VALID_PHONE = re.compile(r'[+()\s-]')

def get_display_name(entity) -> str:
    try:
        first_name = entity.first_name + ' ' if entity.first_name else ''
        last_name = entity.last_name or ''
        return first_name + last_name
    except:
        pass

    try:
        return entity.title
    except:
        pass

    return ''

def parse_phone(phone: str|int) -> str|None:
    if isinstance(phone, int):
        return str(phone)
    else:
        phone = VALID_PHONE.sub('', str(phone))
        if phone.isdigit():
            return phone



