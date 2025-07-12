import cv2
import numpy as np

def detect_table_with_hough(img_gray):
    img = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)

    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    horizontal_lines = cv2.morphologyEx(img_gray, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)

    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    vertical_lines = cv2.morphologyEx(img_gray, cv2.MORPH_OPEN, vertical_kernel, iterations=2)

    table_structure = cv2.add(horizontal_lines, vertical_lines)

    contours, _ = cv2.findContours(table_structure, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # image_with_tables = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)
    # cv2.drawContours(image_with_tables, contours, -1, (0, 255, 0), 2)
    print(vertical_lines)
    cv2.drawContours(img_gray, contours, -1, 0, 4)

    return img_gray
