import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery, Message, WebAppInfo, CallbackQuery
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.client.default import DefaultBotProperties

# ===== НАСТРОЙКИ =====
BOT_TOKEN = os.environ.get("BOT_TOKEN")
RENDER_URL = "https://tapalka-bot-hcsb.onrender.com"
WEBHOOK_PATH = "/webhook"
CHANNELS = ["tapalka_news"] # Твой канал

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

SHOP_ITEMS = {
    "mult_5": {"title": "✨ Множитель +5", "price": 25},
    "energy_1000": {"title": "⚡ Энергия +1000", "price": 15},
    "tap_10": {"title": "💪 Сила +10", "price": 20},
    "auto_5": {"title": "🤖 Авто +5 ур.", "price": 75},
    "rebirth_1": {"title": "🔁 Перерождение +1", "price": 200}
}

async def check_sub(user_id):
    if not CHANNELS: return True
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=f"@{channel}", user_id=user_id)
            if member.status in ["left", "kicked"]: return False
        except Exception as e:
            logging.error(f"Ошибка проверки канала {channel}: {e}")
            return True
    return True

def get_play_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🍃 Играть", web_app=WebAppInfo(url="https://kamodikss.github.io/tapalka/"))]])

def get_sub_kb():
    buttons = [[InlineKeyboardButton(text="📢 Подписаться", url=f"https://t.me/{ch}")] for ch in CHANNELS]
    buttons.append([InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    if await check_sub(message.from_user.id):
        await message.answer("👋 Привет! Жми кнопку и играй!", reply_markup=get_play_kb())
    else:
        await message.answer("⚠️ Для доступа подпишись на канал!", reply_markup=get_sub_kb())

@dp.callback_query(F.data == "check_sub")
async def process_check_sub(callback: CallbackQuery):
    if await check_sub(callback.from_user.id):
        await callback.message.edit_text("✅ Отлично! Теперь ты можешь играть.", reply_markup=get_play_kb())
    else:
        await callback.answer("❌ Ты еще не подписался!", show_alert=True)

@dp.message(F.web_app_data)
async def handle_webapp_data(message: Message):
    data = message.web_app_data.data
    if data.startswith("buy_"):
        item_id = data.replace("buy_", "")
        if item_id in SHOP_ITEMS:
            item = SHOP_ITEMS[item_id]
            await message.answer_invoice(title=item["title"], description="Покупка", payload=f"item_{item_id}", provider_token="", currency="XTR", prices=[LabeledPrice(label=item["title"], amount=item["price"])])

@dp.pre_checkout_query()
async def pre_checkout_query(pre_checkout_q: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

@dp.message(F.successful_payment)
async def successful_payment(message: Message):
    await message.answer("✅ Успешно куплено!")

# ===== ФУНКЦИЯ ЗАПУСКА =====
async def on_startup(bot: Bot):
    await bot.set_webhook(f"{RENDER_URL}{WEBHOOK_PATH}")
    logging.info("Webhook установлен!")

def main():
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    app.on_startup.append(on_startup)
    
    port = int(os.environ.get("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
