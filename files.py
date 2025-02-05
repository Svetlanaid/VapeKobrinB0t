import requests
import re

from log import logger
from config import CLIENT_SHEETS, DOC_ID_REGEX

# Функция для загрузки содержимого Google Doc
def get_google_doc_text(doc_id):
    """
    Загружает текст из Google Docs по ID документа.

    :param doc_id: Идентификатор Google Docs документа.
    :return: Текст документа.
    :raises Exception: Если не удается загрузить документ.
    """
    try:
        logger.info(f"Загрузка текста из Google Doc с ID: {doc_id}")
        url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
        response = requests.get(url)
        if response.status_code == 200:
            logger.info("Документ успешно загружен.")
            return response.text
        else:
            logger.error(f"Не удалось загрузить документ: {response.status_code}")
            raise Exception(f"Не удалось загрузить документ: {response.status_code}")
    except Exception as e:
        logger.error(f"Ошибка при загрузке Google Doc: {e}")
        raise

# Извлекаем ID документа
def extract_doc_id(url_or_id):
    """
    Извлекает ID документа из URL или принимает ID документа.

    :param url_or_id: URL или ID документа.
    :return: Извлеченный ID документа.
    :raises Exception: Если не удается извлечь ID.
    """
    try:
        logger.info(f"Извлечение ID документа из URL: {url_or_id}")
        match = re.search(DOC_ID_REGEX, url_or_id)
        if match:
            doc_id = match.group(1)
            logger.info(f"ID документа успешно извлечен: {doc_id}")
            return doc_id
        else:
            logger.warning("ID документа не найден в URL.")
            return url_or_id
    except Exception as e:
        logger.error(f"Ошибка при извлечении ID документа: {e}")
        raise

# Загружаем товары из Google Sheets
def load_products_from_sheet(sheet_id, worksheet_name):
    """
    Загружает список товаров из Google Sheets.

    :param sheet_id: Идентификатор Google Sheets документа.
    :param worksheet_name: Название листа, с которого загружаются данные.
    :return: Список товаров в виде словарей.
    :raises Exception: Если не удается загрузить товары.
    """
    try:
        logger.info(f"Загрузка товаров из Google Sheets: sheet_id={sheet_id}, worksheet_name={worksheet_name}")
        sheet = CLIENT_SHEETS.open_by_key(sheet_id).worksheet(worksheet_name)
        products = sheet.get_all_records()
        if not products:
            logger.warning("Таблица пуста.")
            return []
        logger.info(f"Загружено {len(products)} товаров.")
        return products
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных из Google Sheets: {e}")
        return []