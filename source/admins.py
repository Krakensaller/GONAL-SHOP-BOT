from loader import bot
from src.config import ADMIN_ID


async def send_admins(message_text, keyboard=None):
    """
    Отправка сообщений всем админам

    :param message_text: сообщение
    :param keyboard: при необходимости клавиатура
    :return:
    """
    for i in range(len(ADMIN_ID)):
        await bot.send_message(ADMIN_ID[i], message_text, reply_markup=keyboard)
