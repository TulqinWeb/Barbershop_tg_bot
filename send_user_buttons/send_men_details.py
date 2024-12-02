from telegram import InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup


async def send_men_barber_details(context, barber, barber_photos, location, chat_id):
    # Inline tugmalar
    buttons = [[InlineKeyboardButton(text='Orqaga', callback_data='barber_back_M')]]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    # Manzil uchun default qiymat
    maps_url = "Manzil mavjud emas"

    # Location borligini tekshirish va URL yaratish
    if location:
        latitude = float(location.get('latitude', 0))
        longitude = float(location.get('longitude', 0))

        # Latitude va Longitude ni tekshirish
        if -90 <= latitude <= 90 and -180 <= longitude <= 180:
            maps_url = f"https://www.google.com/maps?q={latitude},{longitude}"

    # Sartarosh haqidagi ma'lumotlar
    barber_details = (
        f"<b>Sartarosh haqida ma'lumot:</b>\n"
        f"<b>Ismi:</b> {barber['name']}\n"
        f"<b>Telefon raqami:</b> +{barber['phone']}\n"
        f"<b>Telegram link:</b> {barber['telegram_link']}\n"
        f"<b>Ma'lumot:</b> {barber['bio']}\n"
        f"<b>Manzil:</b> <a href='{maps_url}'>Google Maps'da ochish</a>"
    )

    # Rasmlarni yuborish
    message_ids = []
    if barber_photos:
        media_group = [InputMediaPhoto(media=photo['photo_url']) for photo in barber_photos]
        messages = await context.bot.send_media_group(chat_id=chat_id, media=media_group)
        message_ids.extend([msg.message_id for msg in messages])

    # Ma'lumot va tugmani yuborish
    message = await context.bot.send_message(
        chat_id=chat_id,
        text=barber_details,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    message_ids.append(message.message_id)

    return message_ids
