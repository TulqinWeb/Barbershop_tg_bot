from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from send_user_buttons import send_men_regions, send_women_regions, send_men_barbers, send_women_barbers, \
    send_men_barber_details

from barbershop_db import DataBase
from send_user_buttons.send_women_details import send_women_barber_details

db = DataBase()


async def inline_handler(update, context):
    query = update.callback_query

    # regionlarni olib keladi.
    if query.data == 'barber_men':
        # Foydalanuvchi genderini aniqlab olish
        context.user_data['gender'] = 'M'

        print(context.user_data['gender'])
        regions = db.get_regions(gender='M')
        await send_men_regions(context=context, regions=regions,
                               chat_id=query.message.chat_id,
                               message_id=query.message.message_id)

    elif query.data == 'barber_women':
        context.user_data['gender'] = 'F'
        print(context.user_data['gender'])
        regions = db.get_regions(gender='F')
        await send_women_regions(context=context, regions=regions,
                                 chat_id=query.message.chat_id,
                                 message_id=query.message.message_id)

    elif query.data == 'main_back_M' or query.data == 'main_back_F':
        keyboard = [
            [InlineKeyboardButton(text="Erkaklar uchun 🧑", callback_data='barber_men')],
            [InlineKeyboardButton(text="Ayollar uchun  👩", callback_data='barber_women')],
            [InlineKeyboardButton(text="Close", callback_data='close')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.edit_message_text(chat_id=update.callback_query.from_user.id,
                                            message_id=update.callback_query.message.message_id,
                                            text="Tanlang",
                                            reply_markup=reply_markup)

    if query.data == 'close':
        # Xabarni "⏱" belgisi bilan tahrirlash
        await query.message.edit_text(
            text='⏱',
            reply_markup=None
        )

        # Tahrirlangan xabarni o'chirish
        await context.bot.delete_message(
            chat_id=update.callback_query.from_user.id,
            message_id=query.message.message_id
        )

    # regionlardagi sartaroshlarni olib keladi.
    data_sp = str(query.data).split('_')

    if data_sp[0] == 'region':
        region_id = data_sp[1]

        # Foydalanuvchi regionni tanlagan paytda region_id ni saqlash
        context.user_data['region_id'] = region_id
        # genderni ajratib olish
        data_sp[2] = context.user_data.get('gender')

        if data_sp[1].isdigit() and data_sp[2] == 'M':
            barbers = db.get_barbers(region_id=region_id, gender='M')
            await send_men_barbers(context=context, barbers=barbers,
                                   chat_id=query.message.chat_id,
                                   message_id=query.message.message_id)


        elif data_sp[1].isdigit() and data_sp[2] == 'F':
            barbers = db.get_barbers(region_id=region_id, gender='F')
            await send_women_barbers(context=context, barbers=barbers,
                                     chat_id=query.message.chat_id,
                                     message_id=query.message.message_id)

        elif data_sp[1] == 'back' and data_sp[2] == 'M' or data_sp[2] == 'F':
            gender = context.user_data.get('gender')
            if gender == 'M':
                regions = db.get_regions(gender='M')
                await send_men_regions(context=context, regions=regions,
                                       chat_id=query.message.chat_id,
                                       message_id=query.message.message_id)
            elif gender == 'F':
                regions = db.get_regions(gender='F')
                await send_men_regions(context=context, regions=regions,
                                       chat_id=query.message.chat_id,
                                       message_id=query.message.message_id)


    elif data_sp[0] == 'barber':
        # region_id = context.user_data.get('region_id')
        gender = context.user_data.get('gender')

        # Erkaklar uchun sartarosh ma'lumotlari
        if data_sp[1].isdigit() and data_sp[2] == 'M':
            barber_id = int(data_sp[1])

            # Sartarosh haqida ma'lumotlar
            barber = db.get_barber_details(barber_id=barber_id, gender=gender)

            # Rasmlar URL-larini olish
            barber_photos = db.get_barber_photos(barber_id=barber_id)

            location = db.get_location(barber_id=barber_id)

            # Foydalanuvchiga yuborish
            message_ids = await send_men_barber_details(
                context=context,
                barber=barber,
                barber_photos=barber_photos,
                location=location,
                chat_id=query.message.chat_id
            )

            # Foydalanuvchi uchun yuborilgan xabarlar IDlarini saqlash
            context.user_data['barber_message_ids'] = message_ids

        # "Orqaga" tugmasi uchun (erkaklar)
        elif data_sp[1] == 'back' and data_sp[2] == 'M':
            # Saqlangan xabarlarni o'chirish
            message_ids = context.user_data.get('barber_message_ids', [])
            for msg_id in message_ids:
                try:
                    await context.bot.delete_message(
                        chat_id=query.message.chat_id,
                        message_id=msg_id
                    )
                except Exception as e:
                    print(f"Xabarni o'chirishda xato: {e}")

            # Kontekstni tozalash
            context.user_data['barber_message_ids'] = []

        # Ayollar uchun sartarosh ma'lumotlari
        if data_sp[1].isdigit() and data_sp[2] == 'F':
            barber_id = int(data_sp[1])

            # Sartarosh haqida ma'lumotlar
            barber = db.get_barber_details(barber_id=barber_id, gender=gender)

            # Rasmlar URL-larini olish
            barber_photos = db.get_barber_photos(barber_id=barber_id)

            location = db.get_location(barber_id=barber_id)

            # Foydalanuvchiga yuborish
            message_ids = await send_women_barber_details(
                context=context,
                barber=barber,
                barber_photos=barber_photos,
                location=location,
                chat_id=query.message.chat_id
            )

            # Foydalanuvchi uchun yuborilgan xabarlar IDlarini saqlash
            context.user_data['barber_message_ids'] = message_ids

        # "Orqaga" tugmasi uchun (ayollar)
        elif data_sp[1] == 'back' and data_sp[2] == 'F':
            # Saqlangan xabarlarni o'chirish
            message_ids = context.user_data.get('barber_message_ids', [])
            for msg_id in message_ids:
                try:
                    await context.bot.delete_message(
                        chat_id=query.message.chat_id,
                        message_id=msg_id
                    )
                except Exception as e:
                    print(f"Xabarni o'chirishda xato: {e}")

            # Kontekstni tozalash
            context.user_data['barber_message_ids'] = []