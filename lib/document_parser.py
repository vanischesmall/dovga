import cv2 
import numpy as np

import logging 
from json import dumps
from typing import Union
from pdf2image import convert_from_path

from .page import Page
from .statement import Statement

class DocumentParser:
    def __init__(self, path: Union[str, None] = None):
        self.__path = path
        self.__collect_document(path)

        self.__doc_len = len(self.__doc_src)
        self.__doc_end = False
        self.__page_idx = 27

        logging.info(f'Pages scanned: {self.__doc_len}')

    def collect_statement(self):
        statement = Statement()

        while True: 
            page = Page(*self.__get_page()).process()
            statement.add_page(page)

            if page.sealed: 
                break 

        statement.process() 

        print(dumps(statement.description, indent=4, ensure_ascii=False))
        print()


        for page in statement.pages: 
            cv2.imshow(f'Page {page.idx}', page.dst)
        while cv2.waitKey(1) != ord('n'): pass
        cv2.destroyAllWindows()

        return None

    def __get_page(self) -> tuple[int, np.ndarray]: 
        page = self.__doc_src[self.__page_idx]

        self.__page_idx += 1
        if self.__page_idx == self.__doc_len: 
            self.__doc_end = True 

        return self.__page_idx, page

    def __collect_document(self, path: Union[str, None]) -> None: 
        if path is None:
            logging.error('path is none')
            return path

        self.__doc_src = [
            cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
            for page in convert_from_path(path, dpi=300, grayscale=False)
        ]
        
    @property
    def end(self):
        return self.__doc_end
