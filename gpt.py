import requests

from datetime import datetime, timedelta

from files import extract_doc_id, get_google_doc_text, load_products_from_sheet
from config import SHEET_ID, WORKSHEET_NAME, DOC_URL, QWEN_API_KEY, NEW_URL
from settings import format_product_data, filter_relevant_messages, count_tokens
from log import logger

# Словарь для хранения истории сообщений пользователей
user_history = {}

# Генерируем ответ с помощью HTTP API Qwen
async def generate_ai_response(user_input, user_id):
    """
        Генерирует ответ с использованием API Qwen на основе ввода пользователя.

        :param user_input: Ввод пользователя.
        :param user_id: Идентификатор пользователя.
        :return: Кортеж с ответом, количеством входных и выходных токенов.
        :raises Exception: Если возникает ошибка при запросе к API.
        """
    try:
        logger.info(f"Генерация ответа Qwen для пользователя {user_id}.")
        doc_id = extract_doc_id(DOC_URL)
        system_prompt = get_google_doc_text(doc_id)
        products = load_products_from_sheet(SHEET_ID, WORKSHEET_NAME)
        product_info = format_product_data(products)
        if product_info.strip():
            system_prompt += f"\n\nСписок товаров:\n{product_info}"

        history = user_history.get(user_id, [])
        filtered_history = filter_relevant_messages(history, user_id)

        messages = [{"role": "system", "content": system_prompt}]
        for msg in filtered_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_input})

        # Подсчет входных токенов
        input_tokens = sum(count_tokens(msg["content"]) for msg in messages)
        logger.info(f"Входные токены: {input_tokens}")

        # Отправляем запрос к HTTP API Qwen
        url = NEW_URL
        headers = {
            "Authorization": f"Bearer {QWEN_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "qwen-turbo",
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 500,
            "frequency_penalty": 0.5
        }
        response = requests.post(url, json=data, headers=headers, timeout=10)

        if response.status_code == 200:
            result = response.json()
            assistant_content = result["choices"][0]["message"]["content"]

            # Подсчет выходных токенов
            output_tokens = count_tokens(assistant_content)
            logger.info(f"Выходные токены: {output_tokens}")

            current_time = datetime.now()
            user_history.setdefault(user_id, []).append(
                {"role": "user", "content": user_input, "timestamp": current_time}
            )
            user_history[user_id].append(
                {"role": "assistant", "content": assistant_content, "timestamp": current_time}
            )
            logger.info("Ответ Qwen успешно сгенерирован.")
            return assistant_content, input_tokens, output_tokens
        else:
            logger.error(f"Ошибка API Qwen: {response.status_code}, {response.text}")
            return f"Ошибка API: {response.status_code}", 0, 0
    except Exception as e:
        logger.error(f"Ошибка при генерации ответа Qwen: {e}")
        return f"Ошибка: {str(e)}", 0, 0

