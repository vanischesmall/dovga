import re
import pytesseract

import cv2
import math
import numpy as np

from typing import Union
from cv2.typing import Rect

from .page import Page
from . import ocr
from . import utils
from .regexs import get_float, Patterns
from collections import defaultdict


OCR_CFG_NUMERIC = r'--oem 3 --psm 6 -c tessedit_char_whitelist=-,.0123456789'

def parse_table(pages: list[Page]) -> defaultdict:
    table_data = defaultdict(float) 

    for page_idx, page in enumerate(pages): 
        # cv2.GaussianBlur(page.bin, (5, 5), 0, page.bin)

        table_cont = max(
            [
                cont
                for cont in cv2.findContours(page.bin, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
                if cv2.contourArea(cont) > 2000
            ],
            key=lambda cont: utils.rect_geom_s(*cv2.boundingRect(cont))
        )
        table_bbox = cv2.boundingRect(table_cont)

        table_mask = 255 - np.zeros(page.bin.shape, np.uint8)
        cv2.fillPoly(table_mask, [table_cont], (0, 0, 0))

        x, y, w, h = table_bbox
        table = (page.bin ^ table_mask)[y:y + h, x:x + w]
        page.dst = cv2.rectangle(page.dst, (x, y), (x + w, y + h), (0, 255, 0), 5)

        hor_line_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
        hor_lines_mask = cv2.morphologyEx(
            table, cv2.MORPH_OPEN, hor_line_kernel, iterations=2)
        cv2.dilate(hor_lines_mask, np.ones((5, 5), np.uint8), hor_lines_mask)
        cv2.dilate(hor_lines_mask, hor_line_kernel, hor_lines_mask)

        ver_line_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 50))
        ver_lines_mask = cv2.morphologyEx(
            table, cv2.MORPH_OPEN, ver_line_kernel, iterations=2)
        cv2.dilate(ver_lines_mask, np.ones((5, 5), np.uint8), ver_lines_mask)
        cv2.dilate(ver_lines_mask, ver_line_kernel, ver_lines_mask)

        rows_conts = sorted(
            [
                cont 
                for cont in cv2.findContours(255 - hor_lines_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
                if cv2.contourArea(cont) > 1000 
            ],
            key=lambda cont: utils.cont_ctr(cont)[1],
        )

        cols_conts = sorted(
            [
                cont
                for cont in cv2.findContours(255 - ver_lines_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
                if cv2.contourArea(cont) > 1000
            ],
            key=lambda cont: utils.cont_ctr(cont)[0],
        )

        cols_mask = np.zeros(table.shape, np.uint8)
        cv2.fillPoly(cols_mask, [cols_conts[0 ]], (255, 255, 255))
        cv2.fillPoly(cols_mask, [cols_conts[-1]], (255, 255, 255))

        table &= cols_mask
        table -= (table_struct := cv2.add(ver_lines_mask, hor_lines_mask))

        # cv2.imshow('table', table)
        # cv2.imwrite(f'photos/reestr2{page_idx}.png', table)

        # while cv2.waitKey(1) != ord('n'): pass
        

        # cv2.imshow('cols mask', cols_mask)
        # cv2.imshow('table', table)
        # cv2.imshow('hor', hor_lines_mask)
        # cv2.imshow('table_struct', table_struct)
        fail_mask = page.dst.copy()[y:y + h, x:x + w]
        for row_idx, row_cont in enumerate(rows_conts[1:]): 
            if row_idx == len(rows_conts) - 2 and page_idx == len(pages) - 1: 
                continue
            
            x, y, w, h = cv2.boundingRect(row_cont)
            row = (table & cv2.fillPoly(np.zeros(table.shape, np.uint8), [row_cont], (255, 255, 255)))[y:y + h, x:x + w]

            hh = int(h * 1.00)
            ww = int(w * 0.05)

            row_bg = np.zeros((h + 2 * hh, w + 2 * ww), np.uint8)
            row_bg[hh:h + hh, ww:w + ww] = row
            row = row_bg

            # raw_data = pytesseract.image_to_string(row, config=OCR_CFG_NUMERIC)
            raw_data = ocr.string(row, config=ocr.Config.NUMERIC)
            data = re.findall(Patterns.FLOAT, raw_data.replace(',', '.'))

            date = None
            fine = 0.0
            try:
                date = data[0]
                fine = float(data[1])

                # print(date, fine, sep='\t')
            except:
                cv2.GaussianBlur(row, (5, 5), 0, row)

                raw_data = ocr.string(row, config=ocr.Config.NUMERIC)
                data = re.findall(Patterns.FLOAT, raw_data.replace(',', '.'))

                try:
                    date = data[0]
                    fine = float(data[1])

                    # print(date, fine, sep='\t')
                except:
                    cv2.imshow('Row', row)
                    cv2.waitKey(1)

                    print(f'Invalid OCR output on page {page_idx}: {raw_data}')
                    while True:
                        try:
                            data = input(
                                'Введите данные строки в формате <дата> <пени>. Если строка некорекктна, нажмите Enter: ')
                            if data:
                                # print(data)
                                data = re.findall(Patterns.FLOAT, data.replace(',', '.'))
                                # print(data)

                                date = data[0]
                                fine = float(data[1])
                                cv2.fillPoly(fail_mask, [row_cont], (0, 0, 255))
                            break
                        except:
                            print('Неправильный формат ввода. Повторите попытку')

            if date is not None:
                table_data[date] += fine

            # cv2.imshow('row', row)
            # while cv2.waitKey(1) != ord('n'): pass
            

        x, y, w, h = table_bbox 
        page.dst[y:y + h, x:x + w] = cv2.addWeighted(page.dst[y:y + h, x:x + w], 0.5, fail_mask, 0.5, 1.0)
        # while cv2.waitKey(1) != ord('n'): pass
        # cv2.destroyAllWindows()
    # for k, v in table_data.items():
    #     print(type(k), type(v))

    return table_data







