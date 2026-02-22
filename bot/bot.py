import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.fsm.storage.memory import MemoryStorage
import aiohttp
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
API_BASE = os.getenv("API_BASE", "http://localhost:8000/api")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-casino-domain.com")
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "")  # e.g. "@yourchannel"
SECRET = os.getenv("SECRET_KEY", "your-super-secret-key-c")[:20]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ============= SUBSCRIPTION CHECK =============
async def check_subscription(user_id: int) -> bool:
    if not REQUIRED_CHANNEL:
        return True
    try:
        member = await bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status not in ["left", "kicked", "banned"]
    except:
        return False

# ============= API HELPERS =============
async def api_register(telegram_id: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_BASE}/auth/telegram-register",
            json={"telegram_id": telegram_id, "secret": SECRET}
        ) as resp:
            return await resp.json()

async def api_get_user_info(username: str, password: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_BASE}/auth/login",
            json={"username": username, "password": password}
        ) as resp:
            if resp.status == 200:
                return await resp.json()
    return None

# ============= START COMMAND =============
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = str(message.from_user.id)
    
    # Check subscription
    if REQUIRED_CHANNEL and not await check_subscription(message.from_user.id):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{REQUIRED_CHANNEL.lstrip('@')}"),
            InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")
        ]])
        await message.answer(
            "❌ *Botdan foydalanish uchun kanalga obuna bo'lishingiz kerak!*",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        return
    
    # Register/get user
    result = await api_register(user_id)
    
    if result.get("exists"):
        # Returning user
        keyboard = main_keyboard()
        await message.answer(
            f"👋 Xush kelibsiz qaytib!\n\n"
            f"👤 Login: `{result['username']}`\n"
            f"💰 Balans: *{result['balance']}* so'm\n\n"
            f"O'yin o'ynash uchun quyidagi tugmalardan foydalaning:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    else:
        # New user
        keyboard = main_keyboard()
        await message.answer(
            f"🎰 *Casino'ga xush kelibsiz!*\n\n"
            f"✅ Hisobingiz yaratildi!\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"👤 Login: `{result['username']}`\n"
            f"🔐 Parol: `{result['password']}`\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"⚠️ *Bu ma'lumotlarni saqlang!*\n"
            f"Web App'ga kirish uchun ishlatiladi.\n\n"
            f"💰 Balansni to'ldirish uchun /deposit buyrug'ini yuboring.",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

def main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 O'yin O'ynash", web_app=WebAppInfo(url=f"{WEBAPP_URL}/games"))],
        [
            InlineKeyboardButton(text="👤 Profil", callback_data="profile"),
            InlineKeyboardButton(text="💰 Balans", callback_data="balance")
        ],
        [
            InlineKeyboardButton(text="➕ To'ldirish", callback_data="deposit"),
            InlineKeyboardButton(text="➖ Yechish", callback_data="withdraw")
        ],
        [InlineKeyboardButton(text="🎟 Promokod", callback_data="promo")]
    ])

# ============= SUBSCRIPTION CHECK CALLBACK =============
@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: types.CallbackQuery):
    if await check_subscription(callback.from_user.id):
        await callback.message.delete()
        # Restart
        await cmd_start(callback.message)
    else:
        await callback.answer("❌ Siz hali obuna bo'lmagansiz!", show_alert=True)

# ============= PROFILE =============
@dp.callback_query(F.data == "profile")
async def profile_callback(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    result = await api_register(user_id)
    
    if result.get("status") == "blocked":
        await callback.answer("❌ Sizning hisobingiz bloklangan!", show_alert=True)
        return
    
    text = (
        f"👤 *Profilingiz*\n\n"
        f"🆔 Telegram ID: `{user_id}`\n"
        f"👤 Login: `{result.get('username', '-')}`\n"
        f"💰 Balans: *{result.get('balance', 0)}* so'm\n"
    )
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=main_keyboard())
    await callback.answer()

# ============= BALANCE =============
@dp.callback_query(F.data == "balance")
async def balance_callback(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    result = await api_register(user_id)
    
    await callback.answer(f"💰 Balansingiz: {result.get('balance', 0)} so'm", show_alert=True)

# ============= DEPOSIT =============
@dp.callback_query(F.data == "deposit")
async def deposit_callback(callback: types.CallbackQuery):
    await callback.message.answer(
        "💳 *Balans to'ldirish*\n\n"
        "To'ldirish uchun admin bilan bog'laning:\n"
        "👨‍💼 @AdminUsername\n\n"
        "To'lov amalga oshirilgach, admin balansingizni yangilaydi.\n\n"
        "To'lov miqdori va vaqtini yuboring:\n"
        "Masalan: `/deposit 50000`",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(Command("deposit"))
async def cmd_deposit(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ To'g'ri format: /deposit <summa>\nMasalan: /deposit 50000")
        return
    
    try:
        amount = float(parts[1])
    except:
        await message.answer("❌ Noto'g'ri summa!")
        return
    
    user_id = str(message.from_user.id)
    # Send deposit request to admins
    admin_ids = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
    
    for admin_id in admin_ids:
        try:
            await bot.send_message(
                admin_id,
                f"💰 *YANGI TO'LDIRISH SO'ROVI*\n\n"
                f"👤 Foydalanuvchi: @{message.from_user.username or 'noname'}\n"
                f"🆔 Telegram ID: `{user_id}`\n"
                f"💵 Summa: *{amount}* so'm\n"
                f"⏰ Vaqt: {message.date}\n\n"
                f"Tasdiqlash uchun: /approve_{user_id}_{int(amount)}",
                parse_mode="Markdown"
            )
        except:
            pass
    
    await message.answer(
        f"✅ So'rovingiz adminlarga yuborildi!\n"
        f"💵 Summa: *{amount}* so'm\n\n"
        f"Tasdiqlangancha kuting...",
        parse_mode="Markdown"
    )

# ============= WITHDRAW =============
@dp.callback_query(F.data == "withdraw")
async def withdraw_callback(callback: types.CallbackQuery):
    await callback.message.answer(
        "💸 *Balans yechish*\n\n"
        "Yechish uchun:\n"
        "`/withdraw <summa> <karta_raqam>`\n\n"
        "Masalan: `/withdraw 100000 8600123456789012`",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(Command("withdraw"))
async def cmd_withdraw(message: types.Message):
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ Format: /withdraw <summa> <karta/hamyon>")
        return
    
    try:
        amount = float(parts[1])
        wallet = parts[2]
    except:
        await message.answer("❌ Noto'g'ri format!")
        return
    
    user_id = str(message.from_user.id)
    admin_ids = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
    
    for admin_id in admin_ids:
        try:
            await bot.send_message(
                admin_id,
                f"💸 *YANGI YECHISH SO'ROVI*\n\n"
                f"👤 @{message.from_user.username or 'noname'}\n"
                f"🆔 ID: `{user_id}`\n"
                f"💵 Summa: *{amount}* so'm\n"
                f"💳 Karta: `{wallet}`\n"
                f"⏰ Vaqt: {message.date}",
                parse_mode="Markdown"
            )
        except:
            pass
    
    await message.answer(
        f"✅ Yechish so'rovi yuborildi!\n💵 Summa: *{amount}* so'm",
        parse_mode="Markdown"
    )

# ============= PROMO =============
@dp.callback_query(F.data == "promo")
async def promo_callback(callback: types.CallbackQuery):
    await callback.message.answer(
        "🎟 *Promokod kiritish*\n\n"
        "Promokodingizni kiriting:\n"
        "`/promo KODINGIZ`",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(Command("promo"))
async def cmd_promo(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Format: /promo <KODINGIZ>")
        return
    
    code = parts[1].upper()
    await message.answer(f"🎟 Promokod `{code}` tekshirilmoqda...", parse_mode="Markdown")
    # User redirected to webapp to apply promo with their session

# ============= ADMIN COMMANDS =============
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    admin_ids = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
    if message.from_user.id not in admin_ids:
        await message.answer("❌ Ruxsat yo'q!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika", web_app=WebAppInfo(url=f"{WEBAPP_URL}/admin"))],
        [InlineKeyboardButton(text="💰 Kutayotgan to'lovlar", callback_data="pending_payments")],
        [InlineKeyboardButton(text="📢 Reklama yuborish", callback_data="send_ad")],
    ])
    
    await message.answer("👨‍💼 *Admin Panel*", parse_mode="Markdown", reply_markup=keyboard)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
