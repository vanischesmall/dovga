import os
import re
import cv2 
import numpy as np
import pytesseract

from .page import Page
from .regexs import Patterns, get_float
from .table_parser import parse_table
from .text_opetations import text_confidence
from . import utils

from typing import Union, Optional
from collections import defaultdict



TEXT_CONFIDENCE = 60

CYRRILLIC_ALPHABET = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ0123456789'.lower()
OCR_CFG_NUMERIC = r'--oem 3 --psm 6 -c tessedit_char_whitelist=-.0123456789'

STREETS = [street.strip() for street in open(os.path.join('assets', 'streets.txt'))]



from random import randint
def randcolor() -> tuple[int, ...]:
    return (randint(0, 255), randint(0, 255), randint(0, 255))

def get_geom_c(x, y, w, h) -> tuple[int, int]: 
    return x + w // 2, y + h // 2



class Statement(object):
    TYPES = {
        "справка": "Справка",
        "реестр": "Реестр",
        "расчет": "Расчет",
    }

    MONTHES_FR = (
        'января',
        'февраля',
        'марта',
        'апреля',
        'мая',
        'июня',
        'июля',
        'августа',
        'сентября',
        'октября',
        'ноября',
        'декабря',
    )

    MONTHES_TO = (
        'январь',
        'февраль',
        'март',
        'апрель',
        'май',
        'июнь',
        'июль',
        'август',
        'сентябрь',
        'октябрь',
        'ноябрь',
        'декабрь',
    )

    def __init__(self) -> None: 
        self.__pages: list[Page] = []

        self.__type: Union[str, None] = None
        self.__total: Union[float, None] = None
        self.__period: Union[dict, None] = None
        self.__address: Union[dict, None] = None
        self.__ca_number: Union[str, None] = None
        self.__fine_table: Union[defaultdict, None] = None

    def get_type(self) -> "Statement":
        self.__process_title() 

        for i in range(len(self.__title_data['text'])):
            if not self.__title_data['text'][i]:
                continue

            for statement_type, statement_pattern in Statement.TYPES.items():
                if text_confidence(statement_pattern, self.__title_data['text'][i]) < TEXT_CONFIDENCE: 
                    continue 

                self.__type = statement_type
                self.__display_text_rect(
                    self.__pages[0].dst, self.__title_data, i, crop_rect=self.__title_rect)
                break

            if self.__type is not None:
                break
        return self

    def get_period(self) -> "Statement":
        if self.__type is None or self.__type == 'реестр':
            print(f'[WARN] Getting period from page {-1}: Type is {self.__type}')
            return self

        _month_fr: Union[dict, None] = None
        _month_to: Union[dict, None] = None
        for idx in range(len(self.__title_data['text'])):
            if not self.__title_data['text'][idx]:
                continue

            string = self.__title_data['text'][idx]
            if string == 'дата':
                continue 

            for fr_pattern, to_pattern in zip(Statement.MONTHES_FR, Statement.MONTHES_TO):
                fr_conf: int = text_confidence(fr_pattern, string)
                to_conf: int = text_confidence(to_pattern, string)

                if _month_fr is None or fr_conf > _month_fr['conf'] and fr_conf > to_conf: 
                    _month_fr = { 'value': fr_pattern.lower(), 'conf': fr_conf, 'idx': idx }

                if _month_to is None or to_conf > _month_to['conf'] and to_conf > fr_conf: 
                    _month_to = { 'value': to_pattern.lower(), 'conf': to_conf, 'idx': idx }

        year_fr:  Union[int, None] = None
        month_fr: Union[int, None] = None
        try:
            if _month_fr is not None:
                year_fr = int(re.findall(Patterns.YEAR, self.__title_data['text'][_month_fr['idx'] + 1])[0])
                month_fr = Statement.MONTHES_FR.index(_month_fr['value']) + 1

                self.__display_text_rect(
                    self.title_page, self.__title_data, _month_fr['idx'],     crop_rect=self.__title_rect, color=(255, 0, 255))
                self.__display_text_rect(
                    self.title_page, self.__title_data, _month_fr['idx'] + 1, crop_rect=self.__title_rect, color=(255, 0, 255))
        except:
            cv2.imshow('Period', self.__title_page)
            cv2.waitKey(1)

            print(f'\nОшибка при обработке периода: {_month_fr}')
            while True:
                try:
                    month_fr, year_fr = map(int, input('Введите дату начала периода в формате <номер месяца> <год>: ').split())
                    break
                except:
                    print('Неправильный формат ввода, повторите попытку')

        year_to:  Union[int, None] = None
        month_to: Union[int, None] = None
        try:
            if _month_to is not None:
                year_to = int(re.findall(Patterns.YEAR, self.__title_data['text'][_month_to['idx'] + 1])[0])
                month_to = Statement.MONTHES_TO.index(_month_to['value']) + 1

                self.__display_text_rect(
                    self.title_page, self.__title_data, _month_to['idx'],     crop_rect=self.__title_rect, color=(0, 255, 255))
                self.__display_text_rect(
                    self.title_page, self.__title_data, _month_to['idx'] + 1, crop_rect=self.__title_rect, color=(0, 255, 255))
        except:
            cv2.imshow('Period', self.__title_page)
            cv2.waitKey(1)

            print(f'\nОшибка при обработке периода: {_month_fr}')
            while True:
                try:
                    month_fr, year_fr = map(int, input('Введите дату начала периода в формате <номер месяца> <год>: ').split())
                    break
                except:
                    print('Неправильный формат ввода, повторите попытку')

        self.__period = {
            'from': { 'year': year_fr, 'month': month_fr },
            'to'  : { 'year': year_to, 'month': month_to },
        }

        return self

    def get_ca_number(self) -> "Statement":
        if self.__type in [None, 'справка']:
            print(f'[WARN] Getting CA from page {-1}: Type is {self.__type}')
            return self

        # find "Лицевой счет"
        idx, ca = max(
            [
                (i, f'{a} {b}')
                for i, (a, b) in enumerate(zip(self.__title_data['text'], self.__title_data['text'][1:]))
                if a and b #and (self.__title_data['conf'][i] + self.__title_data['conf'][i+1] // 2 >= TEXT_CONFIDENCE)
            ],
            key=lambda x: text_confidence('лицевой счет', x[1]) 
        ) 
        # assert text_confidence('лицевой счет', ca) >= TEXT_CONFIDENCE, f'[ERROR] No CA on page {-1}. Best match - {ca}'
        self.__display_text_rect(self.__pages[0].dst, self.__title_data, idx+1, crop_rect=self.__title_rect, color=(0, 255, 0))

        x, y, w, h = Statement.data_to_bbox(self.__title_data, idx + 1, self.__title_rect) # idx + 1 because we use счет
        y = max(0, y - 20)
        x = x + w 
        w = w * 8
        h = h + 30

        ca_crop = self.__pages[0].bin[y:y + h, x:x + w]
        # cv2.imshow('ca raw', ca_crop)

        ca_number_str = pytesseract.image_to_string(ca_crop, lang='remake', config=OCR_CFG_NUMERIC).strip()
        ca_number = re.findall(Patterns.CA, ca_number_str) or None

        if ca_number is None: 
            print('Ошибка при поиске лицевого счета')
            while True:
                try:
                    cv2.imshow('CA Number', self.__pages[0].bin)
                    cv2.waitKey(1)

                    data = input('\nВведите номер лицевого счета (Без P): ')
                    ca_number = re.findall(Patterns.CA, ca_number_str) or None

                    if not ca_number:
                        raise Exception 
                except:
                    print('Некорректный формат, повторите попытку')

        self.__ca_number = 'P' + ca_number[0]

        cv2.rectangle(self.__pages[0].dst, (x, y), (x + w, y + h), (0, 255, 0), 3)
        return self

    def get_address(self) -> "Statement":
        self.__address = {
            'street': None,
            'house': None,
            'aparts': None,
        }

        idx, addr = max(
            [
                (i, string)#, text_confidence('адрес', string)) 
                for i, string in enumerate(self.__title_data['text']) 
                if string #and self.__title_data['conf'][i] >= TEXT_CONFIDENCE
            ],
            key=lambda x: text_confidence('адрес', x[1])
        )
        self.__display_text_rect(
            self.__pages[0].dst, self.__title_data, idx, crop_rect=self.__title_rect, color=(0, 255, 0))

        x, y, w, h = Statement.data_to_bbox(self.__title_data, idx, self.__title_rect)
        y = max(0, y - 10)
        x = x + w + 20 
        w = w * 10
        h = h + 20

        address_crop = self.__pages[0].bin[y:y + h, x:x + w]
        for cont in cv2.findContours(address_crop, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)[0]:
            if cv2.contourArea(cont) < 50:
                cv2.fillPoly(address_crop, [cont], (0, 0, 0))

        if self.__type == 'справка':
            cv2.GaussianBlur(address_crop, (5, 5), 0, address_crop)

        self.__pages[0].dst[y:y + h, x:x + w] = cv2.cvtColor(address_crop, cv2.COLOR_GRAY2BGR)
        # cv2.imwrite(f'photos/addr2{self.__pages[0].idx}.png', address_crop)

        address_list: list = pytesseract.image_to_string(
            address_crop, lang='remake').lower().replace('.', ' ').replace(',', ' ').split()

        raw_street = ''.join(
            address_list[(address_list.index('ул') + 1 if 'ул' in address_list else 0):address_list.index('д')])
        self.__address['street'] = max(
            STREETS,
            key=lambda s: text_confidence(s, raw_street)
        )
        self.__address['house']     = ''.join(address_list[address_list.index('д' ) + 1:address_list.index('кв')])
        self.__address['aparts']    = ''.join(address_list[address_list.index('кв') + 1:])

        cv2.rectangle(self.__pages[0].dst, (x, y), (x + w, y + h), (0, 255, 0), 3)

        # cv2.imshow('address_processed', address_crop)
        return self

    def get_payments_total(self) -> "Statement":
        page = self.__pages[0]

        table_cont = max(
            [
                cont
                for cont in cv2.findContours(page.bin, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
                if cv2.contourArea(cont) > 2000
            ],
            key=lambda cont: utils.rect_geom_s(*cv2.boundingRect(cont))
        )
        table_bbox = cv2.boundingRect(table_cont)
        x, y, w, h = table_bbox

        table = page.bin[y:y + h, x:x + w]
        
        total_bbox = (
            x + w // 4 * 3, int(y + h // 6 * 4.75), 
            w - w // 4 * 3, int(h - h // 6 * 4.75),
        )

        cv2.rectangle(page.dst, (x, y), (x + w, y + h), (0, 255, 0), 5)

        x, y, w, h = total_bbox
        cv2.rectangle(page.dst, (x, y), (x + w, y + h), (0, 255, 255), 5)

                                # cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1)))

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

        table -= (struct := cv2.dilate(cv2.add(hor_lines_mask, ver_lines_mask), np.ones((11, 11), np.uint8)))

        total_crop = page.bin[y:y + h, x:x + w]
        total_mask = cv2.dilate(total_crop, 
                                np.ones((1, 20), np.uint8))
        cv2.dilate(total_mask, np.ones((5, 5), np.uint8), total_mask)

        # cv2.imshow('mask', total_mask)
        x, y, w, h = cv2.boundingRect(
            max(
                [
                    cont 
                    for cont in cv2.findContours(total_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
                    if cv2.contourArea(cont) > 1000
                ],
                key=lambda cont: (cv2.contourArea(cont), cv2.boundingRect(cont)[1])
            )
        )

        total_crop = total_crop[y:y + h, x:x + w]
        hh = int(h * 1.00)
        ww = int(w * 0.05)

        row_bg = np.zeros((h + 2 * hh, w + 2 * ww), np.uint8)
        row_bg[hh:h + hh, ww:w + ww] = total_crop
        total_crop = row_bg
        cv2.GaussianBlur(total_crop, (5, 5), 0, total_crop)

        # cv2.imshow('table', table)
        # cv2.imshow('total_crop', total_crop)
        # cv2.imshow('total_struct', struct)

        data_raw = pytesseract.image_to_data(total_crop, lang='remake', config=OCR_CFG_NUMERIC, output_type=pytesseract.Output.DICT)
        try:
            idx = max(
                [
                    i 
                    for i in range(len(data_raw['text']))
                    if re.findall(Patterns.FLOAT, data_raw['text'][i].replace(',', '.')) and data_raw['conf'][i] > TEXT_CONFIDENCE
                ], key=lambda i: data_raw['top'][i]
            )

            data = re.findall(Patterns.FLOAT, data_raw['text'][idx].replace(',', '.'))
            self.__total = float(data[0])

            cv2.putText(
                page.dst, str(self.__total), 
                (table_bbox[0], table_bbox[1] - 20), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 5)
        except:
            cv2.imshow('table', table)
            cv2.waitKey(1)

            # print(data_raw['text'])
            print(f'\nОшибка при поиске итоговой суммы. ', end='')

            while True:
                try:
                    data = input('Введите итоговую сумму: ')
                    self.__total = float(data)

                    cv2.putText(
                        page.dst, str(self.__total), 
                        (table_bbox[0], table_bbox[1] - 20), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 5)
                    break
                except:
                    print('Неправильный формат ввода. Повторите попытку')
                cv2.destroyAllWindows()

            # x, y, w, h = total_bbox
            # fail_mask = np.zeros(page.src[y:y + h, x:x + w].shape, np.uint8)
            #
            # cv2.rectangle(fail_mask, (x, y), (x + w, y + h), (0, 0, 255), -1)
            # page.dst[y:y + h, x:x + w] = cv2.addWeighted(page.dst[y:y + h, x:x + w], 0.5, fail_mask, 0.5, 1.0)
        # while cv2.waitKey(1) != ord('n'): pass

        return self


    def process(self) -> dict: 
        self.get_type().get_address()

        match self.__type:
            case "справка":
                self.get_period().get_payments_total()

            case "реестр":
                self.get_ca_number()
                for page in self.__pages[1:]:
                    page.process()

                self.__fine_table = parse_table(self.__pages)

            case "расчет":
                self.get_period().get_ca_number()

        cv2.destroyAllWindows()
        return self.__generate_description()

    def __process_title(self) -> "Statement":
        self.__pages[0].process()

        H, W = self.__pages[0].bin.shape

        self.__title_rect: tuple[int, ...] = tuple(map(int, (
            0.01 * W, 0.02 * H,
            0.75 * W, 0.3 * H
        )))
        self.__title_page: np.ndarray = self.__pages[0].bin[
            self.__title_rect[1]:self.__title_rect[3], 
            self.__title_rect[0]:self.__title_rect[2],
        ]

        self.__title_data: dict = pytesseract.image_to_data(
            self.__title_page, lang='remake', output_type=pytesseract.Output.DICT)

        # cv2.rectangle(self.__pages[0].dst, 
        #               (self.__title_rect[0], self.__title_rect[1]), 
        #               (self.__title_rect[2], self.__title_rect[3]), 
        #               (0, 255, 0), 5
        # )

        return self

    def __generate_description(self) -> dict: 
        _fine_table_value = 'defined' if self.__fine_table is not None else None

        self.__description = {
            'type': self.__type,
            'total': self.__total,
            'period': self.__period,
            'address': self.__address,
            'ca_number': self.__ca_number,
            'fine_table': self.__fine_table,
        }

        return self.__description

    def __display_text_rect(
        self,
        src: np.ndarray,
        data: dict, 
        i: int, 
        text: str = '', 
        crop_rect: tuple[int, ...] = (0, 0, 0, 0), 
        color: tuple[int, ...] = (0, 255, 0),
    ) -> None:
        x, y, w, h = Statement.data_to_bbox(data, i, crop_rect)

        cv2.rectangle(src, (x, y), (x+w, y+h), color, 3)
        if text:
            cv2.putText(
                src, text,
                (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3, cv2.LINE_AA,
            )

    @staticmethod
    def data_to_bbox(data: dict, i: int, crop_rect = (0, 0, 0, 0)) -> tuple[int, ...]:
        x = data['left'][i] + crop_rect[0]
        y = data['top'][i]  + crop_rect[1]
        w = data['width'][i]
        h = data['height'][i]

        return x, y, w, h

    def add_page(self, page: Page) -> None: 
        self.__pages.append(page)

    def get_page(self, page_idx: int) -> Page: 
        return self.__pages[page_idx]
    
    def get_page_idx(self, page_idx: int) -> int: 
        return self.__pages[page_idx].idx

    @property 
    def pages(self):
        return self.__pages

    @property 
    def title_page(self):
        return self.__pages[0].dst

    @property 
    def period(self):
        return self.__period

    @property 
    def address(self):
        return self.__address

    @property
    def description(self):
        return self.__description

    @property
    def report(self):
        return self.__description

    @property 
    def type(self):
        return self.__type
    
    @property 
    def total(self) -> Union[float, None]:
        return self.__total

    @property 
    def fine_table(self) -> Union[defaultdict, None]: 
        return self.__fine_table

