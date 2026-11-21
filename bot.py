import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

MINI_APP_URL = "https://vapeoffj.netlify.app"
ADMIN_IDS = [8678582128, 8918951833]

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
    await update.message.reply_text("🔥 <b>Добро пожаловать в Vape off!</b> 🔥\n\nЖми кнопку, чтобы открыть каталог!", parse_mode="HTML", reply_markup=main_keyboard())

async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Менеджер скоро ответит. А пока посмотри каталог!", reply_markup=main_keyboard())

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет доступа.")
        return
    await update.message.reply_text("🛠 <b>Админ-панель</b>", parse_mode="HTML", reply_markup=admin_keyboard())

async def add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📸 Отправьте фото товара.")
    return PHOTO

async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ Отправьте именно фото.")
        return PHOTO
    try:
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Загрузка в Cloudinary
        parts = CLOUDINARY_URL.replace("cloudinary://", "").split("@")
        auth = parts[0].split(":")
        cloud_name = parts[1]
        
        files = {'file': ('product.jpg', photo_bytes)}
        response = requests.post(
            f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload",
            files=files,
            auth=(auth[0], auth[1])
        )
        
        if response.status_code == 200:
            context.user_data['image_url'] = response.json()['secure_url']
            await update.message.reply_text("✅ Фото загружено! Введите НАЗВАНИЕ.")
            return TITLE
        else:
            await update.message.reply_text(f"❌ Ошибка Cloudinary: {response.text}")
            return PHOTO
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")
        return PHOTO

async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    await update.message.reply_text("Введите ЦЕНУ (цифру).")
    return PRICE

async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['price'] = int(update.message.text)
        await update.message.reply_text("Введите КАТЕГОРИЮ.")
        return CATEGORY
    except:
        await update.message.reply_text("❌ Введите цифру.")
        return PRICE

async def get_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['category'] = update.message.text
    await update.message.reply_text("Введите ВКУСЫ через запятую (или 'нет').")
    return FLAVORS

async def get_flavors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flavors_text = "" if update.message.text.lower() == 'нет' else update.message.text
    data = {
        "title": context.user_data['title'], "price": context.user_data['price'],
        "category": context.user_data['category'], "image_url": context.user_data['image_url'], "flavors": flavors_text
    }
    
    # Отправка данных в Supabase
    url = f"{SUPABASE_URL}/rest/v1/products"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code in [200, 201]:
            await update.message.reply_text("✅ Товар добавлен!", reply_markup=main_keyboard())
        else:
            await update.message.reply_text(f"❌ Ошибка БД: {response.text}")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.", reply_markup=main_keyboard())
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_product_start, pattern="^add_product$")],
        states={
            PHOTO: [MessageHandler(filters.PHOTO | filters.TEXT, get_photo)],
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_category)],
            FLAVORS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_flavors)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))
    application.run_polling()

if __name__ == "__main__":
    main()
