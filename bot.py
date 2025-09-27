import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния диалога
(
    ADDRESS, WIDTH, HEIGHT, DEPTH, ELEMENTS, RS_COUNT, POSTS, SHELVES,
    SHELF_SIZES_CHOICE, CUSTOM_SHELF_SIZES, ROD, FALSE_PANEL, METAL_CUTTING,
    RS_TYPE, SHELF_TYPE, SGR_TIERS, SGR_ADJUSTMENT, BUMPER_INSTALLATION,
    BUMPER_TRANSFER, SECOND_INSTALLER, DISTANCE_KAD, WALL_MATERIAL,
    ROOF_MATERIAL, RS_PROFILE, FLOOR_COVERING, COLOR, SHELF_MATERIAL,
    OPTIONS
) = range(28)

# Прайс-лист
PRICE_LIST = {
    'Выход': 2000,
    'Доставка 1 заказ': 2000,
    'Вторая Р/С шире 2х метров': 1000,
    'Второй монтажник': 2000,
    'Боковая стенка. м/п': 364,
    'Крыша. м/п': 280,
    'Мягкая кровля. м/п': 180,
    'Задняя стенка. м2': 250,
    'Дно OSB. м/п': 350,
    'На дно квинтет (цинк). м/п': 100,
    'Перегородка. м/п': 300,
    'Фальш-панель. шт': 550,
    'Р/С (PD39, PD45, PD55 до 6 м2). шт': 300,
    'Р/С (AER44mS от 4 м2, PD55 от 6 м2). шт': 500,
    'Рама стеллажа + упор. м/п': 250,
    'Установка полок OSB. м/п': 100,
    'Установка полок металл. м/п': 160,
    'Резка металл, ламелей. шт': 30,
    'Рама стеллаж. шт': 400,
    'Установка ярусов. м/п': 80,
    'Подгонка по ширине на месте. Комплек': 500,
    'Штанга. шт': 200,
    'Отбойники (монтаж новых). комплек': 400,
    'Отбойники (перенос). комплек': 700,
    'LED светильник. шт': 200,
    'Электропривод (подключение) шт': 500,
    'Вент решетки (стенки) шт': 200,
    'Стойки для колес. шт': 500,
    'Выезд за МКАД более 10 км. (15Руб/км)': 15,
    'Высота шкафа 2,5-3 м': 500,
    'Высота шкафа 3м и более': 1000,
    'Фото заказчика на фоне шкафа. шт': 250,
    'Видеоотзыв': 750
}

MATERIALS = {
    'wall': ["Сэндвич-панель 40 мм", "Профлист С8А, 0,45 мм"],
    'roof': ["Сэндвич-панель 40 мм", "Профлист С8А, 0,45 мм", "Плита OSB + мягкая кровля"],
    'rs_profile': ["PD 45", "PD 55", "AR 40", "AER 44м/5", "AEG 56"],
    'floor': ["нет", "покраска", "лист оцинк. металла", "лист алюминия (квинтет)"],
    'color': ["Серебристый RAL 9006", "Бежевый RAL 1014", "Белый RAL 9003", "Антрацит RAL 7016", "Коричневый RAL 8014", "Коричневый RAL 8017", "Серый RAL 7038"],
    'shelf': ["Металл", "Плита OSB 22 мм", "СГР", "Навесной"]
}

OPTIONS_LIST = [
    "Вент. решетка",
    "LED светильник",
    "Электропривод",
    "Стойки для колес",
    "Фото заказчика",
    "Видеоотзыв"
]

# Все ваши async def функции остаются без изменений
# (start, get_address, get_width, ..., calculate_result, cancel)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я калькулятор зарплаты мастера Саши.\n\n"
        "Давайте начнём расчёт. Введите адрес монтажа:"
    )
    return ADDRESS

# ... (остальные функции get_address, get_width и т.д. - оставьте как есть)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Расчёт отменён.", reply_markup=ReplyKeyboardMarkup([["/start"]], one_time_keyboard=True))
    return ConversationHandler.END

def main():
    # ВРЕМЕННО для теста - вставьте ваш токен здесь
    TOKEN = "8131813785:AAEn4UkKQ2AhFzoz53YD-PRMwbTk..."  # ← ЗАМЕНИТЕ НА ВАШ ТОКЕН!
    
    print(f"🚀 BOT_TOKEN (length={len(TOKEN)}): '{TOKEN}'")
    
    if not TOKEN:
        print("❌ BOT_TOKEN не установлен!")
        return

    try:
        application = Application.builder().token(TOKEN).build()
        print("✅ Application создан успешно")
    except Exception as e:
        print(f"❌ Ошибка создания Application: {e}")
        return

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            WIDTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_width)],
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_height)],
            DEPTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_depth)],
            ELEMENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_elements)],
            RS_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_rs_count)],
            POSTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_posts)],
            SHELVES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_shelves)],
            SHELF_SIZES_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, shelf_sizes_choice)],
            CUSTOM_SHELF_SIZES: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_shelf_sizes)],
            ROD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_rod)],
            FALSE_PANEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_false_panel)],
            METAL_CUTTING: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_metal_cutting)],
            RS_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_rs_type)],
            SHELF_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_shelf_type)],
            SGR_TIERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_sgr_tiers)],
            SGR_ADJUSTMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_sgr_adjustment)],
            BUMPER_INSTALLATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bumper_installation)],
            BUMPER_TRANSFER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bumper_transfer)],
            SECOND_INSTALLER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_second_installer)],
            DISTANCE_KAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_distance_kad)],
            WALL_MATERIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_wall_material)],
            ROOF_MATERIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_roof_material)],
            RS_PROFILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_rs_profile)],
            FLOOR_COVERING: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_floor_covering)],
            COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_color)],
            SHELF_MATERIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_shelf_material)],
            OPTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_options)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)
    print("✅ Запуск polling...")
    application.run_polling()

if __name__ == '__main__':
    main()
