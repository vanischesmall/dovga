import logging
from json import dumps
from pdf2image import convert_from_path

import cv2
import numpy as np

from lib.document_parser import DocumentParser

SCAN_PATH = 'assets/input.pdf'



def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

    doc_parser = DocumentParser(path=SCAN_PATH)
    while True:
        doc_parser.collect_statement()

        if doc_parser.end:
            print('End')
            break

        # while cv2.waitKey(1) != ord('n'): pass


if __name__ == "__main__":
    main()
