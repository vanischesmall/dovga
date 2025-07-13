import re
import pytesseract

from pdf2image import convert_from_path

import io
import cv2
import imutils
import numpy as np

import utils
from random import randint


SEAL_HSV = (
    np.array([10, 30, 160]),
    np.array([180, 255, 255]),
)
SCAN_PATH = 'scans/input.pdf'


class DocumentParser:
    def __init__(self):
        self.__doc = [
            cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
            for page in convert_from_path(SCAN_PATH, dpi=300, grayscale=False)
        ]
        self.__doc_len = len(self.__doc)
        self.__doc_end = False
        self.__page_index = 4

        self.__clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))

        print(f'Pages scanned: {self.__doc_len}')

    def get_statement(self):
        statement = self.__doc[self.__page_index] 

        statement = self.__autorotate(statement)
        statement = self.__remove_seal(statement)
        statement = self.__preprocess_page(statement)

        table = utils.detect_table(statement)

        if table is not None:
            pass
            # cv2.imshow('table', table)

        # img = cv2.cvtColor(statement, cv2.COLOR_GRAY2BGR)
        # conts = cv2.findContours(statement, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
        #
        # table_cont = None
        # table_conts = [cont for cont in conts if cv2.contourArea(cont) > 1000] 
        # if len(table_conts): 
        #     table_cont = max(table_conts, key=cv2.contourArea)
        #     table_bbox = cv2.boundingRect(table_cont)
        #
        #
        #
        #     table_crop = statement[table_bbox[1]:table_bbox[1] + table_bbox[3], table_bbox[0]:table_bbox[0]+table_bbox[2]]
        #     table = utils.detect_table_with_hough(table_crop)
        #
        #     table_data = pytesseract.image_to_string(table, lang='rus')
        #     # print(table_data)
        #
        #     # table_data = pytesseract.image_to_data(table_crop, lang='rus', output_type=pytesseract.Output.DICT)
        #     # for i in range(len(table_data['text'])):
        #         # if table_data['conf'][i] < 6:
        #         #     continue
        #
        #         # x, y, w, h = table_data["left"][i], table_data["top"][i], table_data["width"][i], table_data["height"][i] 
        #         # rand_color = (randint(0, 255), randint(0, 255), randint(0, 255))
        #
        #         # cv2.rectangle(table, (x, y), (x+w, y+h), 0, -1)
        #         # cv2.rectangle(table, (x, y), (x+w, y+h), rand_color, 4)
        #
        #     cv2.rectangle(img, 
        #                   (table_bbox[0], table_bbox[1]),
        #                   (table_bbox[0] + table_bbox[2], table_bbox[1] + table_bbox[3]),
        #                   (0, 255, 0), 4)
        #
        #     cv2.imshow('table', table)


        # img = cv2.cvtColor(statement, cv2.COLOR_GRAY2BGR)
        # lines = cv2.HoughLinesP(statement,1,np.pi/180,100,minLineLength=50,maxLineGap=5)
        # for line in lines:
        #     x1,y1,x2,y2 = line[0]
        #     cv2.line(img,(x1,y1),(x2,y2),(0,255,0),2)

        self.__update_page()
        return self.__doc_end, statement
    
    def __detect_table(self, page):
        ret = utils.detect_table(page)

        return ret

    def __preprocess_page(self, page):
        return cv2.adaptiveThreshold(
            self.__clahe.apply(cv2.GaussianBlur(cv2.cvtColor(page, cv2.COLOR_BGR2GRAY), (9, 9), 0)), 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,
            15, 15,
        )

    def __remove_seal(self, page): 
        hsv_page = cv2.cvtColor(page, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv_page, *SEAL_HSV)


        return cv2.bitwise_not(
            cv2.cvtColor(255-mask, cv2.COLOR_GRAY2BGR), 
            page, mask=mask
        )

    def __autorotate(self, page): 
        osd = pytesseract.image_to_osd(page) 
        angle = re.search("(?<=Rotate: )\d+", osd)

        if angle is not None:
            page = imutils.rotate_bound(page, float(angle.group(0)))
        return page
    
    def __update_page(self): 
        print(self.__page_index)
        self.__page_index += 1
        if self.__page_index == self.__doc_len: 
            self.__doc_end = True 

    def __display_ocr(self, page): 
        h, w, _ = page.shape
        data = pytesseract.image_to_data(page, output_type=pytesseract.Output.DICT, lang='rus')

        for i in range(len(data['text'])):
            if data['conf'][i] > 60:
                x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i] 
                rand_color = (randint(0, 255), randint(0, 255), randint(0, 255))

                print(data['text'][i])
                cv2.rectangle(page, (x, y), (x+w, y+h), rand_color, 5)
                cv2.putText(page, str(data['text'][i]), (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 2, rand_color, 5, cv2.LINE_AA)

        return page


def main():
    doc_parser = DocumentParser()

    while True:
        end, statement = doc_parser.get_statement()

        if end:
            print('End')
            break

        cv2.imshow("statement", statement)
        while cv2.waitKey(1) != ord('l'): pass


if __name__ == "__main__":
    main()
