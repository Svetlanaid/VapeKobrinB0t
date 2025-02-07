from aiogram import Router
from aiogram.types import Message
from aiogram import Bot

from gpt import generate_ai_response
from log import logger

from config import TOKEN, ADMIN_ID  # Укажите ваш Telegram ID в config.py

bot = Bot(token=TOKEN)

router = Router()

# Функция для отправки уведомления админу
async def notify_admin(user_id, response):
    """Отправляет уведомление админу о новом заказе."""
    message = f"🛒 Новый заказ от пользователя {user_id}:\n{response}"
    await bot.send_message(ADMIN_ID, message)

# Обработчик сообщений в боте
@router.message()
async def handle_message(message: Message):
    """
        Обрабатывает входящее сообщение от пользователя.

        :param message: Сообщение от пользователя.
        :raises Exception: Если происходит ошибка при обработке сообщения.
        """
    try:
        user_input = message.text
        user_id = message.from_user.id
        logger.info(f"Получено сообщение от пользователя {user_id}: {user_input}")

        logger.info(f"Генерация ответа Qwen для пользователя {user_id}.")
        response, input_tokens, output_tokens = await generate_ai_response(user_input, user_id)

        # Проверяем, оформлен ли заказ
        if "ваш заказ оформлен" in response.lower():
            await notify_admin(user_id, response)  # Отправляем уведомление админу

        # Добавляем информацию о токенах в ответ
        full_response = (
            f"{response}\n\n"
            f"📊 Статистика токенов:\n"
            f"- Входные токены: {input_tokens}\n"
            f"- Выходные токены: {output_tokens}"
        )
        await message.answer(full_response)
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")