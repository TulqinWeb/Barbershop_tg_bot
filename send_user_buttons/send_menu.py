from telegram import KeyboardButton, ReplyKeyboardMarkup


async def send_main_menu(context, chat_id):
    buttons = [
        [KeyboardButton(text="Foydalanuvchi")],
        [KeyboardButton(text="Xizmat ko'rsatish uchun ro'yxatdan o'tish")]
    ]
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)
    await context.bot.send_message(
        chat_id=chat_id,
        text=f'<b> Menulardan birini tanlang:</b>',
        parse_mode="HTML",
        reply_markup=reply_markup
    )
