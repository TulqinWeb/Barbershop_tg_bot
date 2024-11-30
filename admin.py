from barbershop_db import DataBase
from config import ADMIN_ID

db = DataBase()


# Adminni tekshirish funksiyasi
def is_admin(user_id):
    return str(user_id) in ADMIN_ID


# Admin qarorini boshqaruvchi funksiya
async def handle_admin_decision(update, context):
    query = update.callback_query
    await query.answer()

    # Callback data-dan action va user_id olish
    callback_data = query.data

    # Callback data formatini tekshirish
    if not callback_data.startswith("service:"):
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="❌ Xatolik: Noto'g'ri formatdagi callback data."
        )
        return

    # Callback data-dan action va user_id ni ajratib olish
    parts = callback_data.split(":")
    if len(parts) != 3:
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="❌ Xatolik: Callback data noto'g'ri formatda."
        )
        return

    action, user_id = parts[1], parts[2]
    print(user_id)

    # Admin huquqini tekshirish
    if not is_admin(update.effective_user.id):
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="🚫 Sizda bu amalni bajarish huquqi yo'q."
        )
        return

    # Foydalanuvchi ma'lumotlarini olish
    users_data = context.bot_data.get("users", {})  # Barcha foydalanuvchilar ma'lumotlarini olish
    user_data = users_data.get(user_id)  # ID bo'yicha kerakli foydalanuvchini olish

    if not user_data:
        await query.message.reply_text("❌ Foydalanuvchi ma'lumotlari topilmadi.")
        return

    # Foydalanuvchi ma'lumotlarini ajratib olish
    name = user_data.get("name", "Noma'lum")
    phone = user_data.get("phone_number", "Noma'lum")
    telegram_link = user_data.get("telegram_link", "Noma'lum")
    region_name = user_data.get("region_name", "Noma'lum")
    gender = user_data.get("gender", "Noma'lum")
    bio = user_data.get("bio", "Noma'lum")
    latitude = user_data.get("latitude", "Noma'lum")
    longitude = user_data.get("longitude", "Noma'lum")
    photos = user_data.get("photos", [])

    if action == "save":
        # Hududni olish yoki yaratish
        regions = db.get_all_regions()
        region_id = next((reg["region_id"] for reg in regions if reg["region_name"] == region_name), None)

        if not region_id:
            db.create_region(region_name)
            regions = db.get_all_regions()
            region_id = next(reg["region_id"] for reg in regions if reg["region_name"] == region_name)

        # Barberni yaratish
        db.create_barber(name, telegram_link, phone, gender, bio, region_id, latitude, longitude)

        # Barber ID ni olish
        db.cursor.execute(
            "SELECT barber_id FROM barbers WHERE name = %s AND phone = %s", (name, phone)
        )
        barber = db.cursor.fetchone()

        if barber:
            barber_id = barber[0]
            for photo in photos:
                db.insert_photo(barber_id, photo)

            await context.bot.send_message(
                chat_id=query.from_user.id,
                text="✅ Ma'lumotlar bazaga muvaffaqiyatli saqlandi!"
            )

            # Xizmat ko'rsatuvchiga xabar yuborish
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="✅ Ma'lumotlaringiz tasdiqlandi! Endi xizmatlaringiz tizimga qo'shildi.",
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"Xizmat ko'rsatuvchiga xabar yuborishda xatolik: {e}")

            # Tugmachalarni o'chirish
            try:
                await query.edit_message_reply_markup(reply_markup=None)
            except Exception as e:
                print(f"Tugmachalarni o'chirishda xatolik: {e}")
        else:
            await context.bot.send_message(
                chat_id=query.from_user.id,
                text="❌ Ma'lumotlar bazaga saqlanmadi. Iltimos, yana urinib ko'ring."
            )

    elif action == "delete":
        # Foydalanuvchi ma'lumotlarini o'chirish
        users_data.pop(user_id, None)
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="❌ Foydalanuvchi ma'lumotlari o'chirildi!"
        )

        # Xizmat ko'rsatuvchiga xabar yuborish
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Ma'lumotlaringiz tasdiqlanmadi. Tizimga qo'shilmadingiz.",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Xizmat ko'rsatuvchiga xabar yuborishda xatolik: {e}")

        # Tugmachalarni o'chirish
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception as e:
            print(f"Tugmachalarni o'chirishda xatolik: {e}")
