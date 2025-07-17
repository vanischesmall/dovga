import logging

from typing import List

import re
import pytesseract

import cv2
import imutils
import numpy as np
from pdf2image import convert_from_path


import utils
from random import randint

from lib.page import Page
from lib.statement import Statement


SCAN_PATH = 'scans/input.pdf'


class DocumentParser:
    def __init__(self):
        self.__collect_document(SCAN_PATH)

        self.__doc_len = len(self.__doc_src)
        self.__doc_end = False
        self.__page_idx = 0

        logging.info(f'Pages scanned: {self.__doc_len}')

    def collect_statement(self):
        statement = Statement()

        while True: 
            page = Page(*self.__get_page()).process()
            statement.add_page(page)

            # cv2.imshow('Page src', page.src)
            # cv2.imshow('Page bin', page.bin)
            #
            # while cv2.waitKey(1) != ord('n'): pass

            if page.sealed: 
                break 

        statement.process() 
        logging.info(f'{statement.type} ({statement.type_confidence=}%)')

        print()

        return None

    def __get_page(self) -> tuple[int, np.ndarray]: 
        page = self.__doc_src[self.__page_idx]

        self.__page_idx += 1
        if self.__page_idx == self.__doc_len: 
            self.__doc_end = True 

        return self.__page_idx, page

    def __collect_document(self, path: str) -> None: 
        self.__doc_src = [
            cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
            for page in convert_from_path(path, dpi=300, grayscale=False)
        ]
        

    # def get_statement(self) -> Mat: 
    #     page = self.__get_page()
    #     _, page = self.__remove_seal(page)
    #
    #     page = self.__autorotate(page)
    #     page = self.__preprocess(page) 
    #
    #     statement_type = utils.get_statement_type(page)
    #     print(statement_type)
    #
    #     return page

    # def get_statement_1(self) -> Mat:
    #     pages = [] 
    #
    #     start_page_idx = self.__page_index
    #     while True: 
    #         page = self.__doc_src[self.__page_index] 
    #         seal, page = self.__remove_seal(page)
    #
    #         page = self.__autorotate(page)
    #         page = self.__preprocess(page) 
    #
    #         pages.append(page)
    #         # self.__update_page()
    #         #FIX get_page 
    #
    #         if seal or self.__doc_end: 
    #             break
    #
    #     statement = np.vstack(pages)
    #     table_data = utils.extract_table_data(pages, pages_idxs=[idx + 1 for idx in range(start_page_idx, self.__page_index)])
    #
    #     for date, fine in table_data.items(): 
    #         print(f'{date}: {fine}')
    #
    #     cv2.imshow('statement', statement)
    #     while cv2.waitKey(1) != ord('n'): pass
    #
    #     return statement


    # def __preprocess(self, page) -> Mat:
    #     return cv2.adaptiveThreshold(
    #         self.__clahe.apply(cv2.GaussianBlur(cv2.cvtColor(page, cv2.COLOR_BGR2GRAY), (9, 9), 0)), 255, 
    #         cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,
    #         15, 15,
    #     )
    #
    # def __remove_seal(self, page) -> tuple[bool, Mat]: 
    #     mask = cv2.inRange(cv2.cvtColor(page, cv2.COLOR_BGR2HSV), *SEAL_HSV)
    #
    #     seal = any(
    #         cv2.contourArea(cont) > 1000 
    #         for cont in cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0])
    #     page = cv2.bitwise_not(
    #         cv2.cvtColor(255-mask, cv2.COLOR_GRAY2BGR), 
    #         page, mask=mask)
    #
    #     return seal, page
    #
    # def __autorotate(self, page) -> Mat: 
    #     osd = pytesseract.image_to_osd(page) 
    #     angle = re.search("(?<=Rotate: )\d+", osd)
    #
    #     if angle is not None:
    #         page = imutils.rotate_bound(page, float(angle.group(0)))
    #     return page
    #
    # def __display_ocr(self, page): 
    #     h, w, _ = page.shape
    #     data = pytesseract.image_to_data(page, output_type=pytesseract.Output.DICT, lang='rus')
    #
    #     for i in range(len(data['text'])):
    #         if data['conf'][i] > 60:
    #             x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i] 
    #             rand_color = (randint(0, 255), randint(0, 255), randint(0, 255))
    #
    #             print(data['text'][i])
    #             cv2.rectangle(page, (x, y), (x+w, y+h), rand_color, 5)
    #             cv2.putText(page, str(data['text'][i]), (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 2, rand_color, 5, cv2.LINE_AA)
    #
    #     return page

    @property
    def end(self):
        return self.__doc_end

def main():
    # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

    doc_parser = DocumentParser()
    while True:
        doc_parser.collect_statement()

        if doc_parser.end:
            print('End')
            break

        # while cv2.waitKey(1) != ord('n'): pass


if __name__ == "__main__":
    main()
