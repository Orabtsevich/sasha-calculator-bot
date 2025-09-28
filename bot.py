import os
import logging
import urllib.parse
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Координаты офиса
OFFICE_COORDS = "59.973050,30.445787"
OFFICE_ADDRESS = "Санкт-Петербург, ул. Комсомола, 2к1"

# Состояния диалога
(
    ADDRESS, DISTANCE_KAD, WIDTH, HEIGHT, ELEMENTS, RS_COUNT, RS_WIDER_THAN_2M, 
    RS_TYPE, SHELVES, SHELF_SIZES_CHOICE, CUSTOM_SHELF_SIZES, SHELF_TYPE,
    WALL_MATERIAL, ROOF_MATERIAL, RS_PROFILE, FLOOR_COVERING, COLOR, SHELF_MATERIAL,
    ALL_OPTIONS, OPTION_COUNT, RESTART, SHOW_SUMMARY
) = range(22)

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

# Все опции в одном списке
ALL_OPTIONS_LIST = [
    "Штанга",
    "Фальш-панель", 
    "Резка металл/ламелей",
    "Установка отбойников",
    "Перенос отбойников", 
    "Второй монтажник",
    "Вент. решетка",
    "LED светильник",
    "Электропривод",
    "Стойки для колес",
    "Фото заказчика",
    "Видеоотзыв"
]

# Опции, которые НЕ требуют количества (только да/нет)
BOOLEAN_OPTIONS = ["Фото заказчика", "Видеоотзыв"]

# Соответствие опций и их цен в прайсе
OPTION_PRICE_KEYS = {
    "Штанга": "Штанга. шт",
    "Фальш-панель": "Фальш-панель. шт",
    "Резка металл/ламелей": "Резка металл, ламелей. шт",
    "Установка отбойников": "Отбойники (монтаж новых). комплек",
    "Перенос отбойников": "Отбойники (перенос). комплек",
    "Второй монтажник": "Второй монтажник",
    "Вент. решетка": "Вент решетки (стенки) шт",
    "LED светильник": "LED светильник. шт",
    "Электропривод": "Электропривод (подключение) шт",
    "Стойки для колес": "Стойки для колес. шт",
    "Фото заказчика": "Фото заказчика на фоне шкафа. шт",
    "Видеоотзыв": "Видеоотзыв"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я калькулятор зарплаты мастера Саши.\n\n"
        "Давайте начнём расчёт. Введите адрес монтажа:"
    )
    return ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['address'] = update.message.text
    
    # Создаем ссылку на Яндекс.Карты
    try:
        encoded_address = urllib.parse.quote(update.message.text)
        yandex_maps_url = f"https://yandex.ru/maps/?rtext={OFFICE_COORDS}~{encoded_address}&rtt=mt"
        
        await update.message.reply_text(
            f"📍 Адрес монтажа сохранен: {update.message.text}\n\n"
            f"🚗 [Построить маршрут от офиса до адреса монтажа]({yandex_maps_url})",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Ошибка при создании ссылки на карты: {e}")
        await update.message.reply_text(f"📍 Адрес монтажа сохранен: {update.message.text}")
    
    await update.message.reply_text("Введите расстояние от КАД в километрах:")
    return DISTANCE_KAD

async def get_distance_kad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        distance = float(update.message.text)
        if distance < 0:
            raise ValueError
        context.user_data['distance_kad'] = distance
        await update.message.reply_text("Введите ширину шкафа:")
        return WIDTH
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число:")
        return DISTANCE_KAD

async def get_width(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        width = int(update.message.text)
        if width < 0:
            raise ValueError
        context.user_data['width'] = width
        await update.message.reply_text("Введите высоту шкафа:")
        return HEIGHT
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число:")
        return WIDTH

async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        height = int(update.message.text)
        if height < 0:
            raise ValueError
        context.user_data['height'] = height
        
        # Обновляем флаги высоты
        if height >= 3000:
            context.user_data['height_over_3000'] = True
            context.user_data['height_over_2500'] = False
        elif height >= 2500:
            context.user_data['height_over_2500'] = True
            context.user_data['height_over_3000'] = False
        else:
            context.user_data['height_over_2500'] = False
            context.user_data['height_over_3000'] = False
        
        keyboard = [
            ["Крыша", "Правая стена", "Левая стена"],
            ["Задняя стенка", "Дно", "Далее"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            "Выберите элементы шкафа (нажимая по одному):",
            reply_markup=reply_markup
        )
        context.user_data['elements'] = []
        return ELEMENTS
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число:")
        return HEIGHT

async def get_elements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Далее":
        await update.message.reply_text(
            "Введите количество рольставен:", 
            reply_markup=ReplyKeyboardRemove()
        )
        return RS_COUNT
    
    element_map = {
        "Крыша": "roof",
        "Правая стена": "right_wall",
        "Левая стена": "left_wall",
        "Задняя стенка": "back_wall",
        "Дно": "floor"
    }
    
    if text in element_map:
        if element_map[text] not in context.user_data['elements']:
            context.user_data['elements'].append(element_map[text])
            message = f"Добавлено: {text}"
        else:
            message = f"Элемент '{text}' уже добавлен"
    else:
        message = "Выберите элемент из списка ниже."
    
    keyboard = [
        ["Крыша", "Правая стена", "Левая стена"],
        ["Задняя стенка", "Дно", "Далее"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False)
    await update.message.reply_text(
        f"{message}",
        reply_markup=reply_markup
    )
    
    return ELEMENTS

async def get_rs_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text)
        if count < 0:
            raise ValueError
        context.user_data['rs_count'] = count
        
        if count >= 2:
            # Если 2 или более рольставен, спрашиваем про вторую шире 2м
            keyboard = [["Да", "Нет"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text("Вторая рольставня шире 2 метров?", reply_markup=reply_markup)
            return RS_WIDER_THAN_2M
        else:
            # Если только одна рольставня, переходим к выбору типа
            keyboard = [["До 6 м² (300 ₽/шт)"], ["Более 6 м² (500 ₽/шт)"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text("Выберите тип рольставней:", reply_markup=reply_markup)
            return RS_TYPE
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число:")
        return RS_COUNT

async def get_rs_wider_than_2m(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Да":
        context.user_data['rs_wider_than_2m'] = True
    else:
        context.user_data['rs_wider_than_2m'] = False
    
    keyboard = [["До 6 м² (300 ₽/шт)"], ["Более 6 м² (500 ₽/шт)"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Выберите тип рольставней:", reply_markup=reply_markup)
    return RS_TYPE

async def get_rs_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if "До 6 м²" in choice:
        context.user_data['rs_type'] = 'upTo6'
    else:
        context.user_data['rs_type'] = 'over6'
    
    await update.message.reply_text("Введите количество полок:")
    return SHELVES

async def get_shelves(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text)
        if count < 0:
            raise ValueError
        context.user_data['shelves'] = count
        
        if count > 0:
            keyboard = [["Да, вводить вручную"], ["Нет, полки = ширине шкафа"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text(
                "Полки не в размер шкафа?",
                reply_markup=reply_markup
            )
            return SHELF_SIZES_CHOICE
        else:
            context.user_data['custom_shelf_sizes'] = False
            # Переходим сразу к выбору типа стеллажа
            keyboard = [["Без стеллажа"], ["Стандарт (неразборный)"], ["СГР (разборный)"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text("Выберите тип стеллажа:", reply_markup=reply_markup)
            return SHELF_TYPE
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число:")
        return SHELVES

async def shelf_sizes_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice == "Да, вводить вручную":
        context.user_data['custom_shelf_sizes'] = True
        context.user_data['shelf_widths'] = []
        context.user_data['current_shelf'] = 1
        await update.message.reply_text(f"Введите ширину полки 1:")
        return CUSTOM_SHELF_SIZES
    else:
        context.user_data['custom_shelf_sizes'] = False
        keyboard = [["Без стеллажа"], ["Стандарт (неразборный)"], ["СГР (разборный)"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await update.message.reply_text("Выберите тип стеллажа:", reply_markup=reply_markup)
        return SHELF_TYPE

async def custom_shelf_sizes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        width = int(update.message.text)
        if width < 0:
            raise ValueError
        context.user_data['shelf_widths'].append(width)
        
        current = context.user_data['current_shelf']
        total = context.user_data['shelves']
        
        if current < total:
            context.user_data['current_shelf'] += 1
            await update.message.reply_text(f"Введите ширину полки {current + 1}:")
            return CUSTOM_SHELF_SIZES
        else:
            keyboard = [["Без стеллажа"], ["Стандарт (неразборный)"], ["СГР (разборный)"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text("Выберите тип стеллажа:", reply_markup=reply_markup)
            return SHELF_TYPE
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число:")
        return CUSTOM_SHELF_SIZES

async def get_shelf_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if "Без стеллажа" in choice:
        context.user_data['shelf_type'] = 'none'
    elif "Стандарт" in choice:
        context.user_data['shelf_type'] = 'standard'
    else:
        context.user_data['shelf_type'] = 'sgr'
    
    # Переходим к выбору материалов
    keyboard = [[mat] for mat in MATERIALS['wall']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Выберите материал для стенок:", reply_markup=reply_markup)
    return WALL_MATERIAL

async def get_wall_material(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['wall_material'] = update.message.text
    keyboard = [[mat] for mat in MATERIALS['roof']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Выберите материал для крыши:", reply_markup=reply_markup)
    return ROOF_MATERIAL

async def get_roof_material(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['roof_material'] = update.message.text
    keyboard = [[mat] for mat in MATERIALS['rs_profile']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Выберите профиль Р/С:", reply_markup=reply_markup)
    return RS_PROFILE

async def get_rs_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['rs_profile'] = update.message.text
    keyboard = [[mat] for mat in MATERIALS['floor']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Выберите покрытие дна:", reply_markup=reply_markup)
    return FLOOR_COVERING

async def get_floor_covering(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['floor_covering'] = update.message.text
    keyboard = [[mat] for mat in MATERIALS['color']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Выберите цвет:", reply_markup=reply_markup)
    return COLOR

async def get_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['color'] = update.message.text
    keyboard = [[mat] for mat in MATERIALS['shelf']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Выберите материал полок:", reply_markup=reply_markup)
    return SHELF_MATERIAL

async def get_shelf_material(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['shelf_material'] = update.message.text
    
    # Теперь показываем один большой список всех опций
    keyboard = [[opt] for opt in ALL_OPTIONS_LIST] + [["✅ Завершить выбор"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False)
    await update.message.reply_text(
        "📋 Выберите дополнительные опции и введите их количество:",
        reply_markup=reply_markup
    )
    context.user_data['selected_options'] = {}
    return ALL_OPTIONS

async def get_all_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "✅ Завершить выбор":
        # Показываем сводку перед финальным расчетом
        keyboard = [["Показать результат", "Редактировать данные"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await update.message.reply_text(
            "Все данные собраны! Что хотите сделать?",
            reply_markup=reply_markup
        )
        return SHOW_SUMMARY
    
    if text in ALL_OPTIONS_LIST:
        if text in BOOLEAN_OPTIONS:
            # Для булевых опций просто добавляем как 1
            context.user_data['selected_options'][text] = 1
            # Показываем клавиатуру снова
            keyboard = [[opt] for opt in ALL_OPTIONS_LIST] + [["✅ Завершить выбор"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False)
            await update.message.reply_text(
                f"✅ Добавлено: {text} (1 шт)",
                reply_markup=reply_markup
            )
            return ALL_OPTIONS
        else:
            # Для ВСЕХ остальных опций запрашиваем количество
            context.user_data['current_option'] = text
            await update.message.reply_text(f"🔢 Введите количество '{text}':")
            return OPTION_COUNT
    else:
        await update.message.reply_text("Выберите опцию из списка.")
        return ALL_OPTIONS

async def get_option_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text)
        if count < 0:
            raise ValueError
        
        current_option = context.user_data['current_option']
        context.user_data['selected_options'][current_option] = count
        
        # Показываем клавиатуру снова для выбора следующей опции
        keyboard = [[opt] for opt in ALL_OPTIONS_LIST] + [["✅ Завершить выбор"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            f"✅ Добавлено: {current_option} - {count} шт",
            reply_markup=reply_markup
        )
        return ALL_OPTIONS
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число (только цифры):")
        return OPTION_COUNT

async def show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice == "Показать результат":
        await calculate_result(update, context)
        return ConversationHandler.END
    elif choice == "Редактировать данные":
        await show_edit_menu(update, context)
        return RESTART

async def show_edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает текущие данные и предлагает ввести новое значение для любого поля"""
    data = context.user_data
    
    summary = "📋 Текущие данные:\n\n"
    
    # Основные параметры
    summary += f"📍 Адрес: {data.get('address', 'Не указан')}\n"
    summary += f"🚗 Расстояние от КАД: {data.get('distance_kad', 0)} км\n"
    summary += f"↔️ Ширина шкафа: {data.get('width', 0)} мм\n"
    summary += f"↕️ Высота шкафа: {data.get('height', 0)} мм\n"
    
    # Элементы шкафа
    if data.get('elements'):
        elements_map = {'roof': 'Крыша', 'right_wall': 'Правая стена', 'left_wall': 'Левая стена', 'back_wall': 'Задняя стенка', 'floor': 'Дно'}
        elements_str = ', '.join([elements_map.get(e, e) for e in data['elements']])
        summary += f"📦 Элементы: {elements_str}\n"
    
    # Рольставни
    summary += f"🚪 Рольставни: {data.get('rs_count', 0)} шт\n"
    if data.get('rs_wider_than_2m'):
        summary += "📏 Вторая Р/С шире 2м: Да\n"
    if data.get('rs_type'):
        summary += f"🏷️ Тип Р/С: {'До 6 м²' if data['rs_type'] == 'upTo6' else 'Более 6 м²'}\n"
    
    # Полки и стеллаж
    summary += f"🧱 Полки: {data.get('shelves', 0)} шт\n"
    if data.get('shelf_type'):
        shelf_types = {'none': 'Без стеллажа', 'standard': 'Стандарт', 'sgr': 'СГР'}
        summary += f"🪜 Тип стеллажа: {shelf_types.get(data['shelf_type'], data['shelf_type'])}\n"
    
    # Материалы
    if data.get('wall_material'):
        summary += f"🧱 Материал стенок: {data['wall_material']}\n"
    if data.get('roof_material'):
        summary += f"🏠 Материал крыши: {data['roof_material']}\n"
    if data.get('rs_profile'):
        summary += f"🚪 Профиль Р/С: {data['rs_profile']}\n"
    if data.get('floor_covering'):
        summary += f"🪵 Покрытие дна: {data['floor_covering']}\n"
    if data.get('color'):
        summary += f"🎨 Цвет: {data['color']}\n"
    if data.get('shelf_material'):
        summary += f"📦 Материал полок: {data['shelf_material']}\n"
    
    # Дополнительные опции
    if data.get('selected_options'):
        options_str = ', '.join([f"{opt} ({count})" if count > 1 else opt 
                               for opt, count in data['selected_options'].items()])
        summary += f"➕ Доп. опции: {options_str}\n"
    
    summary += "\nЧтобы изменить любое значение, просто введите его в формате:\n"
    summary += "поле = новое значение\n\n"
    summary += "Примеры:\n"
    summary += "ширина = 2500\n"
    summary += "адрес = Новый адрес\n"
    summary += "второй монтажник = 2\n\n"
    summary += "Или введите 'готово' для показа результата."
    
    await update.message.reply_text(summary)
    return RESTART

async def handle_edit_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    
    if text == "готово":
        await calculate_result(update, context)
        return ConversationHandler.END
    
    # Парсим ввод в формате "поле = значение"
    if "=" in text:
        try:
            field_part, value_part = text.split("=", 1)
            field = field_part.strip()
            value = value_part.strip()
            
            # Числовые поля
            if field in ['расстояние', 'расстояние от кад']:
                context.user_data['distance_kad'] = float(value)
                await update.message.reply_text("✅ Расстояние обновлено!")
            elif field in ['ширина', 'ширина шкафа']:
                context.user_data['width'] = int(value)
                await update.message.reply_text("✅ Ширина обновлена!")
            elif field in ['высота', 'высота шкафа']:
                height = int(value)
                context.user_data['height'] = height
                # Обновляем флаги высоты
                if height >= 3000:
                    context.user_data['height_over_3000'] = True
                    context.user_data['height_over_2500'] = False
                elif height >= 2500:
                    context.user_data['height_over_2500'] = True
                    context.user_data['height_over_3000'] = False
                else:
                    context.user_data['height_over_2500'] = False
                    context.user_data['height_over_3000'] = False
                await update.message.reply_text("✅ Высота обновлена!")
            elif field == 'адрес':
                context.user_data['address'] = value
                await update.message.reply_text("✅ Адрес обновлен!")
            else:
                # Попробуем найти опцию для редактирования
                for opt in ALL_OPTIONS_LIST:
                    if field.lower() in opt.lower():
                        try:
                            count = int(value)
                            context.user_data['selected_options'][opt] = count
                            await update.message.reply_text(f"✅ {opt} обновлено на {count} шт!")
                            await show_edit_menu(update, context)
                            return RESTART
                        except ValueError:
                            await update.message.reply_text("Введите число для количества.")
                            await show_edit_menu(update, context)
                            return RESTART
                
                await update.message.reply_text("Неизвестное поле. Используйте: адрес, расстояние, ширина, высота, или название опции.")
            
            # Показываем обновленное меню
            await show_edit_menu(update, context)
            return RESTART
            
        except (ValueError, IndexError):
            await update.message.reply_text("Ошибка формата. Используйте: поле = значение")
            await show_edit_menu(update, context)
            return RESTART
    else:
        await update.message.reply_text("Используйте формат: поле = значение\nИли введите 'готово'")
        await show_edit_menu(update, context)
        return RESTART

async def restart_calculation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Начать новый расчёт":
        return await start(update, context)
    else:
        await update.message.reply_text("Пожалуйста, используйте кнопку для нового расчёта.")
        return RESTART

async def calculate_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data
    results = []
    total = 0
    
    # Добавляем адрес в начало результатов
    address = data.get('address', 'Не указан')
    results.append(f"📍 Адрес монтажа: {address}")
    results.append("")
    
    results.append("Выход на работу: 2000 ₽")
    total += 2000
    results.append("Доставка 1 заказ: 2000 ₽")
    total += 2000
    
    elements = data.get('elements', [])
    width = data['width']
    height = data['height']
    
    if 'right_wall' in elements or 'left_wall' in elements:
        wall_count = sum(1 for e in ['right_wall', 'left_wall'] if e in elements)
        wall_length = height / 1000
        wall_cost = wall_count * wall_length * PRICE_LIST['Боковая стенка. м/п']
        results.append(f"Боковые стенки ({wall_count} шт): {wall_cost:.0f} ₽")
        total += wall_cost
    
    if 'roof' in elements:
        roof_length = width / 1000
        roof_cost = roof_length * PRICE_LIST['Крыша. м/п']
        results.append(f"Крыша: {roof_cost:.0f} ₽")
        total += roof_cost
    
    if 'back_wall' in elements:
        back_area = (width * height) / 1000000
        back_cost = back_area * PRICE_LIST['Задняя стенка. м2']
        results.append(f"Задняя стенка: {back_cost:.0f} ₽")
        total += back_cost
    
    if 'floor' in elements:
        floor_length = width / 1000
        floor_cost = floor_length * PRICE_LIST['Дно OSB. м/п']
        results.append(f"Дно OSB: {floor_cost:.0f} ₽")
        total += floor_cost
        
        if data.get('floor_covering') in ["лист оцинк. металла", "лист алюминия (квинтет)"]:
            covering_cost = floor_length * PRICE_LIST['На дно квинтет (цинк). м/п']
            results.append(f"На дно квинтет: {covering_cost:.0f} ₽")
            total += covering_cost
    
    rs_count = data.get('rs_count', 0)
    if rs_count > 0:
        if data['rs_type'] == 'upTo6':
            rs_cost = rs_count * PRICE_LIST['Р/С (PD39, PD45, PD55 до 6 м2). шт']
            results.append(f"Р/С до 6 м² ({rs_count} шт): {rs_cost} ₽")
        else:
            rs_cost = rs_count * PRICE_LIST['Р/С (AER44mS от 4 м2, PD55 от 6 м2). шт']
            results.append(f"Р/С более 6 м² ({rs_count} шт): {rs_cost} ₽")
        total += rs_cost
    
    # Добавляем стоимость второй рольставни шире 2м, если применимо
    if data.get('rs_wider_than_2m', False):
        total += PRICE_LIST['Вторая Р/С шире 2х метров']
        results.append("Вторая Р/С шире 2х метров: 1000 ₽")
    
    shelves = data.get('shelves', 0)
    if shelves > 0 and data['shelf_type'] == 'standard':
        # Расчет стоимости полок и рамы
        total_shelf_cost = 0
        total_frame_cost = 0
        
        if data.get('custom_shelf_sizes') and data.get('shelf_widths'):
            # Обрабатываем каждую полку отдельно
            for i, width_mm in enumerate(data['shelf_widths']):
                width_m = width_mm / 1000  # переводим в метры
                
                if data['shelf_material'] == 'Металл':
                    shelf_cost = width_m * PRICE_LIST['Установка полок металл. м/п']
                elif data['shelf_material'] == 'Плита OSB 22 мм':
                    shelf_cost = width_m * PRICE_LIST['Установка полок OSB. м/п']
                
                frame_cost = width_m * PRICE_LIST['Рама стеллажа + упор. м/п']
                
                total_shelf_cost += shelf_cost
                total_frame_cost += frame_cost
        
        else:
            # Все полки = ширине шкафа
            shelf_width_m = width / 1000
            for i in range(shelves):
                if data['shelf_material'] == 'Металл':
                    shelf_cost = shelf_width_m * PRICE_LIST['Установка полок металл. м/п']
                elif data['shelf_material'] == 'Плита OSB 22 мм':
                    shelf_cost = shelf_width_m * PRICE_LIST['Установка полок OSB. м/п']
                
                frame_cost = shelf_width_m * PRICE_LIST['Рама стеллажа + упор. м/п']
                
                total_shelf_cost += shelf_cost
                total_frame_cost += frame_cost
        
        # Добавляем в результаты
        if data['shelf_material'] == 'Металл':
            results.append(f"Установка полок металл: {total_shelf_cost:.0f} ₽")
        else:
            results.append(f"Установка полок OSB: {total_shelf_cost:.0f} ₽")
        total += total_shelf_cost
        
        results.append(f"Рама стеллажа + упор: {total_frame_cost:.0f} ₽")
        total += total_frame_cost
    
    elif shelves > 0 and data['shelf_type'] == 'sgr':
        frame_cost = shelves * PRICE_LIST['Рама стеллаж. шт']
        results.append(f"Рама стеллажа СГР: {frame_cost} ₽")
        total += frame_cost
        
        if data.get('sgr_tiers'):
            tier_cost = (width / 1000) * data.get('sgr_tiers_count', 0) * PRICE_LIST['Установка ярусов. м/п']
            results.append(f"Установка ярусов СГР: {tier_cost:.0f} ₽")
            total += tier_cost
    
    selected_opts = data.get('selected_options', {})
    for opt, count in selected_opts.items():
        price_key = OPTION_PRICE_KEYS[opt]
        cost = count * PRICE_LIST[price_key]
        if opt in BOOLEAN_OPTIONS:
            results.append(f"{opt}: {cost} ₽")
        else:
            results.append(f"{opt} ({count} шт): {cost} ₽")
        total += cost
    
    if data.get('height_over_2500'):
        total += PRICE_LIST['Высота шкафа 2,5-3 м']
        results.append("Высота 2,5-3 м: 500 ₽")
    elif data.get('height_over_3000'):
        total += PRICE_LIST['Высота шкафа 3м и более']
        results.append("Высота 3м и более: 1000 ₽")
    
    distance = data.get('distance_kad', 0)
    if distance > 0:
        delivery_cost = distance * PRICE_LIST['Выезд за МКАД более 10 км. (15Руб/км)']
        results.append(f"Выезд за КАД ({distance} км): {delivery_cost:.0f} ₽")
        total += delivery_cost
    
    # Используем жирный шрифт и эмодзи для итоговой суммы
    result_text = "📋 Результаты расчёта:\n\n" + "\n".join(results) + f"\n\n💰 *ИТОГО: {total:.0f} ₽*"
    await update.message.reply_text(result_text, reply_markup=ReplyKeyboardRemove(), parse_mode='Markdown')
    
    # Добавляем ссылку на маршрут в конце результатов
    try:
        encoded_address = urllib.parse.quote(data.get('address', ''))
        yandex_maps_url = f"https://yandex.ru/maps/?rtext={OFFICE_COORDS}~{encoded_address}&rtt=mt"
        await update.message.reply_text(
            f"🚗 [Построить маршрут от офиса до адреса монтажа]({yandex_maps_url})",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Ошибка при создании ссылки на карты в результатах: {e}")
    
    keyboard = [["Начать новый расчёт"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Хотите сделать новый расчёт?", reply_markup=reply_markup)
    
    return RESTART

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Расчёт отменён.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    TOKEN = "8258670576:AAEeT3bQfOQ1Euqdbw3jVhEXVETmyQ43iXs"
    print(f"🚀 BOT_TOKEN (length={len(TOKEN) if TOKEN else 0}): '{TOKEN}'")

    if not TOKEN:
        print("❌ Переменная BOT_TOKEN не установлена!")
        return

    try:
        application = Application.builder().token(TOKEN).build()
    except Exception as e:
        print(f"❌ Ошибка при создании бота: {e}")
        return

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            DISTANCE_KAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_distance_kad)],
            WIDTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_width)],
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_height)],
            ELEMENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_elements)],
            RS_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_rs_count)],
            RS_WIDER_THAN_2M: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_rs_wider_than_2m)],
            RS_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_rs_type)],
            SHELVES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_shelves)],
            SHELF_SIZES_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, shelf_sizes_choice)],
            CUSTOM_SHELF_SIZES: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_shelf_sizes)],
            SHELF_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_shelf_type)],
            WALL_MATERIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_wall_material)],
            ROOF_MATERIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_roof_material)],
            RS_PROFILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_rs_profile)],
            FLOOR_COVERING: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_floor_covering)],
            COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_color)],
            SHELF_MATERIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_shelf_material)],
            ALL_OPTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_all_options)],
            OPTION_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_option_count)],
            SHOW_SUMMARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, show_summary)],
            RESTART: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_input)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
