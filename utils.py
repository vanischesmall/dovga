import cv2
import math
import numpy as np
from collections import defaultdict



            # print(table_data)

            # table_data = pytesseract.image_to_data(table_crop, lang='rus', output_type=pytesseract.Output.DICT)
            # for i in range(len(table_data['text'])):
                # if table_data['conf'][i] < 6:
                #     continue

                # x, y, w, h = table_data["left"][i], table_data["top"][i], table_data["width"][i], table_data["height"][i] 
                # rand_color = (randint(0, 255), randint(0, 255), randint(0, 255))

                # cv2.rectangle(table, (x, y), (x+w, y+h), 0, -1)
                # cv2.rectangle(table, (x, y), (x+w, y+h), rand_color, 4)

def get_c(x, y, w, h): 
    return x + w // 2, y + h // 2


def detect_table(statement):
    img = cv2.cvtColor(statement, cv2.COLOR_GRAY2BGR)

    table_conts = [
        cont 
        for cont in cv2.findContours(statement, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0] 
        if cv2.contourArea(cont) > 1000
    ] 

    if not len(table_conts): 
        return None

    table_cont = max(table_conts, key=cv2.contourArea)
    table_bbox = cv2.boundingRect(table_cont)
    cv2.rectangle(img, 
                  (table_bbox[0], table_bbox[1]), 
                  (table_bbox[0] + table_bbox[2], table_bbox[1] + table_bbox[3]),
                  (0, 255, 0), 4)

    # Cropping only table 
    table_mask = np.zeros(statement.shape, np.uint8)
    cv2.drawContours(table_mask, [table_cont], -1, 255, -1)
    table = cv2.bitwise_and(statement, table_mask) \
        [table_bbox[1]:table_bbox[1] + table_bbox[3], table_bbox[0]:table_bbox[0]+table_bbox[2]]

    # Removing lines from table 
    ver_lines = cv2.morphologyEx(table, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40)), iterations=2)
    hor_lines = cv2.morphologyEx(table, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1)), iterations=2)
    table_struct = cv2.dilate(cv2.add(hor_lines, ver_lines), np.ones((9, 9), np.uint8))
    table -= table_struct

    table_conts = cv2.findContours(table_struct, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
    table_conts = [(cont, cv2.boundingRect(cont)) for cont in table_conts if cv2.contourArea(cont) < math.prod(table.shape) // 2]
    # table_conts = sorted(table_conts, key=lambda cont: (cont[1][1] + cont[1][3] // 2, cont[1][0] + cont[1][2] // 2))
    table_conts = sorted(table_conts, key=lambda cont: get_c(*cont[1])[::-1])

    table_img = cv2.cvtColor(table, cv2.COLOR_GRAY2BGR)
    table_struct_img = cv2.cvtColor(table_struct, cv2.COLOR_GRAY2BGR)

    row = 0
    table_rois = defaultdict(list)
    last_cell = get_c(*table_conts[0][1]) 
    for _, (x, y, w, h) in table_conts:
        cx, cy = x + w // 2, y + h // 2
        if abs(last_cell[0] - cx) > (3 * w) or abs(last_cell[1] - cy) > h // 2:
            row += 1
            print()

        last_cell = (cx, cy) 
        table_rois[row].append((x, y, w, h))
        print(cy, cx, row, len(table_rois[row]) - 1)
        cv2.circle(table_struct_img, (cx, y + h // 2), 5, (0, 255, 0), -1)

    table_h = row
    for row in range(table_h + 1): 
        first_cell, last_cell = table_rois[row][0], table_rois[row][-1]

        cv2.putText(
            table_struct_img, f'{row}', 
            (first_cell[0] + 10, first_cell[1] + first_cell[3] - 10), 
            cv2.FONT_HERSHEY_SIMPLEX, 1.25, (0, 255, 0), 3)
        cv2.rectangle(
            table_img, 
            (first_cell[0], first_cell[1]), (first_cell[0] + first_cell[2], first_cell[1] + first_cell[3]),
            (0, 255, 0), 3)
        cv2.circle(table_struct_img, get_c(*first_cell), 20, (0, 0, 255), -1)

        cv2.putText(
            table_struct_img, f'{row}', 
            (last_cell[0] + 10, last_cell[1] + first_cell[3] - 10), 
            cv2.FONT_HERSHEY_SIMPLEX, 1.25, (0, 255, 0), 3)
        cv2.rectangle(
            table_img, 
            (last_cell[0], last_cell[1]), (last_cell[0] + last_cell[2], last_cell[1] + last_cell[3]),
            (0, 255, 0), 3)
        cv2.circle(table_struct_img, get_c(*last_cell), 10, (0, 0, 255), -1)


    cv2.imshow('table', table_img)
    cv2.imshow('table_struct', table_struct_img)
    
    return img














