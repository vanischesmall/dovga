import pytesseract

import cv2
import math
import numpy as np

from collections import defaultdict

Mat = np.ndarray
OCR_CONFIG = r'--oem 3 --psm 6 -c tessedit_char_whitelist=-.0123456789'

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

def extract_table_data(statement: list[Mat], pages_idxs: list[int]) -> defaultdict:
    curr_row = 0 
    curr_page = 0
    table_data = defaultdict(float)

    for page in statement: 
        table_conts = [
            cont 
            for cont in cv2.findContours(page, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0] 
            if cv2.contourArea(cont) > 1000
        ] 

        table_cont = max(table_conts, key=cv2.contourArea)
        table_bbox = cv2.boundingRect(table_cont)

        table_mask = np.zeros(page.shape, np.uint8)
        cv2.drawContours(table_mask, [table_cont], -1, 255, -1)
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
        cv2.fillPoly(columns_mask, [polygon_from_lines(ver_lines[0][0],  ver_lines[1][0])],  255)
        cv2.fillPoly(columns_mask, [polygon_from_lines(ver_lines[-2][0], ver_lines[-1][0])], 255)
        table_struct = cv2.bitwise_and(table_struct, columns_mask)

        cell_conts = sorted([
            (cont, cv2.moments(cont))
            for cont in cv2.findContours(255-table_struct, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
            if cv2.contourArea(cont) < math.prod(table_struct.shape) // 4 and is_cell(cont)
        ], key=lambda x: get_moment_c(x[1])[::-1])

        table -= table_struct
        table_img = cv2.cvtColor(table, cv2.COLOR_GRAY2BGR)
        table_struct_img = cv2.cvtColor(table_struct, cv2.COLOR_GRAY2BGR)

        for row in range(1, len(cell_conts) // 2):
            curr_row += 1

            l_bbox = cv2.boundingRect(cell_conts[2 * row + 1][0])
            r_bbox = cv2.boundingRect(cell_conts[2 * row + 0][0])

            cv2.rectangle(table_img, (l_bbox[0], l_bbox[1]), (l_bbox[0] + l_bbox[2], l_bbox[1] + l_bbox[3]), (0, 255, 0), 4)
            cv2.rectangle(table_img, (r_bbox[0], r_bbox[1]), (r_bbox[0] + r_bbox[2], r_bbox[1] + r_bbox[3]), (0, 255, 0), 4)

            l_crop = 255 - table[max(0, l_bbox[1] - int(0.1 * l_bbox[3])):l_bbox[1] + l_bbox[3], l_bbox[0]:l_bbox[0] + l_bbox[2]]
            r_crop = 255 - table[max(0, r_bbox[1] - int(0.1 * l_bbox[3])):r_bbox[1] + r_bbox[3], r_bbox[0]:r_bbox[0] + r_bbox[2]]

            date = pytesseract.image_to_string(l_crop, config=OCR_CONFIG) or 'NULL'
            fine = pytesseract.image_to_string(r_crop, config=OCR_CONFIG) or 'NULL'

            if date == 'NULL' or fine == 'NULL': 
                print(f'Ошибка при обработке {curr_row} строки на странице {pages_idxs[curr_page]}')
                continue

            table_data[date.strip()] += float(fine.strip())
        curr_page += 1
            # cv2.imshow('l', l_crop)
            # cv2.imshow('r', r_crop)
            #
            # print(date, fine)

        # cv2.imshow('table', table_img)
        # cv2.imshow('table_struct', table_struct_img)
        # while cv2.waitKey(1) != ord('n'): pass

    return table_data
