import pandas as pd
import re

PATH_TO_ASSETS = 'assets/'

def normalize_street_name(name: str) -> str:
    """Приводит название улицы к каноничному виду без 'ул.', 'просп.' и т.п."""
    name = str(name).lower()
    name = re.sub(r'[.,]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    drop = {
        "ул", "улица", "проспект", "пр", "пр-кт", "пр-кт.", 
        "пер", "переулок", "бульвар", "бул", "бул.", 
        "шоссе", "ш", "наб", "набережная", 
        "территория", "тер"
    }
    tokens = [t for t in name.split() if t not in drop]
    return " ".join(tokens)

def load_and_prepare(path: str, name_col: str, split_by_comma: bool):
    """
    Читает Excel:
      name_col       – как назвать колонку с судом/ук
      split_by_comma – True=сплит по запятой, False=по пробелу
    Возвращает DataFrame с колонками [name_col, 'street', 'houses']
    """
    df = pd.read_excel(path, dtype=str)
    df = df.rename(columns={
        df.columns[0]: name_col,
        df.columns[1]: 'street_raw',
        df.columns[2]: 'houses_raw'
    })
    df['street'] = df['street_raw'].apply(normalize_street_name)
    
    def parse_houses(raw: str) -> list:
        if pd.isna(raw) or not raw.strip():
            return []
        parts = raw.split(',') if split_by_comma else raw.split()
        clean = []
        for p in parts:
            p = p.strip().lower()
            m = re.match(r'[\d\w\-/]+', p)
            if m:
                clean.append(m.group())
        return clean
    
    df['houses'] = df['houses_raw'].apply(parse_houses)
    return df[[name_col, 'street', 'houses']]

def load_uk_info(path: str):
    df = pd.read_excel(path, dtype=str)
    df = df.rename(columns={
        df.columns[0]: 'uk',
        df.columns[1]: 'number',
        df.columns[2]: 'location',
        df.columns[3]: 'inn',
        df.columns[4]: 'kpp',
        df.columns[5]: 'ogrn',
        df.columns[6]: 'reg_date'
    })
    
    df['uk_norm'] = df['uk'].str.strip().str.lower()
    return df

def find_matches(df: pd.DataFrame, street: str, house: str, name_col: str):
    street_n = normalize_street_name(street)
    house_n  = house.strip().lower()

    # разбиваем сложный ввод: напр. '111ас120' → ['111а', 'с120']
    query_parts = re.findall(r'\d+\w*|[a-zа-я]+[\d/]*', house_n)

    def match_houses(house_list):
        if not house_list:
            return True  # пустой список → любые дома
        return any(part in house_list for part in query_parts)

    mask = (
        (df['street'] == street_n) &
        df['houses'].apply(match_houses)
    )
    return df[mask][[name_col]]

def load_court_regions(path: str):
    df = pd.read_excel(path, dtype=str)
    df = df.rename(columns={
        df.columns[0]: 'court',
        df.columns[1]: 'region'
    })
    df['court_norm'] = df['court'].str.strip().str.lower()
    return df[['court_norm', 'region']]

def get_address_info(street=None, house=None, appart=None):
    """
    Основная функция для получения информации по адресу.
    Может быть вызвана из других модулей.
    """
    if street is None or house is None or appart is None:
        # Режим интерактивного ввода (для командной строки)
        if street is None:
            street = input("Улица: ")
        if house is None:
            house = input("Номер дома: ")
        if appart is None:
            appart = input("Номер квартиры: ")
    else:
        # Режим работы с переданными параметрами (для API)
        street = str(street)
        house = str(house)
        appart = str(appart)

    courts_df = load_and_prepare(f'{PATH_TO_ASSETS}Суды.xlsx', name_col='court', split_by_comma=False)
    uk_df = load_and_prepare(f'{PATH_TO_ASSETS}УправляющиеКомпании.xlsx', name_col='uk', split_by_comma=True)
    uk_info_df = load_uk_info(f'{PATH_TO_ASSETS}Данные_о_УК.xlsx')
    court_regions_df = load_court_regions(f'{PATH_TO_ASSETS}Данные_о_судах.xlsx')

    normalized_street = normalize_street_name(street)
    house_parts = re.findall(r'\d+\w*|[а-яa-z]+[\d/]*', house.lower())

    found_courts = find_matches(courts_df, street, house, 'court')
    found_uks = find_matches(uk_df, street, house, 'uk')

    matched_courts_list = []
    for _, r in found_courts.iterrows():
        court_name = r['court']
        court_norm = court_name.strip().lower()
        info = court_regions_df[court_regions_df['court_norm'] == court_norm]
        region = info.iloc[0]['region'] if not info.empty else "неизвестно"

        matched_courts_list.append({
            "court": court_name,
            "region": region,
        })

    matched_uks_list = []
    for _, r in found_uks.iterrows():
        uk_name = r['uk']
        uk_norm = uk_name.strip().lower()
        info = uk_info_df[uk_info_df['uk_norm'] == uk_norm]
        if not info.empty:
            matched_uks_list.append({
                "uk": uk_name,
                "number": info.iloc[0]['number'],
                "location": info.iloc[0]['location'],
                "inn": info.iloc[0]['inn'],
                "kpp": info.iloc[0]['ogrn'],
                "ogrn": info.iloc[0]['reg_date'],
                "reg_date": info.iloc[0]['kpp']
            })
        else:
            matched_uks_list.append({
                "uk": uk_name,
                "number": "неизвестно",
                "location": "неизвестно",
                "inn": "неизвестно",
                "kpp": "неизвестно",
                "ogrn": "неизвестно",
                "reg_date": "неизвестно"
            })

    return {
        "raw_street": street,
        "raw_house": house,
        "normalized_street": normalized_street,
        "house_parts": house_parts,
        "courts": matched_courts_list,
        "uks": matched_uks_list,
        "appart": appart,
    }
        
def print_results(results):
    """Печатает результаты в удобном формате"""
    print(f"\nРезультаты для адреса: «{results['raw_street'].title()}, {results['raw_house']}, {results['appart']}»\n")

    if results['courts']:
        print("Суды:")
        for court in results['courts']:
            print(f"  – {court['court']} (район: {court['region']})")
    else:
        print("Суды: не найдены")

    print()

    if results['uks']:
        print("Управляющие компании:")
        for uk in results['uks']:
            print(f"  – {uk['uk']}")
            print(f"    Номер: {uk['number']}")
            print(f"    Местонахождение: {uk['location']}")
            print(f"    ИНН: {uk['inn']}")
            print(f"    КПП: {uk['kpp']}")
            print(f"    ОГРН: {uk['ogrn']}")
            print(f"    Дата гос. регистрации: {uk['reg_date']}\n")
    else:
        print("Управляющие компании: не найдены")

def main():
    """Основная функция для запуска из командной строки"""
    results = get_address_info()
    print_results(results)
    return results

if __name__ == "__main__":
    main()
