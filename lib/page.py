import cv2 
import imutils
import numpy as np 

import re 
import pytesseract



class Page(object): 
    SEAL_HSV = (
        np.array([10, 30, 160]),
        np.array([180, 255, 255])
    )

    def __init__(self, idx: int, src: np.ndarray) -> None: 
        self.__idx = idx
        self.__src = src 

        self.__clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(10, 10))
        self.__sealed = False

    def process(self) -> "Page":
        return self.autorotate().check_seal().preprocess()

    def check_seal(self) -> "Page":
        mask = cv2.inRange(cv2.cvtColor(self.__src, cv2.COLOR_BGR2HSV), *Page.SEAL_HSV)

        self.__sealed: bool = any(
            cv2.contourArea(cont) > 1000 
            for cont in cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
        )

        cv2.bitwise_not(cv2.cvtColor(255 - mask, cv2.COLOR_GRAY2BGR), self.__src, mask)
        cv2.fastNlMeansDenoisingColored(self.__src, self.__src, 10, 10, 7, 15)

        if self.__sealed:
            # print(f'Page {self.__idx} sealed!')
            pass

        return self

    def preprocess(self) -> "Page":
        self.__gray = self.__clahe.apply(cv2.cvtColor(self.__src, cv2.COLOR_BGR2GRAY))

        self.__bin = cv2.adaptiveThreshold(
            self.__gray, 255, 
            cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV,
            21, 21,
        )
        self.dst = cv2.cvtColor(self.__bin, cv2.COLOR_GRAY2BGR)

        return self

    def autorotate(self) -> "Page": 
        raw_angle = re.search(
            "(?<=Rotate: )\d+", 
            pytesseract.image_to_osd(self.__src),
        )

        if raw_angle is not None:
            angle = float(raw_angle.group(0))
            self.__src = imutils.rotate_bound(self.__src, angle)

        return self

    @property
    def idx(self) -> int: 
        return self.__idx

    @property
    def src(self) -> np.ndarray:
        return self.__src

    # @property
    # def dst(self) -> np.ndarray:
    #     return self.__dst

    @property 
    def bin(self) -> np.ndarray: 
        return self.__bin

    @property 
    def sealed(self) -> bool: 
        return self.__sealed

