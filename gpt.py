import requests
import re
from openai import OpenAI
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
import asyncio

# Telegram bot token
TOKEN = "8148487118:AAHvC3XYnYClpJjRRyXqVHvL_vJrN5vfZ9o"
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Инициализация клиента DeepSeek
client = OpenAI(
    api_key="sk-2c72d7110b7141dda676ec6ea7e42b73",
    base_url="https://api.deepseek.com/v1"
)

# Настройка доступа к Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client_sheets = gspread.authorize(creds)

# Фиксированная ссылка на документ
DOC_URL = "https://docs.google.com/document/d/1dg8CKU1w5StO9KbiOM-mwmv7AokRx-KTydIBFOxkTv4/edit?usp=sharing"
SHEET_ID = "1gYhoyLtuBy7cVzwGibn2ZrA4k8WiCOtct744BinNWnw"
WORKSHEET_NAME = "Лист1"

# Словарь для корзины пользователей
user_cart = {}

# Функция для загрузки содержимого Google Doc
def get_google_doc_text(doc_id):
    url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Не удалось загрузить документ: {response.status_code}")

# Извлекаем ID документа
def extract_doc_id(url_or_id):
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url_or_id)
    return match.group(1) if match else url_or_id

# Загружаем товары из Google Sheets
def load_products_from_sheet(sheet_id, worksheet_name):
    sheet = client_sheets.open_by_key(sheet_id).worksheet(worksheet_name)
    return sheet.get_all_records()

# Форматируем данные о товарах
def format_product_data(products):
    formatted_data = []
    current_category, current_subcategory = None, None
    for product in products:
        try:
            category = product['Категория']
            subcategory = product['Подкатегория']
            name = product['Название товара']
            price = product['Цена']

            if category != current_category:
                current_category = category
                formatted_data.append(f"# {current_category}")

            if subcategory != current_subcategory:
                current_subcategory = subcategory
                formatted_data.append(f"## {subcategory} - {price} р")

            formatted_data.append(f"### {name}")

        except KeyError as e:
            print(f"Ошибка данных: {e}")
            continue

    return "\n".join(formatted_data)

# Генерируем ответ с ИИ
async def generate_ai_response(user_input, user_id):
    try:
        # Загружаем промпт
        doc_id = extract_doc_id(DOC_URL)
        system_prompt = get_google_doc_text(doc_id)

        # Загружаем товары
        products = load_products_from_sheet(SHEET_ID, WORKSHEET_NAME)
        product_info = format_product_data(products)

        if product_info.strip():
            system_prompt += f"\n\nСписок товаров:\n{product_info}"

        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_input}]

        # Запрос к модели
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            frequency_penalty=0.5
        )

        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка: {str(e)}"

# Добавление товара в корзину
def add_to_cart(user_id, product_name):
    if user_id not in user_cart:
        user_cart[user_id] = []
    user_cart[user_id].append(product_name)

# Показ корзины
def view_cart(user_id):
    if user_id in user_cart and user_cart[user_id]:
        cart_items = "\n".join(user_cart[user_id])
        return f"В вашей корзине:\n{cart_items}"
    else:
        return "Ваша корзина пуста."

# Обработчик сообщений в боте
@dp.message_handler()
async def handle_message(message: Message):
    user_input = message.text
    user_id = message.from_user.id

    # Проверка на команду /корзина
    if user_input.lower() == "/корзина":
        cart_response = view_cart(user_id)
        await message.answer(cart_response)
    else:
        # Добавление товара в корзину, если он выбран
        if "купить" in user_input.lower():
            product_name = user_input.split("купить")[-1].strip()  # Получаем название товара
            add_to_cart(user_id, product_name)
            await message.answer(f"Товар {product_name} добавлен в вашу корзину.")

        # Генерация ответа от ИИ
        response = await generate_ai_response(user_input, user_id)
        await message.answer(response)

# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
