import logging
from json import dumps


from lib.document_parser import DocumentParser
from lib.text_opetations import text_confidence
from make_document import generate_documents, generate_excel_report

SCAN_PATH = 'assets/input2.pdf'

from collections import Counter

def most_frequent_address(addresses):
    address_tuples = [
        (addr["street"], addr["house"], addr["aparts"])
        for addr in addresses
    ]
    
    counter = Counter(address_tuples)
    
    most_common = counter.most_common(1)[0][0]
    
    return {
        "street": most_common[0],
        "house": most_common[1],
        "aparts": most_common[2]
    }

def get_total_fine(period, table): 
    sm = 0.0
    monthes = get_perd(period)

    for month in monthes:
        sm += table[month]

    return round(sm, 2)

def get_perd(period):
    monthes = [] 

    fy, fm = period['from']['year'], period['from']['month']
    ty, tm = period['to']['year'], period['to']['month']

    for year in range(int(ty), int(ty) + 1):
        for month in range(1 if year != int(fy) else fm, (12 if year != int(ty) else tm) + 1):
            month = str(month) 
            if len(month) == 1: 
                month = '0' + month
            monthes.append(f'{month}.{year}')

    return monthes

def get_addr(rep) -> str:
    return f"{rep['address']['street']} {rep['address']['house']} {rep['address']['aparts']}"

def gendoc(statement):
    result = generate_documents(statement)
    if result is not None:
        generate_excel_report(result['data'])
    
    else:
        print('nan')

def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    print()

    reports = list()
    statements = list()

    doc_parser = DocumentParser(path=SCAN_PATH)
    while True:
        statement = doc_parser.collect_statement()
        reports.append(statement.report)

        # print(dumps(statement.description, indent=4, ensure_ascii=False))
        # print()

        if doc_parser.end:
            print('Конец!')
            break

    _reports = reports.copy()
    while _reports:
        rep = _reports[0]
        reps = sorted(_reports, key=lambda _rep: text_confidence(get_addr(rep), get_addr(_rep)))[:3]

        _statement = {}
        for _rep in reps:
            _reports.remove(_rep)

            typ = _rep['type'] 
            if typ == 'реестр':
                _statement['reestr'] = _rep

            if typ == 'справка':
                _statement['spravka'] = _rep

            if typ == 'расчет':
                _statement['raschet'] = _rep

        address = most_frequent_address([x['address'] for _, x in _statement.items()])
        period = {
            'from': {
                'month': str(_statement['raschet']['period']['from']['month']),
                'year': str(_statement['raschet']['period']['from']['year']),
            },
            'to': {
                'month': str(_statement['raschet']['period']['to']['month']),
                'year': str(_statement['raschet']['period']['to']['year']),
            }
        }

        total = _statement['spravka']['total']
        total_fine = get_total_fine(_statement['spravka']['period'], _statement['reestr']['fine_table'])
        ca_number = _statement['reestr']['ca_number']

        statement = {
            'address': address,
            'total': total,
            'fine_total': total_fine,
            'period': period,
            'ca_number': ca_number
        }
        print('\n\n==========================================')
        # print(statement)
        print(dumps(statement, indent=4, ensure_ascii=False))

        gendoc(statement)


    print(len(statements))
    # for statement in statements: 


if __name__ == "__main__":
    main()
