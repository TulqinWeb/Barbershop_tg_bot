from telegram import InlineKeyboardMarkup, InlineKeyboardButton


async def send_men_barber_details(context, barber, chat_id, message_id=None):
    button = [[InlineKeyboardButton(text='Orqaga', callback_data='barber_back_F')]]

    barbermen_details = (
        f"<b>Sartarosh haqida ma'lumot:</b>\n"
        f"<b>Ismi:</b> {barber['name']}\n"
        f"<b>Telefon raqami:</b> +{barber['phone']}\n"
        f"<b>Telegram link:</b> {barber['telegram_link']}\n"
        f"<b>Ma'lumot:</b> {barber['bio']}\n"
    )

    reply_markup = InlineKeyboardMarkup(inline_keyboard=button)

    if message_id:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=barbermen_details,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=barbermen_details,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

