import json

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Regexp
from aiogram.dispatcher.filters.state import StatesGroup, State

import database
from loader import dp, bot
from source.admins import send_admins
from source.payments.qiwi.qiwi_params import check_db_qiwi, create_qiwi_link, check_qiwi_payment
from source.payments.yoo_money.yoo_money_params import check_db_yoomoney, create_yoomoney_link, check_yoomoney_payment
from src.const import const_ru
from src.strings import create_comment, get_now_date, get_buy_message


class PurchaseCreator(StatesGroup):
    user_count = State()
    item_count = State()
    payment_type = State()
    create_purchase = State()

    check_purchase = State()


async def select_count(message: types.Message, item_id):
    """
    Клавиатура для выбора количества товаров

    :param message:
    :param item_id: id выброанного товара
    :return:
    """
    await PurchaseCreator.item_count.set()

    item_count = database.get_item_count(item_id)

    state = Dispatcher.get_current().current_state()
    await state.update_data(item_id=item_id)

    keyboard = types.InlineKeyboardMarkup(row_width=5)

    i = 1
    btn_list = []
    while i <= 15 and i <= item_count:
        btn_list.append(types.InlineKeyboardButton(text=f"{str(i)} шт.",
                                                   callback_data=f"select_count={str(i)}"))
        i += 1

    await state.update_data(max_count=i)

    keyboard.add(*btn_list)
    keyboard.add(types.InlineKeyboardButton(text="🛒 Своё значение", callback_data="user_count"))
    keyboard.add(types.InlineKeyboardButton(text=const_ru['cancel_buy'], callback_data="cancel_buy"))

    await message.answer("🛒 Введите необходимое количество товара", reply_markup=keyboard)


@dp.callback_query_handler(Regexp("select_count"), state=PurchaseCreator.item_count)
async def get_count_keyboard(call: types.CallbackQuery):
    """
    Количество товара из клавиатуры

    :param call:
    :return:
    """
    await call.message.delete()

    call_data = call.data.split("=")
    state = Dispatcher.get_current().current_state()
    await state.update_data(count=int(call_data[1]))

    await select_payment(call.message, state)


@dp.callback_query_handler(Regexp("user_count"), state=PurchaseCreator.item_count)
async def input_count(call: types.CallbackQuery):
    """
    Выбор количества товара для покупки

    :param call:
    :return:
    """
    await call.message.delete()
    state = Dispatcher.get_current().current_state()
    data = await state.get_data()
    item_id = data['item_id']

    item_count = database.get_item_count(item_id)
    max_count = 15
    if item_count < max_count:
        max_count = item_count

    await call.message.answer("🛒 Введите количество необходимого товара:\n\n"
                              "Минимальное значение: <i>1 шт.</i>\n"
                              f"Максимальное: <i>{max_count} шт.</i>")

    await state.update_data(max_count=int(max_count))


@dp.message_handler(state=PurchaseCreator.item_count)
async def check_count(message: types.Message, state: FSMContext):
    """
    Проверка количества товара

    :param message:
    :param state:
    :return:
    """
    data = await state.get_data()

    max_count = data['max_count']
    count = message.text

    if count.isdigit() and int(count) <= max_count:
        count = int(count)
    else:
        await message.answer("❗️ Некорректное значение количества ❗️")
        return

    await state.update_data(count=count)
    await select_payment(message, state)


async def select_payment(message: types.Message, state: FSMContext):
    """
    Выбор способа оплаты

    :param message:
    :param state:
    :return:
    """
    keyboard = types.InlineKeyboardMarkup()
    if check_db_qiwi():
        keyboard.add(types.InlineKeyboardButton(text=const_ru["qiwi"],
                                                callback_data="payment=qiwi"))

    if check_db_yoomoney():
        keyboard.add(types.InlineKeyboardButton(text=const_ru["yoomoney"],
                                                callback_data="payment=yoomoney"))

    length = len(json.loads(keyboard.as_json())["inline_keyboard"])

    if length > 0:
        keyboard.add(types.InlineKeyboardButton(text=const_ru['cancel_buy'], callback_data="cancel_buy"))
        await message.answer("💳 Выберите удобный способ оплаты", reply_markup=keyboard)

        await PurchaseCreator.next()
    else:
        await message.answer("😔 К сожалению, оплата в данный момент не работает")
        await state.finish()


@dp.callback_query_handler(Regexp("payment"), state=PurchaseCreator.payment_type)
async def check_payment_type(call: types.CallbackQuery):
    """
    Сохранение выбранного способа оплаты и переход к покупке

    :param call:
    :return:
    """
    await call.message.delete()

    call_data = call.data.split("=")

    state = Dispatcher.get_current().current_state()
    await state.update_data(payment_type=call_data[1])

    await PurchaseCreator.next()
    await create_purchase(call.message, state)


@dp.message_handler(state=PurchaseCreator.create_purchase)
async def create_purchase(message: types.Message, state: FSMContext):
    """
    Обработка покупки

    :param message:
    :param state:
    :return:
    """
    data = await state.get_data()
    item_data = database.get_item(data['item_id'])

    # создание ссылки на оплату
    payment_type = data['payment_type']
    comment = create_comment()
    amount = item_data[4] * int(data['count'])

    payment_form = dict()

    warning_payment = ""
    if payment_type == "qiwi":
        payment_form = create_qiwi_link(amount, comment)
        warning_payment = "❗️ При оплате через никнейм <b>указывайте комментарий самостоятельно</b>, " \
                          "иначе вы не получите покупку\n" \
                          "При оплате через номер телефона ничего указывать <b>не нужно</b>. Всё сделано " \
                          "автоматически ❗️\n"
    elif payment_type == "yoomoney":
        payment_form = create_yoomoney_link(amount, comment)
        warning_payment = "❗️ Для оплаты <b>необходимо перейти по ссылке, где все данные указаны автоматически</b>️\n" \
                          "Вам необходимо только нажать <b>Оплатить</b> ❗️\n"

    message_text = f"🛒 Покупка товара <b>{item_data[1]}</b>\n" \
                   f"📦 Количество: <i>{data['count']} шт.</i>\n\n" \
                   f"Для оплаты нажмите <b>{const_ru['buy_item']}</b>\n" \
                   f"Поля менять <b>не нужно</b>\n" \
                   f"{warning_payment}\n" \
                   f"После оплаты нажмите <b>{const_ru['check_buy']}</b>\n\n" \
                   f"➖➖➖➖➖➖➖➖➖➖\n" \
                   f"💳 Способ оплаты: <b>{payment_form['name']}</b>\n" \
                   f"📱 {payment_form['key']}: <b>{payment_form['value']}</b>\n" \
                   f"📋 Комментарий: <b>{comment}</b>\n" \
                   f"💵 Сумма покупки: <b>{amount} руб.</b>\n" \
                   f"➖➖➖➖➖➖➖➖➖➖"

    keyboard = types.InlineKeyboardMarkup()

    keyboard.row(types.InlineKeyboardButton(text=const_ru['buy_item'], url=payment_form['link']),
                 types.InlineKeyboardButton(text=const_ru['check_buy'], callback_data="check_buy"))
    keyboard.row(types.InlineKeyboardButton(text=const_ru['cancel_buy'], callback_data="cancel_buy"))

    await message.answer(message_text, reply_markup=keyboard)

    await state.finish()
    await PurchaseCreator.check_purchase.set()
    state = Dispatcher.get_current().current_state()

    await state.update_data(item_id=data['item_id'])
    await state.update_data(amount=amount)
    await state.update_data(count=data['count'])
    await state.update_data(comment=comment)
    await state.update_data(payment_type=payment_type)


@dp.callback_query_handler(Regexp("check_buy"), state=PurchaseCreator.check_purchase)
async def check_purchase(call: types.CallbackQuery):
    """
    Проверка покупки

    :param call:
    :return:
    """
    state = Dispatcher.get_current().current_state()
    data = await state.get_data()

    item_id = data['item_id']
    amount = data['amount']
    count = data['count']
    comment = data['comment']
    payment_type = data['payment_type']

    has_payment = False

    if payment_type == "qiwi":
        has_payment = check_qiwi_payment(amount, comment)
    elif payment_type == "yoomoney":
        has_payment = check_yoomoney_payment(amount, comment)

    item_info = database.get_item(item_id)

    if has_payment:
        # оплата прошла успешно
        await call.message.delete()

        items_data = database.get_item_data(item_id, count, True)

        # вся инфа о покупке
        purchase_data = dict()
        purchase_data['user_id'] = call.message.chat.id
        purchase_data['item_name'] = item_info[1]
        purchase_data['amount'] = amount
        purchase_data['count'] = count
        purchase_data['date'] = get_now_date()
        purchase_data['payment_type'] = const_ru[payment_type]

        # запись покупки в БД и получение ID
        sale_id = database.add_buy(purchase_data)
        database.add_sold_item_data(sale_id, items_data)
        purchase_data['sale_id'] = sale_id

        user_text = get_buy_message(call.message, purchase_data, True)
        admin_text = get_buy_message(call.message, purchase_data, False)

        item_files = []
        for i in range(len(items_data)):
            item_data = items_data[i][2].split("=", 2)
            admin_text += f"<b>{item_data[1]}\n</b>"

            if item_data[0] == "text":
                # текстовый товар
                user_text += f"<b>{item_data[1]}\n</b>"
            elif item_data[0] == "file":
                # файловый товар
                item_files.append(item_data[1])

        await call.message.answer(user_text)
        for i in range(len(item_files)):
            # отправка файловых товаров
            await call.message.answer_document(open(item_files[i], "rb"))

        await send_admins(admin_text)
        await state.finish()
    else:
        # ошибка при оплате
        await bot.answer_callback_query(callback_query_id=call.id, show_alert=True,
                                        text="❗️ Пополнение не найдено ❗️\n Попробуйте еще раз")


@dp.callback_query_handler(state=PurchaseCreator.item_count)
@dp.callback_query_handler(state=PurchaseCreator.check_purchase)
@dp.callback_query_handler(state=PurchaseCreator.payment_type)
@dp.callback_query_handler(Regexp("cancel_buy"))
async def cancel_buy(call: types.CallbackQuery):
    """
    Отмена покупки

    :param call:
    :return:
    """
    await call.message.delete()
    await call.message.answer("❗️ Покупка отменена ❗️")

    state = Dispatcher.get_current().current_state()
    await state.finish()
