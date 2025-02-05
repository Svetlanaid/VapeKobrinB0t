import asyncio
import logging

from openai import OpenAI
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from datetime import datetime

from handler import router
from config import TOKEN, SCOPE, QWEN_API_KEY, BASE_URL
from log import logger

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Инициализация клиента DeepSeek
client = OpenAI(api_key=QWEN_API_KEY, base_url=BASE_URL)

# Запуск бота
if __name__ == "__main__":
    async def main():
        """
    Запускает бота и обрабатывает сообщения с использованием Aiogram.

    :raises Exception: Если возникает ошибка при запуске бота.
    """
        try:
            logger.info("Запуск бота.")
            dp.include_router(router)
            await dp.start_polling(bot, skip_updates=True)
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")


    asyncio.run(main())