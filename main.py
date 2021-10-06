import asyncio
import logging

import database
from handlers import dp
from source.admins import send_admins

logger = logging.getLogger(__name__)


async def main():
    database.open_db()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logger.info("Starting bot")

    await dp.skip_updates()
    await dp.start_polling(dp)


async def send_error(e):
    await send_admins(f"❗ Ошибка при работе ❗\n{e}\n\n❗ Бот перезапустится автоматически")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        send_error(e)
