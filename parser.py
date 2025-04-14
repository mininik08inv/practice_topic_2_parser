import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
from config import START_YEAR

BASE_URL = 'https://spimex.com'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def get_all_bulletin_links():
    all_links = []
    page_num = 1

    while True:
        if page_num == 1:
            url = f'{BASE_URL}/markets/oil_products/trades/results/'
        else:
            url = f'{BASE_URL}/markets/oil_products/trades/results/?page=page-{page_num}'

        print(f"Обрабатываю страницу {page_num}... URL: {url}")

        try:
            # time.sleep(2)  # Увеличиваем задержку
            response = requests.get(url, headers=HEADERS)

            soup = BeautifulSoup(response.text, 'lxml')

            # Пробуем разные варианты поиска контейнера
            accordeon = (soup.find('div', class_='accordeon-inner__wrap') or
                         soup.find('div', class_='accordeon-inner') or
                         soup.find('div', {'class': 'accordeon'}))

            items = accordeon.find_all('div', class_=lambda x: x and 'accordeon-inner__item' in x)

            if not items:
                print("Пробуем альтернативный поиск элементов...")
                items = soup.find_all('div', class_=lambda x: x and 'item' in x and 'xls' in x)

            if not items:
                print("Не найдено бюллетеней на странице.")
                break

            # Флаг для остановки, если достигли бюллетеней старше START_YEAR
            should_stop = False

            for item in items:
                try:
                    # Извлекаем дату торгов
                    date_span = item.find('span')
                    if not date_span:
                        continue

                    date_str = date_span.text.strip()
                    trade_date = datetime.strptime(date_str, '%d.%m.%Y').date()

                    # Проверяем, не старше ли START_YEAR года
                    if trade_date.year < START_YEAR:
                        should_stop = True
                        break

                    # Извлекаем ссылку на XLS
                    link_tag = item.find('a')
                    if not link_tag or 'href' not in link_tag.attrs:
                        continue

                    link = link_tag['href']
                    full_link = urljoin(BASE_URL, link)

                    # Добавляем в список с датой
                    all_links.append({
                        'date': trade_date,
                        'url': full_link
                    })
                except Exception as e:
                    print(f"Ошибка при обработке элемента: {e}")
                    continue

            if should_stop:
                print(f"Достигнуты бюллетени за {trade_date.year} год, завершаю сбор.")
                break

            # Проверяем, есть ли следующая страница
            next_page = soup.find('li', class_='bx-pag-next')
            if not next_page or 'disabled' in next_page.get('class', []):
                print("Это последняя страница, завершаю сбор.")
                break

            page_num += 1

        except Exception as e:
            print(f"Ошибка при обработке страницы {page_num}: {str(e)}")
            break

    # Сортируем ссылки по дате (от новых к старым)
    all_links.sort(key=lambda x: x['date'], reverse=True)

    return all_links

