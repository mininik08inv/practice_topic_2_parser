from datetime import date

from parser import get_all_bulletin_links
from save_to_database import process_spimex_bulletins


def main():
    bulletin_list = get_all_bulletin_links()
    # Проверка на двух страницах
    # bulletin_list = [
    #     {'date': date(2025, 4, 11),
    #      'url': 'https://spimex.com/upload/reports/oil_xls/oil_xls_20250411162000.xls?r=3359'},
    #     {'date': date(2025, 4, 10),
    #      'url': 'https://spimex.com/upload/reports/oil_xls/oil_xls_20250410162000.xls?r=6915'},
    # ]
    process_spimex_bulletins(bulletin_list)


if __name__ == "__main__":
    main()
