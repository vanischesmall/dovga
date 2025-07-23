import pytesseract

import cv2
import math
import numpy as np

from .regexs import get_float

from collections import defaultdict


NUMERIC_OCR_CONFIG = r'--oem 3 --psm 6 -c tessedit_char_whitelist=-,.0123456789'

def get_moment_c(moments) -> tuple[int, int]: 
    try: cx = moments['m10'] // moments['m00']
    except ZeroDivisionError: cx = 0

    try: cy = moments['m01'] // moments['m00']
    except ZeroDivisionError: cy = 0

    return cx, cy

def get_geom_c(x, y, w, h) -> tuple[int, int]: 
    return x + w // 2, y + h // 2

def is_cell(cont) -> bool:
    x, y, w, h = cv2.boundingRect(cont) 
    return h <= w

def polygon_from_lines(line_a, line_b):
    return np.array([
        tuple(line_a[line_a[:, :, 1].argmax()][0]),
        tuple(line_a[line_a[:, :, 1].argmin()][0]),
        tuple(line_b[line_b[:, :, 1].argmin()][0]),
        tuple(line_b[line_b[:, :, 1].argmax()][0]),
    ])


def get_statement_type(src: np.ndarray): 
    H, W = src.shape 
    img = cv2.cvtColor(src, cv2.COLOR_GRAY2BGR)

    title_rect = tuple(map(int, (
        0.25 * W, 0.02 * H, 
        0.75 * W, 0.13 * H, 
    )))

    title_crop = src[title_rect[1]:title_rect[3], title_rect[0]:title_rect[2]]
    title_crop = cv2.dilate(title_crop, np.ones((5, 5), np.uint8))
    # dilated = cv2.dilate(page, cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1)), iterations=2)

    cv2.rectangle(img, (title_rect[0], title_rect[1]), (title_rect[2], title_rect[3]), (0, 255, 0), 4)



    cv2.imshow('img', img)
    cv2.imshow('title', title_crop)

    return 'N/A'

def parse_table(pages: list[np.ndarray], pages_idxs: list[int]) -> defaultdict:
    curr_row = 0 
    curr_page = 0
    table_data = defaultdict(float)

    for page in pages: 
        table_conts = [
            cont 
            for cont in cv2.findContours(page, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0] 
            if cv2.contourArea(cont) > 1000
        ] 

        table_cont = max(table_conts, key=cv2.contourArea)
        table_bbox = cv2.boundingRect(table_cont)

        table_mask = np.zeros(page.shape, np.uint8)
        cv2.drawContours(table_mask, [table_cont], -1, (255, 255, 255), -1)
        table = cv2.bitwise_and(page, table_mask) \
        [table_bbox[1]:table_bbox[1] + table_bbox[3], table_bbox[0]:table_bbox[0]+table_bbox[2]]

        ver_lines_mask = cv2.morphologyEx(
            table, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 50)), iterations=2)
        hor_lines_mask = cv2.morphologyEx(
            table, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1)), iterations=2)

        table_struct = cv2.dilate(cv2.add(hor_lines_mask, ver_lines_mask), np.ones((7, 7), np.uint8))

        ver_lines = sorted([
            (cont, cv2.moments(cont)) 
            for cont in cv2.findContours(ver_lines_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
        ], key=lambda x: get_moment_c(x[1])[0])

        columns_mask = np.zeros_like(table)
        cv2.fillPoly(columns_mask, [polygon_from_lines(ver_lines[0][0],  ver_lines[1][0])],  (255, 255, 255))
        cv2.fillPoly(columns_mask, [polygon_from_lines(ver_lines[-2][0], ver_lines[-1][0])], (255, 255, 255))
        table_struct = cv2.bitwise_and(table_struct, columns_mask)

        cell_conts = sorted([
            (cont, cv2.moments(cont))
            for cont in cv2.findContours(255-table_struct, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
            if cv2.contourArea(cont) < math.prod(table_struct.shape) // 4 and is_cell(cont)
        ], key=lambda x: get_moment_c(x[1])[::-1])

        table: np.ndarray =  table - table_struct
        table_img = cv2.cvtColor(table, cv2.COLOR_GRAY2BGR)
        table_struct_img = cv2.cvtColor(table_struct, cv2.COLOR_GRAY2BGR)

        n = len(cell_conts) // 2
        for row in range(1, n):
            curr_row += 1

            l_bbox = cv2.boundingRect(cell_conts[2 * row + 1][0])
            r_bbox = cv2.boundingRect(cell_conts[2 * row + 0][0])

            if l_bbox[0] > r_bbox[0]:
                l_bbox, r_bbox = r_bbox, l_bbox

            cv2.rectangle(table_img, (l_bbox[0], l_bbox[1]), (l_bbox[0] + l_bbox[2], l_bbox[1] + l_bbox[3]), (0, 255, 0), 4)
            cv2.rectangle(table_img, (r_bbox[0], r_bbox[1]), (r_bbox[0] + r_bbox[2], r_bbox[1] + r_bbox[3]), (0, 255, 0), 4)

            l_crop = 255 - table[max(0, l_bbox[1] - int(0.1 * l_bbox[3])):l_bbox[1] + l_bbox[3], l_bbox[0]:l_bbox[0] + l_bbox[2]]
            r_crop = 255 - table[max(0, r_bbox[1] - int(0.1 * l_bbox[3])):r_bbox[1] + r_bbox[3], r_bbox[0]:r_bbox[0] + r_bbox[2]]

            date = pytesseract.image_to_string(l_crop, config=NUMERIC_OCR_CONFIG) or None
            fine = pytesseract.image_to_string(r_crop, config=NUMERIC_OCR_CONFIG) or None

            # # kostil
            # l_crop_p = cv2.dilate(l_crop, np.ones((3, 3), np.uint8))
            # r_crop_p = cv2.dilate(r_crop, np.ones((3, 3), np.uint8))
            #
            # cv2.erode(l_crop_p, np.ones((3, 3), np.uint8), l_crop_p)
            # cv2.erode(r_crop_p, np.ones((3, 3), np.uint8), r_crop_p)

            # date = pytesseract.image_to_string(l_crop_p, config=NUMERIC_OCR_CONFIG) or None
            # fine = pytesseract.image_to_string(r_crop_p, config=NUMERIC_OCR_CONFIG) or None
            #
            # if fine is not None and fine[0] in '46':
            #     _fine = pytesseract.image_to_string(r_crop, config=NUMERIC_OCR_CONFIG) or None
            #     if _fine is not None:
            #         if _fine[0] == '-' and fine[0] != '-':
            #             fine = '-' + fine

            if date is None or fine is None: 
                if row != n - 1:
                    print(f'Error while processing {curr_row} line on {pages_idxs[curr_page]} page. {date=}, {fine=}')
                continue

            date = get_float(date)
            fine = get_float(fine)

            if date is not None:
                table_data[str(f'{date:.4f}')] += fine or 0.0

        #     cv2.imshow('l', l_crop)
        #     cv2.imshow('r', r_crop)
        #     print(date, fine)
        #
        #     # while cv2.waitKey(1) != ord('n'): pass
        #
        # cv2.imshow('table', table_img)
        # cv2.imshow('table_struct', table_struct_img)
        # while cv2.waitKey(1) != ord('n'): pass
        # print('==============================================================')

        curr_page += 1

    return table_data
