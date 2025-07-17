import cv2 
import numpy as np

import pytesseract
from .page import Page
from .text_opetations import text_confidence 

from enum import Enum
from typing import List



class Statement(object):
    TYPES = {
        "Справка": "Справка",
        "Реестр": "Реестр Начисления Пени",
        "Расчет": "Расчет суммы искового заявления о взыскании задолженности",
    }

    def __init__(self) -> None: 
        self.__pages: List[Page] = []

        self.__type: str = 'N/A'
        self.__type_confidence: int = 0

    def get_type(self) -> "Statement":
        self.__crop_title()

        title_data = [
            line for line in pytesseract.image_to_string(self.__title, lang='rus').split('\n') if line]

        for statement_type, statement_pattern in Statement.TYPES.items():
            if any((conf := text_confidence(statement_pattern, line)) > 0.6 for line in title_data):
                print(title_data)
                self.__type = statement_type 
                self.__type_confidence = int(conf * 100)
                break 
        # else: raise Exception

        return self

    def process(self) -> str: 
        self.get_type()

        cv2.imshow('Title Page', self.__pages[0].src)
        while cv2.waitKey(1) != ord('n'): pass
        
        # title_crop = cv2.dilate(title_crop, np.ones((5, 5), np.uint8))
        # dilated = cv2.dilate(page, cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1)), iterations=2)
        return ''


    def __crop_title(self) -> "Statement":
        H, W = self.__pages[0].bin.shape

        self.__title_rect: tuple[int, ...] = tuple(map(int, (
            0.01 * W, 0.02 * H,
            0.75 * W, 0.13 * H
        )))
        self.__title: np.ndarray = self.__pages[0].bin[
            self.__title_rect[1]:self.__title_rect[3], 
            self.__title_rect[0]:self.__title_rect[2],
        ]

        cv2.rectangle(self.__pages[0].src, 
                      (self.__title_rect[0], self.__title_rect[1]), 
                      (self.__title_rect[2], self.__title_rect[3]), 
                      (0, 255, 0), 5)

        return self


    def __get_title1(self, src: np.ndarray) -> tuple[np.ndarray, tuple[int, ...]]:
        H, W = src.shape 

        rect = tuple(map(int, (
            0.01 * W, 0.02 * H,
            0.75 * W, 0.13 * H
        )))
        title = src[rect[1]:rect[3], rect[0]:rect[2]]

        return title, rect 



    def add_page(self, page: Page) -> None: 
        self.__pages.append(page)

    def get_page(self, page_idx: int) -> Page: 
        return self.__pages[page_idx]
    
    def get_page_idx(self, page_idx: int) -> int: 
        return self.__pages[page_idx].idx

    @property 
    def type(self):
        return self.__type

    @property 
    def type_confidence(self):
        return self.__type_confidence

