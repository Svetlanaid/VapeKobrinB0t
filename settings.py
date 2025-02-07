import tiktoken  # Для подсчета токенов

from datetime import datetime, timedelta

from log import logger
from config import NEW_DIALOG_TIMEOUT, MAX_HISTORY_MESSAGES

def format_product_data(products):
    """
            Форматирует данные о товарах для вывода.

            :param products: Список товаров в виде словарей.
            :return: Строка с форматированными данными о товарах.
            """
    try:
        logger.info("Форматирование данных о товарах.")
        formatted_data = []
        current_category, current_subcategory = None, None

        for product in products:
            try:
                category = product['Категория']
                subcategory = product['Подкатегория']
                flavors = product.get('Вкусы', '').strip()
                colors = product.get('Цвета', '').strip()
                price = product['Цена']
                image_url = product.get('URL Изображения', '')

                # Разделяем вкусы и цвета по ";"
                flavors_list = [flavor.strip() for flavor in flavors.split(";") if flavor.strip()]
                colors_list = [color.strip() for color in colors.split(";") if color.strip()]

                if category != current_category:
                    current_category = category
                    formatted_data.append(f"# {current_category}")

                if subcategory != current_subcategory:
                    current_subcategory = subcategory
                    formatted_data.append(f"- {subcategory} - {price} р")

                # Добавляем вкусы или цвета
                if flavors_list or colors_list:
                    if flavors_list and colors_list:
                        formatted_data.append(
                            f"  {subcategory} содержит:\n"
                            f"  - Вкусы: {', '.join(flavors_list)}\n"
                            f"  - Цвета: {', '.join(colors_list)}"
                        )
                    elif flavors_list:
                        formatted_data.extend([f"  - {flavor}" for flavor in flavors_list])
                    elif colors_list:
                        formatted_data.extend([f"  - {color}" for color in colors_list])

                # Добавляем команду для изображения
                if image_url:
                    formatted_data.append(f"SEND_IMAGE: \"{image_url}\"")

            except KeyError as e:
                logger.error(f"Ошибка данных в товаре: {e}")
                continue

        logger.info("Форматирование данных завершено.")
        return "\n".join(formatted_data)

    except Exception as e:
        logger.error(f"Ошибка при форматировании данных: {e}")
        return ""



# Очистка сообщений старше суток и фильтрация актуальной истории
def filter_relevant_messages(history, user_id):
    """
        Фильтрует историю сообщений, оставляя только актуальные сообщения.

        :param history: История сообщений пользователя.
        :param user_id: Идентификатор пользователя.
        :return: Отфильтрованная история сообщений.
        """
    try:
        logger.info(f"Фильтрация истории сообщений для пользователя {user_id}.")
        now = datetime.now()
        last_message_time = history[-1]["timestamp"] if history else now
        dialog_start_time = last_message_time - timedelta(minutes=NEW_DIALOG_TIMEOUT)
        one_day_ago = now - timedelta(days=1)
        relevant_messages = [
            msg for msg in history
            if msg["timestamp"] > one_day_ago and msg["timestamp"] >= dialog_start_time
        ]
        logger.info(f"Отфильтровано {len(relevant_messages)} сообщений.")
        return relevant_messages[-MAX_HISTORY_MESSAGES:]
    except Exception as e:
        logger.error(f"Ошибка при фильтрации истории сообщений: {e}")
        return []

# Подсчет токенов с использованием tiktoken
def count_tokens(text):
    """
        Подсчитывает количество токенов в тексте.

        :param text: Текст для подсчета токенов.
        :return: Количество токенов.
        """
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(text)
        return len(tokens)
    except Exception as e:
        logger.error(f"Ошибка при подсчете токенов: {e}")
        return 0