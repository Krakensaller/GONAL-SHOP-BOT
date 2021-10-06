import time

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Regexp
from aiogram.dispatcher.filters.state import StatesGroup, State

import database
from loader import bot, dp
from src import config
from src.const import is_const


class MailingCreator(StatesGroup):
    mailing_format = State()
    mailing_text = State()
    mailing_send = State()


async def select_format(message: types.Message):
    """
    Выбор форматирования текста

    :param message:
    :return:
    """
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton(text="Markdown", callback_data="format=markdown"),
        types.InlineKeyboardButton(text="HTML", callback_data="format=html")
    )
    await message.answer("Выберите необходимый способ форматирования для рассылки\n\n"
                         "🔹 Для пересылаемых сообщений лучше всего выбирать HTML\n"
                         "🔹 В случае использования Markdown, ники могут отображаться некорректно\n",
                         reply_markup=keyboard)

    await MailingCreator.mailing_format.set()


@dp.callback_query_handler(Regexp("format"), state=MailingCreator.mailing_format)
async def input_mailing(call: types.CallbackQuery):
    """
    Запрос текста рассылки

    :param call:
    :return:
    """
    await call.message.delete()
    call_data = call.data.split("=")

    state = Dispatcher.get_current().current_state()
    await state.update_data(format=call_data[1])

    await call.message.answer(f"✏️ Введите текст вашей рассылки в формате <i>{call_data[1].upper()}</i>\n"
                              "<b>Или прикрепите фото, и укажите текст в описании к картинке</b>")

    await MailingCreator.next()


@dp.message_handler(state=MailingCreator.mailing_text, content_types=['text', 'photo'])
async def get_mailing_text(message: types.Message, state: FSMContext):
    """
    Получение текста для рассылки

    :param message:
    :param state:
    :return:
    """
    mailing_text = message.text

    mailing_photo = ""

    if len(message.photo) > 0:
        # рассылка с фотографией
        src = "mailings"
        config.create_folder(src)

        mailing_photo = f"{src}/{message.photo[-1].file_id}"
        await message.photo[-1].download(mailing_photo)
        mailing_text = message.caption

    await state.update_data(mailing_text=mailing_text)
    await state.update_data(mailing_photo=mailing_photo)

    await MailingCreator.next()
    await send_mailing(message, state)


@dp.message_handler(state=MailingCreator.mailing_send)
async def send_mailing(message: types.Message, state: FSMContext):
    """
    Отправка рассылки

    :param message:
    :param state:
    :return:
    """
    user_list = database.get_all_users()

    mailing_data = await state.get_data()

    mailing_text = mailing_data['mailing_text']
    if is_const(mailing_text):
        await message.answer("❗️ Некорректный текст рассылки ❗️")
        return

    mailing_photo = mailing_data['mailing_photo']
    parse_mode = mailing_data['format'].upper()
    await state.finish()

    success = 0
    bad = 0
    await message.answer("✅ Рассылка началась")

    if mailing_photo != "":
        # рассылка с фото
        for i in range(len(user_list)):
            try:
                await bot.send_photo(user_list[i][0],
                                     photo=open(mailing_photo, "rb"),
                                     caption=mailing_text,
                                     parse_mode=parse_mode)
                success += 1
            except:
                bad += 1

            if i % 20 == 0:
                time.sleep(1)
    else:
        # рассылка без текста
        for i in range(len(user_list)):
            try:
                await bot.send_message(user_list[i][0],
                                       mailing_text,
                                       parse_mode=parse_mode)
                success += 1
            except:
                bad += 1

            if i % 20 == 0:
                time.sleep(1)

    await message.answer("✅ Рассылка завершена\n"
                         f"Всего отправлено: <b>{len(user_list)} шт.</b>\n\n"
                         f"✅ Успешно: <b>{success} шт.</b>\n"
                         f"❌ Не отправлено: <b>{bad} шт.</b>")
