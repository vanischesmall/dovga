import re
import cv2 
import numpy as np 

from typing import Union
from cv2.typing import Rect

from .regexs import Patterns



def get_float_like_str(string: str) -> Union[str, None]:
    string = string.replace(',', '.')
    while '..' in string: 
        string = string.replace('..', '.')

    res = re.findall(Patterns.FLOAT, string)
    return res[0] if res else None


def rect_geom_s(x, y, w, h) -> int: 
    return int(w * h)
    
def rect_geom_c(x, y, w, h) -> tuple[int, int]:
    return int(x + w // 2), int(y + h // 2)

def cont_ctr(cont) -> tuple[int, int]: 
    moments = cv2.moments(cont)
    try: cx = moments['m10'] // moments['m00']
    except ZeroDivisionError: cx = 0

    try: cy = moments['m01'] // moments['m00']
    except ZeroDivisionError: cy = 0

    return int(cx), int(cy)



