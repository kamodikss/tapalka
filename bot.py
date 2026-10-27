import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery, Message, WebAppInfo, CallbackQuery
from aiohttp import web

# ТОКЕН БОТА
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ВСТАВЬ_СЮДА_ТОКЕН_ОТ_BOTFATHER")
# ССЫЛКА НА ИГРУ (GitHub Pages)
WEBAPP_URL = "https://kamodikss.github.io/tapalka/"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ВАЖНО: СЮДА ВПИШИ ЮЗЕРНЕЙМ ТВОЕГО КАНАЛА (без @)
# Если каналов несколько, добавь их через запятую: ["channel1", "channel2"]
CHANNELS = ["tapalka_news"] 

SHOP_ITEMS = {
    "mult_5": {"title": "✨ Множитель +5", "price": 25},
    "energy_1000": {"title": "⚡ Энергия +1000", "price": 15},
    "tap_10": {"title": "💪 Сила +10", "price": 20},
    "auto_5": {"title": "🤖 Авто +5 ур.", "price": 75},
    "rebirth_1": {"title": "🔁 Перерождение +1", "price": 200}
}

# Функция проверки подписки на каналы
async def check_sub(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=f"@{channel}", user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception as e:
            logging.error(f"Ошибка проверки канала {channel}: {e}")
            return False
    return True

# Кнопка для игры
def get_play_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍃 Играть", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])

# Кнопки подписки
def get_sub_kb():
    buttons = []
    for ch in CHANNELS:
        buttons.append([InlineKeyboardButton(text=f"📢 Подписаться на новости", url=f"https://t.me/{ch}")])
    buttons.append([InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    is_subbed = await check_sub(message.from_user.id)
    if is_subbed:
        await message.answer(
            "👋 Привет! Ты подписан на наш канал. Нажимай кнопку и играй!\n\n"
            "🔥 В игре тебя ждут бонусы и листинг $LEAF!",
            reply_markup=get_play_kb()
        )
    else:
        await message.answer(
            "⚠️ Для доступа к игре нужно подписаться на наш канал с новостями!\n\n"
            "1. Нажми кнопку «Подписаться»\n"
            "2. Вернись сюда и нажми «Я подписался»",
            reply_markup=get_sub_kb()
        )

@dp.callback_query(F.data == "check_sub")
async def process_check_sub(callback: CallbackQuery):
    is_subbed = await check_sub(callback.from_user.id)
    if is_subbed:
        await callback.message.edit_text(
            "✅ Отлично! Теперь ты можешь играть.\n"
            "Жми кнопку ниже и забирай бонус!",
            reply_markup=get_play_kb()
        )
    else:
        await callback.answer("❌ Ты еще не подписался на канал!", show_alert=True)

# Обработка запроса на покупку из WebApp
@dp.message(F.web_app_data)
async def handle_webapp_data(message: Message):
    data = message.web_app_data.data
    if data.startswith("buy_"):
        item_id = data.replace("buy_", "")
        if item_id in SHOP_ITEMS:
            item = SHOP_ITEMS[item_id]
            await message.answer_invoice(
                title=item["title"],
                description=f"Покупка в игре Листочки",
                payload=f"item_{item_id}",
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(label=item["title"], amount=item["price"])]
            )

# Проверка перед оплатой
@dp.pre_checkout_query()
async def pre_checkout_query(pre_checkout_q: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

# Успешная оплата
@dp.message(F.successful_payment)
async def successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload
    item_id = payload.replace("item_", "")
    await message.answer(f"✅ Успешно куплено: {SHOP_ITEMS[item_id]['title']}!\n\nЗаходи в игру, чтобы использовать бонус.")

# --- Веб-сервер для Render ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
