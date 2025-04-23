from datetime import date

import pandas as pd
from database import Session
import logging
from typing import List, Tuple, Optional

from models import SpimexTradingResult

# from parser import get_all_bulletin_links

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_table_boundaries(df: pd.DataFrame, start_marker: str, end_marker: str) -> Optional[Tuple[int, int]]:
    """Находит границы таблицы по маркерам начала и конца."""
    try:
        start_rows = df[df.iloc[:, 0] == start_marker]
        if start_rows.empty:
            logger.warning(f"Маркер начала таблицы '{start_marker}' не найден")
            return None

        start_row = start_rows.index[0]

        end_candidates = df.iloc[start_row + 3:][
            (df.iloc[start_row + 3:, 0] == end_marker) |
            (df.iloc[start_row + 3:, 0].isna())
            ]

        if end_candidates.empty:
            logger.warning(f"Маркер конца таблицы '{end_marker}' не найден после строки {start_row}")
            return None

        end_row = end_candidates.index[0]
        return start_row, end_row

    except Exception as e:
        logger.error(f"Ошибка при поиске границ таблицы: {str(e)}")
        return None


def clean_and_filter_data(df: pd.DataFrame, count_column: str) -> pd.DataFrame:
    """Очищает и фильтрует данные."""
    df[count_column] = pd.to_numeric(df[count_column], errors='coerce')
    df = df.dropna(subset=[count_column])
    df = df[df[count_column] > 0]

    numeric_cols = df.columns[3:6]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def panda_filter(link: str) -> pd.DataFrame:
    try:
        df = pd.read_excel(
            link,
            usecols='B:F,O',
            header=None,
            dtype=str
        )

        boundaries = find_table_boundaries(
            df,
            start_marker='Единица измерения: Метрическая тонна',
            end_marker='Итого:'
        )

        if not boundaries:
            return pd.DataFrame()

        start_row, end_row = boundaries

        df = df.iloc[start_row + 3:end_row].copy()
        df.reset_index(drop=True, inplace=True)

        count_column = df.columns[-1]
        df = clean_and_filter_data(df, count_column)

        return df

    except Exception as e:
        logger.error(f"Ошибка в panda_filter: {str(e)}")
        return pd.DataFrame()


def parse_row(row: Tuple, date: str) -> Optional[dict]:
    """Парсит одну строку данных в формат для БД."""
    try:
        exchange_product_id = str(row[1])

        return {
            'exchange_product_id': exchange_product_id,
            'exchange_product_name': str(row[2]),
            'oil_id': exchange_product_id[:4],
            'delivery_basis_id': exchange_product_id[4:7],
            'delivery_basis_name': str(row[3]),
            'delivery_type_id': exchange_product_id[-1],
            'volume': float(row[4]) if pd.notna(row[4]) else 0.0,
            'total': float(row[5]) if pd.notna(row[5]) else 0.0,
            'count': int(float(row[6])) if pd.notna(row[6]) else 0,
            'date': date
        }
    except Exception as e:
        logger.warning(f"Ошибка парсинга строки {row}: {str(e)}")
        return None


def process_spimex_bulletins(bulletin_list: List[dict]) -> None:
    """Обрабатывает список бюллетеней и сохраняет данные в БД."""
    session = Session()

    for bulletin in bulletin_list:
        date = bulletin['date']
        url = bulletin['url']

        try:
            logger.info(f"Обрабатываю бюллетень за {date}")

            df = panda_filter(url)

            if df.empty:
                logger.info(f"Нет данных для обработки в бюллетене за {date}")
                continue

            for row in df.itertuples(index=True, name='Pandas'):
                data = parse_row(row, date)
                if data:
                    save_to_db(session, data)

            session.commit()
            logger.info(f"Успешно обработан бюллетень за {date}")

        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при обработке бюллетеня за {date}: {str(e)}")

    session.close()


def save_to_db(session, data: dict) -> None:
    """Сохраняет данные в базу."""
    data = SpimexTradingResult(**data)
    session.add(data)
