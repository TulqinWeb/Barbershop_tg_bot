import re
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
import logging

from barbershop_db import DataBase
from config import ADMIN_ID
from send_user_buttons import send_main_menu

db = DataBase()

from get_all_regions import get_all_regions


async def start_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    reply_text = "<b>Foydalanuvchilar sizga aloqaga chiqishi uchun telefon raqamingizni yuboring. Telefon raqamingizni yuborish uchun kontakt ulashish tugmasini bosing!.</b>"
    reply_markup = ReplyKeyboardMarkup(
        [[KeyboardButton(text="Kontakt ulashish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await context.bot.send_message(
        chat_id=user.id,
        text=reply_text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    logging.info(f"{user.first_name} has started registering")
    return "PHONE_NUMBER"


async def phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Telefon raqami kiritilganini tekshiramiz
    if update.message.contact:  # Agar kontakt yuborilgan bo'lsa
        phone_number = update.message.contact.phone_number
        print(phone_number)
        context.user_data['phone_number'] = phone_number
        logging.info(f"Telefon raqami: +{phone_number}")
        await update.message.reply_text("<b>Ismingizni kiriting:</b>", parse_mode="HTML")
        return "NAME"  # Keyingi bosqichga o'tish
    else:
        logging.info(f"Telefon raqami yuborilmadi!")
        await update.message.reply_text("Iltimos, telefon raqamingizni yuboring.")
        print("Bo'sh")
        return "PHONE_NUMBER"  # Telefon raqam yuborilguncha bu yerda qoladi


async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    context.user_data["name"] = name
    logging.info(f"Ismi: {name}")
    await update.message.reply_text(
        text="<b>Foydalanuvchilar sizga aloqaga chiqishi uchun telegram profilingiz havolasini yuboring:</b>\n"
             "<b>Masalan:</b> https://t.me/abcdfusername <b>yoki</b> @aadadusername",
        parse_mode="HTML"
    )
    return "TELEGRAM_LINK"


async def verify_telegram_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text.strip()
    # Havola yoki username formatini tekshirish
    if re.match(r"^https://t\.me/\w{5,}$", link) or re.match(r"^@\w{5,}$", link):
        # Havolani umumiy formatga aylantirish (agar username ko‘rinishida bo‘lsa)
        if link.startswith('@'):
            link = f"https://t.me/{link[1:]}"
        context.user_data["telegram_link"] = link
        logging.info(f"Telegram link:{link}")
        await update.message.reply_text(
            text=f"<b>Havolangiz qabul qilindi:</b> {link}\n<b>Rahmat</b>",
            parse_mode="HTML"
        )
        await update.message.reply_text(
            text="""<b>O'zingiz haqingizda ma'lumotlar kiriting.Ushbu ma'lumotlar ko'proq foydalanuvchi sizga qiziqish bildirishi uchun muhim bo'lishi mumkin.</b>""",
            parse_mode="HTML"
        )
        return "BIO"

    else:
        await update.message.reply_text(
            text="<b>Noto'g'ri format. Iltimos, havolani yoki username'ni to‘g‘ri shaklda yuboring.</b>",
            parse_mode="HTML"
        )
        return "TELEGRAM_LINK"


async def bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bio = update.message.text
    context.user_data["bio"] = bio
    keyboard = [
        [KeyboardButton(text="Erkaklar uchun 🧑")],
        [KeyboardButton(text="Ayollar uchun 👩")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    logging.info(f"BIO : {bio}")
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text="<b>Kimlar uchun o'z xizmatingizni taklif etasiz?</b> \n"
             "<b>Tugmalardan birini tanlang</b>",
        parse_mode="HTML",
        reply_markup=reply_markup
    )
    return "GENDER"


async def gender_selection(update, context):
    gender = update.message.text

    if gender == "Erkaklar uchun 🧑":
        context.user_data['gender'] = "M"
        regions = db.get_all_regions()
        logging.info(f"Xzimat turi:{gender}")
        await get_all_regions(context=context, regions=regions,
                              chat_id=update.message.from_user.id)

    elif gender == "Ayollar uchun 👩":
        context.user_data['gender'] = "F"
        regions = db.get_all_regions()
        logging.info(f"Xzimat turi:{gender}")
        await get_all_regions(context=context, regions=regions,
                              chat_id=update.message.from_user.id)

    return "REGION_SELECTION"


async def region_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    # Callback_data dan region_id ni olish
    data = query.data  # Masalan: "region_1"
    region_id = int(data.split('_')[2])

    # Region nomini olish (databazadan qidirib topish yoki inline tugma yaratishda saqlash)
    region_name = next(region['region_name'] for region in db.get_all_regions() if region['region_id'] == region_id)

    # Ma'lumotlarni saqlash
    context.user_data["region_id"] = region_id
    context.user_data["region_name"] = region_name
    logging.info(f"Tuman: {region_name}")
    # Xabarni yangilash
    await query.edit_message_text(
        text=f" <b>{region_name}</b> tumani tanladi.",
        parse_mode="HTML"
    )

    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text="<b> O'zingizning ishlaringizdan namunalar (rasmlar) yuboring! </b> ",
                                   parse_mode="HTML"
                                   )
    return "PHOTO"


async def handle_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Foydalanuvchidan kelgan rasmlar
    photos = context.user_data.get('photos', [])

    if update.message.photo:
        # Yuborilgan har bir rasmni tekshirish
        new_photos = []  # Yangi rasmlar ro'yxati
        # Telegramda rasmlar o'lchami sifatida photo[-1] eng katta versiya bo'ladi
        photo_file_id = update.message.photo[-1].file_id  # Eng katta o'lchamni olish

        # Agar rasm oldin yuborilmagan bo'lsa, uni saqlaymiz
        if photo_file_id not in photos:
            new_photos.append(photo_file_id)  # Yangi rasmni qo'shish
        else:
            # Bu rasm allaqachon yuborilgan, shuning uchun foydalanuvchiga xabar yuboriladi
            await update.message.reply_text(
                "Bu rasm allaqachon yuborilgan. Yana rasmlar yuborishingiz mumkin yoki keyingi bosqichga o'tish uchun /next buyrug'ini kiriting."
            )

        # Yangi rasmlar ro'yxatini to'liq ro'yxatga qo'shish
        photos.extend(new_photos)  # Yangi rasmlarni saqlash

        # Yangilangan ro'yxatni context'ga saqlaymiz
        context.user_data['photos'] = photos

        # Faqat yangi rasmlar yuborilgandan keyin umumiy xabar yuboriladi
        if new_photos:  # Yangi rasmlar qo'shilgan bo'lsa
            await update.message.reply_text(
               text= f"<b>Jami {len(photos)} ta rasm qabul qilindi.</b>\n"
                     "<b>Yana rasmlar yuborishingiz mumkin yoki keyingi bosqichga o'tish uchun /next buyrug'ini kiriting.</b>",
               parse_mode='HTML'
            )

        else:
            pass

    return "PHOTO"  # Shu holatda qoladi, foydalanuvchi yana rasm yuborishi mumkin


async def next_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photos = context.user_data.get('photos', [])
    if photos:
        await update.message.reply_text(
            text=f"<b>Jami {len(photos)} ta rasm qabul qilindi. Keyingi bosqichga o'tamiz.</b>",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            text="<b>Siz hech qanday rasm yubormadingiz. Davom etish uchun kamida bitta rasm yuboring.</b>",
            parse_mode='HTML'
        )
        return "PHOTO"  # Rasmlar yuborilmagani uchun shu holatda qoladi

    # Joylashuv yuborish tugmasi
    reply_markup = ReplyKeyboardMarkup(
        [[KeyboardButton(text="Joylashuv yuborish", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text="<b>Iltimos, foydalanuvchilar ish joyingizni oson topib borishi uchun, o'z ish joyingiz lokatsiyasini yuboring. Lokatsiya yuborish uchun (Joylashuv yuborish) tugmasini bosing!</b>",
        parse_mode='HTML',
        reply_markup=reply_markup
    )
    return "LOCATION"  # Keyingi bosqich


# Joylashuvni olish va tasdiqlash uchun barcha ma'lumotlarni yuborish
async def handle_location(update, context):
    if update.message.location:
        latitude = update.message.location.latitude
        longitude = update.message.location.longitude

        context.user_data['latitude'] = latitude
        context.user_data['longitude'] = longitude

        # # Foydalanuvchining joylashuvini saqlash
        # context.user_data['location'] = {'latitude': latitude, 'longitude': longitude}

        # Foydalanuvchiga joylashuv qabul qilinganligini bildirish
        await update.message.reply_text(text="<b>Joylashuvingiz qabul qilindi.</b>", parse_mode='HTML')

        # Barcha ma'lumotlarni foydalanuvchiga yuborish
        await send_all_data_to_user(update, context)
        return "CONFIRMATION"
    else:
        # Joylashuv yuborilmagan bo'lsa
        await update.message.reply_text(text="<b>Iltimos, telefoningizdan joylashuvingizni ulashing.</b>", parse_mode='HTML')
        return "LOCATION"


# Ma'lumotlarni formatlab, tasdiqlash tugmasi bilan yuborish
async def send_all_data_to_user(update, context):
    user_data = context.user_data
    photos = user_data.get("photos", [])

    # Foydalanuvchiga yuboriladigan xabar
    message = (
        f"📝 <b>Xizmat Ko'rsatuvchi Ma'lumotlari:</b>\n"
        f"📛 <b>Ismi:</b> {user_data.get('name', 'Noma\'lum')}\n"
        f"📞 <b>Telefon:</b> +{user_data.get('phone_number', 'Noma\'lum')}\n"
        f"🔗 <b>Telegram Link:</b> {user_data.get('telegram_link', 'Noma\'lum')}\n"
        f"📍 <b>Hudud:</b> {user_data.get('region_name', 'Noma\'lum')}\n"
        f"👤 <b>Xizmat turi:</b> {'Erkaklar uchun' if user_data.get('gender') == 'M' else 'Ayollar uchun'}\n"
        f"📖 <b>Ma'lumot:</b> {user_data.get('bio', 'Noma\'lum')}\n"
    )

    # Inline tugmalarni yaratish
    keyboard = [
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data="approve"),
            InlineKeyboardButton("❌ Rad etish", callback_data="reject")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Rasm yuborish (agar mavjud bo'lsa)
    for photo in photos:
        await update.message.reply_photo(photo=photo)

    # Foydalanuvchiga xabarni yuborish
    await update.message.reply_text(
        text=message,
        parse_mode="HTML",
        reply_markup=reply_markup
    )

    return "CONFIRMATION"


#  Xizmat ko'rsatuvchi ma'lumotlarini tasdiqlash va adminga yuborish
async def confirm_and_send_to_admin(update, context):
    query = update.callback_query
    await query.answer()

    action = query.data

    if action == "approve":
        # Foydalanuvchi ma'lumotlarini olish
        user_data = context.user_data.copy()  # Foydalanuvchi ma'lumotlarini nusxalash
        user_id = str(user_data.get("user_id", query.from_user.id))  # Foydalanuvchi ID (agar mavjud bo'lmasa, hozirgi foydalanuvchi ID sini oladi)
        print(f"Foydalanuvchi ID: {user_id}")

        # Ma'lumotlarni context.bot_data["users"] ichida saqlash
        if "users" not in context.bot_data:
            context.bot_data["users"] = {}  # Agar mavjud bo'lmasa, yangi lug'at yaratish

        context.bot_data["users"][user_id] = user_data  # Ma'lumotni saqlash
        print(user_data)

        # Admin uchun xabar yaratish
        admin_message = (
            f"📝 <b>Yangi Xizmat Ko'rsatuvchi Ma'lumotlari:</b>\n"
            f"📛 <b>Ismi:</b> {user_data.get('name', 'Noma\'lum')}\n"
            f"📞 <b>Telefon:</b> +{user_data.get('phone_number', 'Noma\'lum')}\n"
            f"🔗 <b>Telegram Link:</b> {user_data.get('telegram_link', 'Noma\'lum')}\n"
            f"📍 <b>Hudud:</b> {user_data.get('region_name', 'Noma\'lum')}\n"
            f"👤 <b>Xizmat turi:</b> {'Erkaklar uchun' if user_data.get('gender') == 'M' else 'Ayollar uchun'}\n"
            f"📖 <b>Ma'lumot:</b> {user_data.get('bio', 'Noma\'lum')}\n"
            f"🌐 <b>Manzil:</b> Latitude: {user_data.get('latitude', 'Noma\'lum')}, Longitude: {user_data.get('longitude', 'Noma\'lum')}\n"
            f"🆔 <b>Foydalanuvchi ID:</b> {user_id}\n"  # Foydalanuvchi ID ni qo'shish
        )

        # Admin uchun tugmalar
        admin_keyboard = [
            [InlineKeyboardButton("✅ Bazaga saqlash", callback_data=f"service:save:{user_id}")],
            [InlineKeyboardButton("❌ O'chirish", callback_data=f"service:delete:{user_id}")]
        ]
        admin_reply_markup = InlineKeyboardMarkup(admin_keyboard)

        # Ma'lumotlarni adminga yuborish
        try:
            # Rasmlarni yuborish
            for photo in user_data.get("photos", []):
                await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo)

            # Matnli xabarni yuborish
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_message,
                parse_mode="HTML",
                reply_markup=admin_reply_markup
            )
            await query.message.reply_text(text="<b>✅ Ma'lumotlaringiz adminga yuborildi.</b>", parse_mode='HTML')
            await send_main_menu(context=context, chat_id=query.from_user.id)
        except Exception as e:
            print(f"Xatolik yuz berdi: {e}")

        # Tugmachalarni o'chirish
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception as e:
            print(f"Tugmachalarni o'chirishda xatolik: {e}")

        return ConversationHandler.END

    elif action == "reject":
        # Foydalanuvchiga rad etilganligini bildirish
        await query.message.reply_text(text="<b>Ma'lumotlaringizni jo'natishni rad ettingiz.</b>", parse_mode='HTML')
        context.user_data.clear()
        await send_main_menu(context=context, chat_id=query.from_user.id)
        # Tugmachalarni o'chirish
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception as e:
            print(f"Tugmachalarni o'chirishda xatolik: {e}")
        return ConversationHandler.END
