import collections
import random
from datetime import datetime

from aiogram import types

import database
from src.config import COMMENT


def format_stat(dict_data):
    """
    Форматирование данных для статистики

    :param dict_data: словарь с данными
    :return:
    """
    result = ""
    for key, value in collections.Counter(dict_data).most_common(10):
        result += f"▫ {key} - {value}\n"

    return result


def item_format(item):
    """
    Создание текста для кнопки с товаром

    :param item: объект из БД с товаром
    :return:
    """
    return f"{item[1]} | {item[4]} руб. | {database.get_item_count(item[0])} шт."


def create_comment():
    """
    Генерация комментария для оплаты

    :return:
    """
    key_pass = list("1234567890QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm")
    random.shuffle(key_pass)
    key_buy = "".join([random.choice(key_pass) for i in range(15)])

    return f"{COMMENT}:{key_buy}"


def get_now_date():
    """
    Получение текущей даты

    :return:
    """
    now_data = datetime.now()

    return now_data.strftime("%d/%m/%Y")


def get_buy_message(message: types.Message, purchase_data, user_mode):
    """
    Получение сообщения о покупке

    :param message: types.Message
    :param purchase_data: данные о покупке
    :param user_mode: true - режим пользователя, false - админ
    :return:
    """
    if user_mode:
        return "🛒 Информация о покупке\n" \
               f"➖➖➖➖➖➖➖➖➖➖\n" \
               f"🆔 Номер покупки: <b>{purchase_data['sale_id']}</b>\n" \
               f"➖➖➖➖➖➖➖➖➖➖\n" \
               f"📙 Название товара: <b>{purchase_data['item_name']}</b>\n" \
               f"📦 Количество: <b>{purchase_data['count']} шт.</b>\n" \
               f"💰 Сумма покупки: <b>{purchase_data['amount']} руб.</b>\n" \
               f"➖➖➖➖➖➖➖➖➖➖\n" \
               f"📱 Данные:\n\n"
    else:
        return "🛒 Новая покупка\n" \
               f"➖➖➖➖➖➖➖➖➖➖\n" \
               f"🆔 Номер покупки: <b>{purchase_data['sale_id']}</b>\n" \
               f"🙍‍♂ Покупатель: <b>@{message.chat.username}</b>\n" \
               f"#️⃣ ID пользователя: <b>{message.chat.id}</b>\n" \
               f"➖➖➖➖➖➖➖➖➖➖\n" \
               f"📙 Название товара: <b>{purchase_data['item_name']}</b>\n" \
               f"📦 Количество: <b>{purchase_data['count']} шт</b>\n" \
               f"💰 Сумма покупки: <b>{purchase_data['amount']} руб.</b>\n" \
               f"➖➖➖➖➖➖➖➖➖➖\n" \
               f"💳 Способ оплаты: <b>{purchase_data['payment_type']}</b>\n" \
               f"➖➖➖➖➖➖➖➖➖➖\n" \
               f"📱 Данные:\n\n"
