# data_provider.py
from make_document import generate_documents, generate_excel_report

# Ваши данные
DEBTS_DATA = [
    {
        "address": {
            "street": "Проспект Красного Знамени",
            "house": "119",
            "aparts": "45"
        },
        "period": {
            "from": {"month": "01", "year": "2023"},
            "to": {"month": "12", "year": "2023"}
        },
        "ca_number": "123456789",
        "total": 15000.50,
        "fine_total": 500.25
    }
]

def get_debts_data():
    """Возвращает данные и может сразу генерировать документы"""
    return DEBTS_DATA

def generate_all_documents(SS):
    """Генерирует все документы для всех данных"""
    cases = []
    for json_data in SS:
        result = generate_documents(json_data)
        if result:
            cases.append(result['data'])
    
    if cases:
        excel_path = generate_excel_report(cases)
        print(f"Excel отчет создан: {excel_path}")
