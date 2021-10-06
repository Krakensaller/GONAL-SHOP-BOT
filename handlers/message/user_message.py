from aiogram import types
from aiogram.dispatcher import FSMContext

import database
from loader import dp
from source.admins import send_admins
from source.states import BotStates
from source.support.support_user import select_type
from src import config, keyboards
from src.config import is_admin
from src.const import *
from src.keyboards import user_keyboard, admin_keyboard, create_list_keyboard


# # # Запуск магазина # # #

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    """
    Стартовое сообщение

    :param message:
    :return:
    """
    added_user = database.add_user(message.chat.id)

    if config.is_admin(message.chat.id):
        keyboard = admin_keyboard
    else:
        keyboard = user_keyboard

    if added_user:
        # новый юзер
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row(const_ru['accept_rules'])

        message_text = database.get_param("rules")
        await BotStates.new_user.set()
    else:
        # уже смешарик
        message_text = database.get_param("comeback_message").format(username=message.chat.username)

    await message.answer(message_text, reply_markup=keyboard)


@dp.message_handler(regexp=const_ru['accept_rules'], state=BotStates.new_user)
async def hello_message(message: types.Message, state: FSMContext):
    """
    Вызов приветствия при первом запуске

    :param state:
    :param message:
    :return:
    """
    if config.is_admin(message.chat.id):
        keyboard = admin_keyboard
    else:
        keyboard = user_keyboard
    message_text = database.get_param("hello_message")

    admin_text = "📱 Новый пользователь\n" \
                 f"➖➖➖➖➖➖➖➖➖➖\n" \
                 f"🙍‍♂ Имя: @{message.chat.username}\n" \
                 f"🆔 ID: {message.chat.id}\n"

    await send_admins(admin_text)
    await message.answer(message_text.format(username=message.chat.username), reply_markup=keyboard)
    await state.finish()


# # # Покупки # # #

@dp.message_handler(regexp=const_ru["shop"])
async def shop_message(message: types.Message):
    """
    Вывод категорий для покупки товара

    :param message:
    :return:
    """
    keyboard = keyboards.create_category_keyboard("select_category")
    length = len(json.loads(keyboard.as_json())["inline_keyboard"])

    message_text = "📂 Все доступные категории"
    if length == 0:
        message_text = const_ru["nothing"]

    keyboard.add(keyboards.CLOSE_BTN)

    await message.answer(message_text, reply_markup=keyboard)


# # # О магазине # # #

@dp.message_handler(regexp=const_ru["faq"])
async def faq(message: types.Message):
    """
    FAQ магазина

    :param message:
    :return:
    """
    keyboard = types.InlineKeyboardMarkup()

    if is_admin(message.chat.id):
        keyboard.add(types.InlineKeyboardButton(text=const_ru["edit"], callback_data="edit_faq"))

    await message.answer(database.get_param("faq"), reply_markup=keyboard)


@dp.message_handler(regexp=const_ru["rules"])
async def rules(message: types.Message):
    """
    Правила магазина

    :param message:
    :return:
    """
    keyboard = types.InlineKeyboardMarkup()

    if is_admin(message.chat.id):
        keyboard.add(types.InlineKeyboardButton(text=const_ru["edit"], callback_data="edit_rules"))

    await message.answer(database.get_param("rules"), reply_markup=keyboard)


# # # Профиль # # #

@dp.message_handler(regexp=const_ru["profile"])
async def profile(message: types.Message):
    """
    Профиль пользователя

    :param message:
    :return:
    """
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(keyboards.CLOSE_BTN)

    sales_list = database.get_user_buy(message.chat.id)

    message_text = f"🙍‍♂ Пользователь: @{message.chat.username}\n" \
                   f"➖➖➖➖➖➖➖➖➖➖\n" \
                   f"🛒 Количество покупок: <b>{len(sales_list)} шт.</b>\n" \
                   f"💰 Общая сумма: <b>{sum(row[3] for row in sales_list)} руб.</b>\n" \
                   f"➖➖➖➖➖➖➖➖➖➖\n" \
                   f"📱 Последние 10 покупок:\n\n"

    sales_list = sales_list[::-1][:10]

    for sale in sales_list:
        message_text += f"▫ {sale[2]} ({sale[4]} шт.) | {sale[3]} руб.\n"

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(keyboards.CLOSE_BTN)
    await message.answer(message_text, reply_markup=keyboard)


# # # Поддержка # # #

@dp.message_handler(regexp=const_ru["support"])
async def support(message: types.Message):
    """
    Поддержка

    :param message:
    :return:
    """
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if config.is_admin(message.chat.id):
        # админ панель
        keyboard.row(const_ru["active_support"], const_ru["close_support"])
    else:
        # юзер панель
        keyboard.row(const_ru["new_support"], const_ru["my_support"])

    keyboard.row(const_ru["back"])
    await message.answer(const_ru["support"], reply_markup=keyboard)


@dp.message_handler(regexp=const_ru["new_support"])
async def new_support(message: types.Message):
    """
    Новое обращение

    :param message:
    :return:
    """
    await select_type(message)


@dp.message_handler(regexp=const_ru["my_support"])
async def my_support(message: types.Message):
    """
    Мои обращения

    :param message:
    :return:
    """
    keyboard = create_list_keyboard(data=database.get_user_supports(message.chat.id),
                                    last_index=0,
                                    page_click=f"get_user_supports={message.chat.id}",
                                    btn_text_param="user_support",
                                    btn_click="get_user_support")
    await message.answer(const_ru["my_support"], reply_markup=keyboard)
