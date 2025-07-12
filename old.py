import pytesseract

import cv2
import numpy as np
from skimage import filters

from pdf2image import convert_from_path
from typing import List, Optional
import imutils


SEAL_HSV = (
    np.array([70, 50, 220]),
    np.array([120, 170, 255]),
)
SCAN_PATH = 'scans/input.pdf'


class DocumentParser:
    def __init__(self):
        self.__doc = [
            np.array(page)
            for page in convert_from_path(SCAN_PATH, dpi=300, grayscale=False)
        ]
        self.__doc_len = len(self.__doc)
        self.__doc_end = False
        self.__page_index = 0

        self.__clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))

        print(f'Pages scanned: {self.__doc_len}')

    def get_statement(self) -> tuple[bool, np.ndarray]:
        statement_pages = []

        while True: 
            page = self.__doc[self.__page_index]
            seal, processed = self.__preprocess_page(page)

            statement_pages.append(processed)

            self.__page_index += 1
            if self.__page_index == self.__doc_len: 
                self.__doc_end = True

            if seal or self.__doc_end:
                break

        statement = np.vstack(statement_pages)

        return self.__doc_end, statement

    def __find_seal(self, page):
        found_seal = False
        kernel = np.ones((7, 7), np.uint8)

        mask = cv2.inRange(
            cv2.cvtColor(page, cv2.COLOR_RGB2HSV),
            *SEAL_HSV,
        )

        mask = cv2.erode(
            cv2.dilate(mask, kernel, iterations=1),
            kernel, iterations=1
        )

        seal_cont = max(cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0], key=cv2.contourArea)
        if cv2.contourArea(seal_cont) > 500: 
            x, y, w, h = cv2.boundingRect(seal_cont)
            if abs(w - h) < 100: 
                found_seal = True
                # cv2.rectangle(mask, (x, y), (x + w, y + h), (255), 5)

        return found_seal, mask

    def __preprocess_page(self, page) -> tuple[bool, np.ndarray]:
        _page = cv2.GaussianBlur(page, (5, 5), 0)
        seal_flag, seal_mask = self.__find_seal(_page)

        bin = cv2.adaptiveThreshold(
            self.__clahe.apply(cv2.cvtColor(_page, cv2.COLOR_RGB2GRAY)),
            255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 13, 13
        )
        bin = cv2.bitwise_not(seal_mask, bin, mask=seal_mask)

        return seal_flag, bin

def main():
    doc_parser = DocumentParser()

    while True:
        end, statement = doc_parser.get_statement()

        if end:
            print('not ret')
            break

        print(pytesseract.image_to_string(statement, lang='rus'))

        cv2.imshow("statement", statement)
        while cv2.waitKey(1) != ord('l'): pass

        

if __name__ == "__main__":
    main()
