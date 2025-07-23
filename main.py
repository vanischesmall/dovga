import logging
from json import dumps

import cv2
import numpy as np
from pdf2image import convert_from_path

from lib.page import Page
from lib.statement import Statement

SCAN_PATH = 'assets/input2.pdf'


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

            # cv2.imshow('page', page.src)

            # cv2.imshow('Page src', page.src)
            # cv2.imshow('Page bin', page.bin)
            #
            # while cv2.waitKey(1) != ord('n'): pass

            if page.sealed: 
                break 

        statement.process() 

        print(dumps(statement.description, indent=4, ensure_ascii=False))
        print()


        cv2.imshow('Title Page', statement.title_page)
        while cv2.waitKey(1) != ord('n'): pass

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
