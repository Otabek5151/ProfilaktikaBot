import asyncio
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from dotenv import load_dotenv

from sheets import (
    get_base_by_id,
    get_active_employees,
    save_profilaktika,
    get_profilaktika_records,
    bazalar_sheet,
)


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN .env faylida topilmadi!")


dp = Dispatcher()


# =========================================================
# ASOSIY MENYU
# =========================================================

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🔧 Profilaktikani boshlash"),
        ],
        [
            KeyboardButton(text="📊 Hisobot"),
        ],
    ],
    resize_keyboard=True
)


# =========================================================
# VAQTINCHALIK FOYDALANUVCHI MA'LUMOTLARI
# =========================================================

user_data = {}


# =========================================================
# 4 OYLIK DAVRNI ANIQLASH
# =========================================================

def get_current_period():
    """
    Joriy sanaga qarab 4 oylik davrni qaytaradi.
    """

    now = datetime.now()

    month = now.month
    year = now.year

    if month <= 4:
        return f"01.01.{year} – 30.04.{year}"

    elif month <= 8:
        return f"01.05.{year} – 31.08.{year}"

    else:
        return f"01.09.{year} – 31.12.{year}"


# =========================================================
# /START
# =========================================================

@dp.message(Command("start"))
async def start_handler(message: types.Message):

    # Eski jarayon bo'lsa tozalaymiz
    user_data.pop(message.from_user.id, None)

    await message.answer(
        "🤖 <b>Profilaktika Bot</b>ga xush kelibsiz!\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=main_keyboard,
        parse_mode="HTML"
    )


# =========================================================
# PROFILAKTIKANI BOSHLASH
# =========================================================

@dp.message(F.text == "🔧 Profilaktikani boshlash")
async def start_profilaktika(message: types.Message):

    user_data[message.from_user.id] = {
        "base": None,
        "employees": [],
    }

    await message.answer(
        "🗄 <b>Baza ID raqamini kiriting:</b>\n\n"
        "Masalan: <code>HRZ5901</code>",
        parse_mode="HTML"
    )


# =========================================================
# HISOBOT
# MUHIM: BU HANDLER receive_message DAN OLDIN TURADI
# =========================================================

@dp.message(F.text == "📊 Hisobot")
async def report_handler(message: types.Message):

    try:

        # Joriy 4 oylik davr
        period = get_current_period()

        # -------------------------------------------------
        # FAOL BAZALARNI OLAMIZ
        # -------------------------------------------------

        base_records = bazalar_sheet.get_all_records()

        active_bases = {}

        for row in base_records:

            faol = str(
                row.get("Faol", "")
            ).strip().lower()

            if faol in ["ha", "true", "1", "active"]:

                base_id = str(
                    row.get("ID", "")
                ).strip().upper()

                base_name = str(
                    row.get("Baza nomi", "")
                ).strip()

                if base_id:
                    active_bases[base_id] = base_name

        # -------------------------------------------------
        # PROFILAKTIKA YOZUVLARINI OLAMIZ
        # -------------------------------------------------

        records = get_profilaktika_records()

        completed_ids = set()

        for row in records:

            record_period = str(
                row.get("4 oylik davr", "")
            ).strip()

            # Faqat joriy davr
            if record_period != period:
                continue

            # Profilaktika jadvalidagi ID
            base_id = str(
                row.get("ID", "")
            ).strip().upper()

            if base_id:
                completed_ids.add(base_id)

        # -------------------------------------------------
        # BAJARILGAN / BAJARILMAGAN BAZALAR
        # -------------------------------------------------

        completed_bases = []
        incomplete_bases = []

        for base_id, base_name in active_bases.items():

            if base_id in completed_ids:

                completed_bases.append(
                    f"• {base_id} — {base_name}"
                )

            else:

                incomplete_bases.append(
                    f"• {base_id} — {base_name}"
                )

        # -------------------------------------------------
        # SONLAR
        # -------------------------------------------------

        total = len(active_bases)

        completed_count = len(
            completed_bases
        )

        incomplete_count = len(
            incomplete_bases
        )

        # -------------------------------------------------
        # HISOBOTNI YASAYMIZ
        # -------------------------------------------------

        report = (
            "📊 <b>PROFILAKTIKA HISOBOTI</b>\n\n"

            f"🔄 <b>Joriy davr:</b>\n"
            f"{period}\n\n"

            f"🗄 <b>Jami bazalar:</b> "
            f"{total} ta\n"

            f"✅ <b>Profilaktika o'tkazilgan:</b> "
            f"{completed_count} ta\n"

            f"❌ <b>Profilaktika o'tkazilmagan:</b> "
            f"{incomplete_count} ta\n\n"

            "━━━━━━━━━━━━━━\n\n"

            "✅ <b>O'TKAZILGAN BAZALAR:</b>\n\n"
        )

        # -------------------------------------------------
        # BAJARILGAN BAZALAR
        # -------------------------------------------------

        if completed_bases:

            report += "\n".join(
                completed_bases
            )

        else:

            report += (
                "Hozircha profilaktika "
                "o'tkazilmagan."
            )

        # -------------------------------------------------
        # BAJARILMAGAN BAZALAR
        # -------------------------------------------------

        report += (
            "\n\n━━━━━━━━━━━━━━\n\n"
            "❌ <b>O'TKAZILMAGAN BAZALAR:</b>\n\n"
        )

        if incomplete_bases:

            report += "\n".join(
                incomplete_bases
            )

        else:

            report += (
                "Barcha bazalarda profilaktika "
                "o'tkazilgan! ✅"
            )

        # -------------------------------------------------
        # TELEGRAMGA YUBORAMIZ
        # -------------------------------------------------

        await message.answer(
            report,
            parse_mode="HTML"
        )

    except Exception as e:

        print(
            "Hisobot xatosi:",
            repr(e)
        )

        await message.answer(
            "❌ Hisobotni shakllantirishda "
            "xatolik yuz berdi.\n\n"
            "Terminaldagi xatoni tekshiring."
        )


# =========================================================
# BAZA ID YOKI KAMCHILIK / IZOH QABUL QILISH
# =========================================================

@dp.message()
async def receive_message(message: types.Message):

    user_id = message.from_user.id

    # Profilaktika boshlanmagan
    if user_id not in user_data:
        return

    data = user_data[user_id]

    # =====================================================
    # 1. BAZA ID
    # =====================================================

    if data.get("base") is None:

        base_id = message.text.strip()

        base = get_base_by_id(
            base_id
        )

        if not base:

            await message.answer(
                "❌ Bunday faol baza topilmadi.\n\n"
                "Iltimos, Baza ID raqamini qayta kiriting."
            )

            return

        data["base"] = base

        # Faol xodimlar
        employees = get_active_employees()

        if not employees:

            await message.answer(
                "❌ Faol xodimlar ro‘yxati topilmadi."
            )

            return

        keyboard = []

        for employee in employees:

            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=f"☐ {employee['name']}",
                        callback_data=(
                            f"emp_{employee['telegram_id']}"
                        )
                    )
                ]
            )

        keyboard.append(
            [
                InlineKeyboardButton(
                    text="➡️ Davom etish",
                    callback_data="employees_done"
                )
            ]
        )

        await message.answer(
            f"✅ Baza topildi!\n\n"

            f"🗄 ID: "
            f"<b>{base['id']}</b>\n"

            f"📍 Baza: "
            f"<b>{base['name']}</b>\n\n"

            "👤 <b>Profilaktikani amalga "
            "oshiruvchi xodimlarni tanlang:</b>\n"

            "Bir yoki bir nechta xodimni "
            "tanlashingiz mumkin.",

            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=keyboard
            ),

            parse_mode="HTML"
        )

        return

    # =====================================================
    # 2. KAMCHILIK / IZOH
    # =====================================================

    if data.get("employee_names"):

        comment = message.text.strip()

        if not comment:

            await message.answer(
                "⚠️ Iltimos, kamchilik yoki "
                "izohni kiriting."
            )

            return

        data["comment"] = comment

        # Sana va vaqt
        now = datetime.now()

        date_text = now.strftime(
            "%d.%m.%Y"
        )

        time_text = now.strftime(
            "%H:%M"
        )

        # 4 oylik davr
        period = get_current_period()

        data["date"] = date_text
        data["time"] = time_text
        data["period"] = period

        base = data["base"]

        employee_names = data[
            "employee_names"
        ]

        # Tasdiqlash tugmalari
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Saqlash",
                        callback_data=(
                            "save_profilaktika"
                        )
                    ),
                    InlineKeyboardButton(
                        text="❌ Bekor qilish",
                        callback_data=(
                            "cancel_profilaktika"
                        )
                    )
                ]
            ]
        )

        await message.answer(
            "📋 <b>Profilaktika ma'lumotlarini "
            "tasdiqlang:</b>\n\n"

            f"🗄 <b>Baza ID:</b> "
            f"{base['id']}\n"

            f"📍 <b>Baza nomi:</b> "
            f"{base['name']}\n"

            f"📅 <b>Sana:</b> "
            f"{date_text} {time_text}\n\n"

            "👤 <b>Xodimlar:</b>\n"

            + "\n".join(
                f"• {name}"
                for name in employee_names
            )

            + "\n\n"

            f"📝 <b>Kamchilik / izoh:</b>\n"
            f"{comment}\n\n"

            f"🔄 <b>4 oylik davr:</b>\n"
            f"{period}\n\n"

            "Ma'lumotlar to'g'riligini tekshiring.",

            reply_markup=keyboard,

            parse_mode="HTML"
        )


# =========================================================
# XODIM TANLASH
# =========================================================

@dp.callback_query(
    F.data.startswith("emp_")
)
async def select_employee(
    callback: types.CallbackQuery
):

    user_id = callback.from_user.id

    if user_id not in user_data:

        await callback.answer(
            "Avval profilaktikani boshlang."
        )

        return

    employee_id = callback.data.replace(
        "emp_",
        ""
    )

    employees = get_active_employees()

    employee = next(
        (
            emp
            for emp in employees
            if emp["telegram_id"] == employee_id
        ),
        None
    )

    if not employee:

        await callback.answer(
            "Xodim topilmadi."
        )

        return

    selected = user_data[user_id][
        "employees"
    ]

    # Tanlangan bo'lsa — olib tashlaymiz
    if employee_id in selected:

        selected.remove(
            employee_id
        )

        await callback.answer(
            f"❌ {employee['name']} "
            "olib tashlandi"
        )

    # Tanlanmagan bo'lsa — qo'shamiz
    else:

        selected.append(
            employee_id
        )

        await callback.answer(
            f"✅ {employee['name']} "
            "tanlandi"
        )

    # Tugmalarni qayta chizamiz
    keyboard = []

    for emp in employees:

        if emp["telegram_id"] in selected:

            symbol = "☑️"

        else:

            symbol = "☐"

        keyboard.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"{symbol} "
                        f"{emp['name']}"
                    ),
                    callback_data=(
                        f"emp_{emp['telegram_id']}"
                    )
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="➡️ Davom etish",
                callback_data="employees_done"
            )
        ]
    )

    await callback.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )


# =========================================================
# XODIM TANLASH TUGADI
# =========================================================

@dp.callback_query(
    F.data == "employees_done"
)
async def employees_done(
    callback: types.CallbackQuery
):

    user_id = callback.from_user.id

    if user_id not in user_data:

        await callback.answer(
            "Avval profilaktikani boshlang."
        )

        return

    selected = user_data[user_id][
        "employees"
    ]

    if not selected:

        await callback.answer(
            "⚠️ Kamida bitta xodimni tanlang.",
            show_alert=True
        )

        return

    employees = get_active_employees()

    selected_names = [
        emp["name"]
        for emp in employees
        if emp["telegram_id"] in selected
    ]

    user_data[user_id][
        "employee_names"
    ] = selected_names

    await callback.message.answer(
        "✅ <b>Xodimlar tanlandi!</b>\n\n"

        "👤 <b>Xodimlar:</b>\n"

        + "\n".join(
            f"• {name}"
            for name in selected_names
        )

        + "\n\n"

        "📝 <b>Aniqlangan kamchiliklarni "
        "kiriting:</b>\n"

        "Agar kamchilik bo‘lmasa, "
        "<code>Kamchilik aniqlanmadi</code> "
        "deb yozing.",

        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# SAQLASH
# =========================================================

@dp.callback_query(
    F.data == "save_profilaktika"
)
async def save_profilaktika_handler(
    callback: types.CallbackQuery
):

    user_id = callback.from_user.id

    if user_id not in user_data:

        await callback.answer(
            "❌ Profilaktika ma'lumotlari "
            "topilmadi.",
            show_alert=True
        )

        return

    data = user_data[user_id]

    try:

        new_id = save_profilaktika(
            base_id=data["base"]["id"],
            base_name=data["base"]["name"],
            date_text=data["date"],
            time_text=data["time"],
            employee_names=data[
                "employee_names"
            ],
            comment=data["comment"],
            period=data["period"],
        )

        await callback.message.answer(
            "✅ <b>Profilaktika "
            "muvaffaqiyatli saqlandi!</b>\n\n"

            f"🗄 Baza ID: "
            f"<b>{data['base']['id']}</b>\n"

            f"📍 Baza: "
            f"<b>{data['base']['name']}</b>\n"

            f"📅 Sana: "
            f"<b>{data['date']} "
            f"{data['time']}</b>\n"

            f"🔄 Davr: "
            f"<b>{data['period']}</b>",

            reply_markup=main_keyboard,

            parse_mode="HTML"
        )

        # Vaqtinchalik ma'lumotlarni tozalaymiz
        user_data.pop(
            user_id,
            None
        )

        await callback.answer(
            "✅ Saqlandi!"
        )

    except Exception as e:

        print(
            "Google Sheets saqlash xatosi:",
            repr(e)
        )

        await callback.answer(
            "❌ Saqlashda xatolik yuz berdi.",
            show_alert=True
        )


# =========================================================
# BEKOR QILISH
# =========================================================

@dp.callback_query(
    F.data == "cancel_profilaktika"
)
async def cancel_profilaktika(
    callback: types.CallbackQuery
):

    user_id = callback.from_user.id

    user_data.pop(
        user_id,
        None
    )

    await callback.message.answer(
        "❌ Profilaktika bekor qilindi.",
        reply_markup=main_keyboard
    )

    await callback.answer()


# =========================================================
# BOTNI ISHGA TUSHIRISH
# =========================================================

async def main():

    bot = Bot(
        token=BOT_TOKEN
    )

    print(
        "🤖 Profilaktika Bot ishga tushdi!"
    )

    print(
        "Telegramdan foydalanishga tayyor."
    )

    await dp.start_polling(
        bot
    )


if __name__ == "__main__":
    asyncio.run(main())