import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Токен берется из переменных окружения Railway
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Тексты
WELCOME_TEXT = (
    "🔥 <b>Добро пожаловать в Vape off!</b> 🔥\n\n"
    "Здесь ты найдешь все для вкусного пара:\n"
    "💨 Одноразки\n"
    "💧 Жижи\n"
    "⚙️ Расходники\n"
    "🎁 И многое другое — большой выбор!\n\n"
    "Весь каталог и оформление заказа находятся в нашем приложении.\n"
    "По любым вопросам пиши: @IkrovnI"
)

# Клавиатура (только кнопка связи, без Mini App)
def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("💬 Написать менеджеру", url="https://t.me/IkrovnI")],
    ]
    return InlineKeyboardMarkup(keyboard)

# Обработчик команды /start
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
        "Он ответит тебе в ближайшее время.",
        reply_markup=main_keyboard(),
    )

# Запуск
def main():
    if not TOKEN:
        raise ValueError("Не задан TELEGRAM_BOT_TOKEN!")

    # drop_pending_updates=True очищает старые зависшие запросы (решает конфликты)
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))

    logger.info("Бот Vape off запущен!")
    
    # Запускаем без очистки, чтобы избежать проблем
    app.run_polling()

if __name__ == "__main__":
    main()
