import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Токен берется из переменных окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ССЫЛКА НА ТВОЙ САЙТ (MINI APP)
# ВАЖНО: Telegram требует HTTPS. Сюда нужно вставить ссылку на твой сайт (например, https://vape-off.ru)
# Если сайта пока нет, можешь оставить ссылку на профиль @IkrovnI, но кнопка МАПП не сработает.
MINI_APP_URL = "https://t.me/IkrovnI" 

# Тексты
WELCOME_TEXT = (
    "🔥 <b>Добро пожаловать в Vape off!</b> 🔥\n\n"
    "Здесь ты найдешь все для вкусного пара:\n"
    "💨 Одноразки\n"
    "💧 Жижи\n"
    "⚙️ Расходники\n"
    "🎁 И многое другое — большой выбор!\n\n"
    "Весь каталог и оформление заказа находятся в нашем приложении. Жми кнопку ниже 👇\n\n"
    "По любым вопросам писать: @IkrovnI"
)

# Клавиатура
def main_keyboard():
    keyboard = [
        # Кнопка запуска Mini App
        [InlineKeyboardButton("🚀 Открыть каталог (Mini App)", web_app=WebAppInfo(url=MINI_APP_URL))],
        # Кнопка связи с тобой
        [InlineKeyboardButton("💬 Написать менеджеру", url="https://t.me/IkrovnI")],
    ]
    return InlineKeyboardMarkup(keyboard)

# Обработчики
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        WELCOME_TEXT,
        parse_mode="HTML",
        reply_markup=main_keyboard(),
    )

# Автоответ на любые другие сообщения
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Спасибо за сообщение! Я передал его менеджеру @IkrovnI.\n"
        "А пока ты можешь посмотреть наш каталог в приложении 👇",
        reply_markup=main_keyboard(),
    )

# Запуск
def main():
    if not TOKEN:
        raise ValueError("Не задан TELEGRAM_BOT_TOKEN!")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))

    logger.info("Бот Vape off (Mini App) запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
