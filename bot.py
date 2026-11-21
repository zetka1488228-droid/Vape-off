import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler
)

# Настройка логов
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Получаем переменные из Railway
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

MINI_APP_URL = "https://vapeoffj.netlify.app"
ADMIN_IDS = [8678582128, 8918951833]

# Состояния для диалога добавления товара
PHOTO, TITLE, PRICE, CATEGORY, FLAVORS = range(5)

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Открыть каталог", web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton("💬 Написать менеджеру", url="https://t.me/v4peoff")],
        [InlineKeyboardButton("📢 Наш канал", url="https://t.me/v4peofff")]
    ])

def admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить товар", callback_data="add_product")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🔥 <b>Добро пожаловать в Vape off!</b> 🔥\n\nЖми кнопку, чтобы открыть каталог!"
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=main_keyboard())

async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Менеджер скоро ответит. А пока посмотри каталог!", reply_markup=main_keyboard())

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет доступа к админ-панели.")
        return
    await update.message.reply_text("🛠 <b>Админ-панель</b>\nВыберите действие:", parse_mode="HTML", reply_markup=admin_keyboard())

async def add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📸 Отправьте фото товара (как картинку, не файлом).")
    return PHOTO

async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Защита от того, что пользователь отправил не фото
    if not update.message.photo:
        await update.message.reply_text("❌ Пожалуйста, отправьте именно картинку (фото).")
        return PHOTO

    try:
        # Скачиваем фото из Telegram
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        file_name = f"product_{update.message.message_id}.jpg"
        
        # Загружаем в Supabase Storage
        url = f"{SUPABASE_URL}/storage/v1/object/products/{file_name}"
        
        # ВАЖНО: Для новых ключей sb_publishable нужен заголовок apikey
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "image/jpeg"
        }
        
        response = requests.post(url, headers=headers, data=photo_bytes)
        
        # Если статус 200 или 201 (создано), значит всё ок
        if response.status_code in [200, 201]:
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/products/{file_name}"
            context.user_data['image_url'] = public_url
            await update.message.reply_text("✅ Фото загружено!\nТеперь введите НАЗВАНИЕ товара.")
            return TITLE
        else:
            error_msg = response.json().get('message', response.text)
            await update.message.reply_text(f"❌ Ошибка загрузки фото: {error_msg}")
            return PHOTO
    except Exception as e:
        await update.message.reply_text(f"❌ Системная ошибка при загрузке: {str(e)}")
        return PHOTO

async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    await update.message.reply_text("Введите ЦЕНУ товара (только цифру, например: 17).")
    return PRICE

async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['price'] = int(update.message.text)
        await update.message.reply_text("Введите КАТЕГОРИЮ (Жидкости, Испарители, Расходники).")
        return CATEGORY
    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите цену цифрой (без букв и символов).")
        return PRICE

async def get_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['category'] = update.message.text
    await update.message.reply_text("Введите ВКУСЫ через запятую (например: Клубника, Банан). Если вкусов нет — напишите 'нет'.")
    return FLAVORS

async def get_flavors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flavors_text = update.message.text
    if flavors_text.lower() == 'нет':
        flavors_text = ""
        
    data = {
        "title": context.user_data['title'],
        "price": context.user_data['price'],
        "category": context.user_data['category'],
        "image_url": context.user_data['image_url'],
        "flavors": flavors_text
    }
    
    # Сохраняем данные в таблицу products
    url = f"{SUPABASE_URL}/rest/v1/products"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code in [200, 201]:
            await update.message.reply_text("✅ Товар успешно добавлен в каталог!", reply_markup=main_keyboard())
        else:
            error_msg = response.text
            await update.message.reply_text(f"❌ Ошибка базы данных: {error_msg}")
    except Exception as e:
        await update.message.reply_text(f"❌ Системная ошибка: {str(e)}")
        
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добавление товара отменено.", reply_markup=main_keyboard())
    return ConversationHandler.END

def main():
    if not TOKEN:
        raise ValueError("Не задан TELEGRAM_BOT_TOKEN!")
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Не заданы SUPABASE_URL или SUPABASE_KEY!")

    app = ApplicationBuilder().token(TOKEN).build()

    # Обработчик шагов добавления товара
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_product_start, pattern="^add_product$")],
        states={
            PHOTO: [MessageHandler(filters.PHOTO | filters.TEXT, get_photo)], # Ловим и фото, и текст (чтобы выдать ошибку)
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_category)],
            FLAVORS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_flavors)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))

    logging.info("Бот Vape off успешно запущен и готов к работе!")
    app.run_polling()

if __name__ == "__main__":
    main()
