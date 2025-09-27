import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния диалога
ADDRESS, WIDTH = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите адрес монтажа:")
    return ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['address'] = update.message.text
    await update.message.reply_text("Введите ширину шкафа (мм):")
    return WIDTH

async def get_width(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        width = int(update.message.text)
        await update.message.reply_text(f"Адрес: {context.user_data['address']}\nШирина: {width} мм\n\n✅ Данные получены!")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число.")
        return WIDTH

def main():
    TOKEN = os.environ.get("BOT_TOKEN")
    print(f"🚀 BOT_TOKEN (length={len(TOKEN)}): '{TOKEN}'")  # ДЕБАГ: покажет реальное значение

    if not TOKEN:
        print("❌ Переменная BOT_TOKEN пустая!")
        return

    if len(TOKEN) < 40:
        print("⚠️ Токен слишком короткий — возможно, неполный или содержит пробелы")
        return

    try:
        application = Application.builder().token(TOKEN).build()
    except Exception as e:
        print(f"❌ Ошибка при создании бота: {e}")
        return

    # Здесь добавляйте ваши ConversationHandler и другие обработчики
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            WIDTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_width)],
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_height)],
            # ... добавьте остальные состояния по аналогии ...
        },
        fallbacks=[]
    )

    application.add_handler(conv_handler)
    application.run_polling()
if __name__ == '__main__':
    main()
