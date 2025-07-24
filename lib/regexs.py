import re 
from typing import Union


class Patterns:
    CA      = re.compile(r'\d{2}-\d{4}-\d{3}-\d')
    YEAR    = re.compile(r'\d{4}')
    FLOAT   = re.compile(r'\-?\d+\.+\d+')


def get_float(string: str) -> Union[float, None]:
    string = string.replace(',', '.')
    while '..' in string: string = string.replace('..', '.')

    try:
        return float(re.findall(Patterns.FLOAT, string)[0])
    except ValueError: 
        return None
