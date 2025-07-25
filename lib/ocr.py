import pytesseract 
import numpy as np

# pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
# pytesseract.pytesseract.tessdata_dir_config = '--tessdata-dir "/opt/homebrew/opt/tesseract/share/tessdata/"'



class Config: 
    NUMERIC = r'--oem 3 --psm 6 -c tessedit_char_whitelist=-.0123456789' 


def data(src: np.ndarray, config: str = '') -> dict: 
    return pytesseract.image_to_data(src, lang='remake', output_type=pytesseract.Output.DICT, config=config)


def string(src: np.ndarray, config: str = '') -> str:
    return pytesseract.image_to_string(src, lang='remake', config=config)
