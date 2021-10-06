from aiogram import types
from aiogram.dispatcher.filters import IDFilter, Regexp

import database
from handlers.message.admin_message import category_management, qiwi_edit, item_management
from loader import dp
from source import category
from source.items import item_creator
from source.items.item_editor import edit_item_menu
from source.params import input_param_value
from source.payments.qiwi import qiwi_params
from source.payments.qiwi.qiwi import qiwi_num
from source.payments.yoo_money import yoo_money_params
from source.payments.yoo_money.yoo_money import client_id
from source.support.support_admin import get_answer
from src import keyboards
from src.config import ADMIN_ID
from src.const import const_ru
# # # Категории # # #
from src.keyboards import create_list_keyboard


@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("get_category_management"))
async def get_category_management(call: types.CallbackQuery):
    """
    Вывод всех категорий для редактирования

    :param call:
    :return:
    """
    await call.message.delete()
    await category_management(call.message)


@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("add_category"))
async def add_category(call: types.CallbackQuery):
    """
    Добавление категории

    :param call:
    :return:
    """
    await call.message.delete()
    await category.add_name(call.message, -1)


@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("add_subcategory"))
async def add_subcategory(call: types.CallbackQuery):
    """
    Добавление подкатегории в категорию

    :param call:
    :return:
    """
    data = call.data.split("=")

    await call.message.delete()
    await category.add_name(call.message, data[1])


@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("edit_category"))
async def edit_category(call: types.CallbackQuery):
    """
    Управление категорией

    :param call:
    :return:
    """
    await call.message.delete()

    data = call.data.split("=")
    category_info = database.get_category(data[1])
    subcategories = database.get_subcategories(data[1])

    message_text = f"📁 Категория: <b>{category_info[1]}</b>\n" \
                   f"Доступные подкатегории:\n"

    for i in range(len(subcategories)):
        message_text += f"▫ {subcategories[i][1]}\n"

    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(types.InlineKeyboardButton(text=const_ru["add_subcategory"],
                                            callback_data=f"add_subcategory={data[1]}"),
                 types.InlineKeyboardButton(text=const_ru["delete_subcategory"],
                                            callback_data=f"delete_subсat_select={data[1]}"))

    keyboard.row(types.InlineKeyboardButton(text=const_ru["delete_category"],
                                            callback_data=f"delete_category={data[1]}"))

    keyboard.row(types.InlineKeyboardButton(text=const_ru["back"],
                                            callback_data=f"get_category_management"),
                 keyboards.CLOSE_BTN)

    message_text += "\n❗ При удалении категории/подкатегории, " \
                    "удаляются <b>все товары/категории находящиеся в ней</b>"
    await call.message.answer(message_text, reply_markup=keyboard)


@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("delete_category"))
async def delete_category(call: types.CallbackQuery):
    """
    Удаление категории

    :param call:
    :return:
    """
    await call.message.delete()
    data = call.data.split("=")
    database.delete_category(data[1])
    await call.message.answer("✅ Категория удалена")


@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("delete_subсat_select"))
async def delete_subcategory_select(call: types.CallbackQuery):
    """
    Выбор подкатегории для удаления

    :param call:
    :return:
    """
    await call.message.delete()
    data = call.data.split("=")

    keyboard = keyboards.create_subcategory_keyboard(data[1], "delete_subcategory")

    await call.message.answer("📁 Выберите подкатегорию", reply_markup=keyboard)


@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID),
                           lambda call: call.data.startswith("delete_subcategory"))
async def delete_subcategory(call: types.CallbackQuery):
    """
    Удаление подкатегории

    :param call:
    :return:
    """
    await call.message.delete()
    data = call.data.split("=")
    database.delete_subcategory(data[1])
    await call.message.answer("✅ Податегория удалена")


# # # Товары # # #

@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("get_item_management"))
async def get_item_management(call: types.CallbackQuery):
    """
    Вернуться ко всем категориям в меню редактирования товаров

    :param call:
    :return:
    """
    await call.message.delete()
    await item_management(call.message)


@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("get_item_category"))
async def get_item_category(call: types.CallbackQuery):
    """
    Все доступные товары и подкатегории в категории

    :param call:
    :return:
    """
    await call.message.delete()

    data = call.data.split("=")
    keyboard = keyboards.create_category_items_keyboard(data[1], "get_item_subcategory", "get_item")
    keyboard.add(types.InlineKeyboardButton(text=const_ru["add_item"],
                                            callback_data=f"add_item={data[1]}|0"))
    keyboard.add(types.InlineKeyboardButton(text=const_ru["back"], callback_data="get_item_management"))
    keyboard.add(keyboards.CLOSE_BTN)

    await call.message.answer("📦 Доступные товары и подкатегории\n\n"
                              "📝 Для редактирования товара <i>нажмите на него</i>",
                              reply_markup=keyboard)


@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("get_item_subcategory"))
async def get_item_subcategory(call: types.CallbackQuery):
    """
    Все доступные товары в подкатегории

    :param call:
    :return:
    """
    await call.message.delete()

    data = call.data.split("=")

    categories = data[1].split("|")

    keyboard = keyboards.create_subcategory_items_keyboard(categories[0], categories[1], "get_item")
    keyboard.add(types.InlineKeyboardButton(text=const_ru["add_item"],
                                            callback_data=f"add_item={categories[0]}|{categories[1]}"))
    keyboard.row(types.InlineKeyboardButton(text=const_ru["back"],
                                            callback_data=f"get_item_category={categories[1]}"),
                 types.InlineKeyboardButton(text=const_ru["to_all_category"],
                                            callback_data="get_item_management"))
    keyboard.add(keyboards.CLOSE_BTN)

    await call.message.answer("📦 Доступные товары\n\n"
                              "📝 Для редактирования товара <i>нажмите на него</i>",
                              reply_markup=keyboard)


@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("get_item"))
async def get_item(call: types.CallbackQuery):
    """
    Выбор товара для редактирования

    :param call:
    :return:
    """
    await call.message.delete()
    item_id = call.data.split("=")[1]
    await edit_item_menu(call.message, item_id)


@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("add_item"))
async def add_item(call: types.CallbackQuery):
    """
    Добавление товара

    :param call:
    :return:
    """
    await call.message.delete()

    data = call.data.split("=")
    await item_creator.add_name(call.message, data[1])


# # # Кошельки # # #

@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("change_qiwi"))
async def change_qiwi(call: types.CallbackQuery):
    """
    Изменение способа оплаты QIWI

    :param call:
    :return:
    """
    await call.message.delete()
    call_data = call.data.split("=")
    database.set_param("qiwi_payment", call_data[1])
    await call.message.answer("✅ Способ оплаты изменен")
    await qiwi_edit(call.message)


@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("edit_qiwi"))
async def edit_qiwi(call: types.CallbackQuery):
    """
    Изменение QIWI

    :param call:
    :return:
    """
    await call.message.delete()
    await qiwi_num(call.message)


@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("check_qiwi"))
async def check_qiwi(call: types.CallbackQuery):
    """
    Проверка QIWI

    :param call:
    :return:
    """
    await call.message.delete()
    qiwi_data = database.get_qiwi()

    if qiwi_params.check_qiwi(qiwi_data[1], qiwi_data[2]):
        await call.message.answer("✅ Кошелёк активен")
    else:
        await call.message.answer("❗️ Кошелек не доступен ❗️")


@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("edit_yoomoney"))
async def edit_yoomoney(call: types.CallbackQuery):
    """
    Изменение YooMoney

    :param call:
    :return:
    """
    await call.message.delete()
    await client_id(call.message)


@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("check_yoomoney"))
async def check_yoomoney(call: types.CallbackQuery):
    """
    Проверка YooMoney

    :param call:
    :return:
    """
    await call.message.delete()
    yoomoney_data = database.get_yoomoney()

    if yoo_money_params.check_yoomoney(yoomoney_data[2]):
        await call.message.answer("✅ Кошелёк активен")
    else:
        await call.message.answer("❗️ Кошелек не доступен ❗️")


# # # Прочее # # #

@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("edit_hello"))
async def edit_hello(call: types.CallbackQuery):
    """
    Редактирование приветствия

    :param call:
    :return:
    """
    await call.message.delete()
    await input_param_value(call.message, "hello_message")


@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("edit_comeback"))
async def edit_hello(call: types.CallbackQuery):
    """
    Редактирование приветствия

    :param call:
    :return:
    """
    await call.message.delete()
    await input_param_value(call.message, "comeback_message")


@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("edit_faq"))
async def edit_faq(call: types.CallbackQuery):
    """
    Редактирование FAQ

    :param call:
    :return:
    """
    await call.message.delete()
    await input_param_value(call.message, "faq")


@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("edit_rules"))
async def edit_rules(call: types.CallbackQuery):
    """
    Редактирование правил

    :param call:
    :return:
    """
    await call.message.delete()
    await input_param_value(call.message, "rules")


# # # Обращения # # #

@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("get_user_support"))
async def get_supports(call: types.CallbackQuery):
    """
    Получение запросов

    :param call:
    :return:
    """
    await call.message.delete()
    call_data = call.data.split("=")
    data = call_data[1].split("|")
    # keyboard = get_supports_keyboard(data[0], data[1])
    keyboard = create_list_keyboard(data=database.get_supports(data[0]),
                                    last_index=int(data[1]),
                                    page_click=f"get_supports={data[0]}",
                                    btn_text_param="support",
                                    btn_click="get_support")

    if data[0] == "0":
        message_text = const_ru["active_support"]
    else:
        message_text = const_ru["close_support"]

    await call.message.answer(message_text, reply_markup=keyboard)


@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("get_support"))
async def get_support(call: types.CallbackQuery):
    """
    Обращение от пользователя

    :param call:
    :return:
    """
    await call.message.delete()
    call_data = call.data.split("=")

    support_data = database.get_support(call_data[1])
    keyboard = types.InlineKeyboardMarkup()

    delete_btn = types.InlineKeyboardButton(text=const_ru["delete"],
                                            callback_data=f"delete_support={call_data[1]}")
    if int(support_data[5]) == 0:
        support_state = "✅ Активно"
        keyboard.row(types.InlineKeyboardButton(text="✏️ Ответить",
                                                callback_data=f"answer_support={call_data[1]}"),
                     delete_btn)
    else:
        support_state = "❌ Закрыто\n" \
                        "➖➖➖➖➖➖➖➖➖➖\n" \
                        f"📧 Ответ:\n\n" \
                        f"{support_data[6]}"

        keyboard.add(delete_btn)

    message_text = f"🆔 Номер запроса: <b>{call_data[1]}</b>\n" \
                   f"🙍‍♂ Пользователь: <b>@{support_data[2]}</b>\n" \
                   "➖➖➖➖➖➖➖➖➖➖\n" \
                   f"📗 Тема запроса: <b>{database.get_support_type(support_data[4])[1]}</b>\n" \
                   f"📋 Описание:\n{support_data[3]}\n" \
                   "➖➖➖➖➖➖➖➖➖➖\n" \
                   f"📱 Состояние: {support_state}"

    keyboard.add(keyboards.CLOSE_BTN)
    await call.message.answer(message_text, reply_markup=keyboard)


@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("answer_support"))
async def answer_support(call: types.CallbackQuery):
    """
    Ответ на запрос

    :param call:
    :return:
    """
    await call.message.delete()
    call_data = call.data.split("=")
    await get_answer(call.message, call_data[1])


@dp.callback_query_handler(IDFilter(chat_id=ADMIN_ID), Regexp("delete_support"))
async def delete_support(call: types.CallbackQuery):
    """
    Удаление обращения

    :param call:
    :return:
    """
    await call.message.delete()
    call_data = call.data.split("=")
    database.delete_support(call_data[1])
    await call.message.answer("✅ Обращение удалено")
