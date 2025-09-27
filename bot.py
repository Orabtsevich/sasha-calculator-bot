import os
token = os.environ.get("BOT_TOKEN")
print("BOT_TOKEN is set:", token is not None, "length:", len(token) if token else 0)
if not token:
    raise RuntimeError("BOT_TOKEN is not set. Define env var or .env")
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я калькулятор зарплаты мастера Саши.\n\n"
        "Давайте начнём расчёт. Введите адрес монтажа:"
    )
    return ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['address'] = update.message.text
    await update.message.reply_text("Введите ширину шкафа (мм):")
    return WIDTH

async def get_width(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        width = int(update.message.text)
        if width < 0:
            raise ValueError
        context.user_data['width'] = width
        await update.message.reply_text("Введите высоту шкафа (мм):")
        return HEIGHT
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число (ширина в мм):")
        return WIDTH

async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        height = int(update.message.text)
        if height < 0:
            raise ValueError
        context.user_data['height'] = height
        await update.message.reply_text("Введите глубину шкафа (мм):")
        return DEPTH
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число (высота в мм):")
        return HEIGHT

async def get_depth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        depth = int(update.message.text)
        if depth < 0:
            raise ValueError
        context.user_data['depth'] = depth
        
        keyboard = [
            ["Крыша", "Правая стена", "Левая стена"],
            ["Задняя стенка", "Дно", "Далее"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await update.message.reply_text(
            "Выберите элементы шкафа (нажимайте по одному):",
            reply_markup=reply_markup
        )
        context.user_data['elements'] = []
        return ELEMENTS
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число (глубина в мм):")
        return DEPTH

async def get_elements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Далее":
        await update.message.reply_text("Количество Р/С:", reply_markup=ReplyKeyboardRemove())
        return RS_COUNT
    
    element_map = {
        "Крыша": "roof",
        "Правая стена": "right_wall",
        "Левая стена": "left_wall",
        "Задняя стенка": "back_wall",
        "Дно": "floor"
    }
    
    if text in element_map:
        context.user_data['elements'].append(element_map[text])
        await update.message.reply_text(f"Добавлено: {text}")
    else:
        await update.message.reply_text("Выберите элемент из списка.")
    
    return ELEMENTS

async def get_rs_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text)
        if count < 0:
            raise ValueError
        context.user_data['rs_count'] = count
        await update.message.reply_text("Количество стоек:")
        return POSTS
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число:")
        return RS_COUNT

async def get_posts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text)
        if count < 0:
            raise ValueError
        context.user_data['posts'] = count
        await update.message.reply_text("Количество полок:")
        return SHELVES
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число:")
        return POSTS

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
            await update.message.reply_text("Количество штанг:")
            return ROD
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число:")
        return SHELVES

async def shelf_sizes_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice == "Да, вводить вручную":
        context.user_data['custom_shelf_sizes'] = True
        context.user_data['shelf_widths'] = []
        context.user_data['current_shelf'] = 1
        await update.message.reply_text(f"Введите ширину полки 1 (мм):")
        return CUSTOM_SHELF_SIZES
    else:
        context.user_data['custom_shelf_sizes'] = False
        await update.message.reply_text("Количество штанг:")
        return ROD

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
            await update.message.reply_text(f"Введите ширину полки {current + 1} (мм):")
            return CUSTOM_SHELF_SIZES
        else:
            await update.message.reply_text("Количество штанг:")
            return ROD
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число (ширина в мм):")
        return CUSTOM_SHELF_SIZES

async def get_rod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text)
        if count < 0:
            raise ValueError
        context.user_data['rod'] = count
        await update.message.reply_text("Количество фальш-панелей:")
        return FALSE_PANEL
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число:")
        return ROD

async def get_false_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text)
        if count < 0:
            raise ValueError
        context.user_data['false_panel'] = count
        await update.message.reply_text("Резка металл, ламелей (шт):")
        return METAL_CUTTING
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число:")
        return FALSE_PANEL

async def get_metal_cutting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text)
        if count < 0:
            raise ValueError
        context.user_data['metal_cutting'] = count
        
        keyboard = [["До 6 м² (300 ₽/шт)"], ["Более 6 м² (500 ₽/шт)"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await update.message.reply_text("Выберите тип рольставней:", reply_markup=reply_markup)
        return RS_TYPE
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число:")
        return METAL_CUTTING

async def get_rs_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if "До 6 м²" in choice:
        context.user_data['rs_type'] = 'upTo6'
    else:
        context.user_data['rs_type'] = 'over6'
    
    keyboard = [["Без стеллажа"], ["Стандарт (неразборный)"], ["СГР (разборный)"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Выберите тип стеллажа:", reply_markup=reply_markup)
    return SHELF_TYPE

async def get_shelf_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if "Без стеллажа" in choice:
        context.user_data['shelf_type'] = 'none'
    elif "Стандарт" in choice:
        context.user_data['shelf_type'] = 'standard'
    else:
        context.user_data['shelf_type'] = 'sgr'
    
    if context.user_data['shelf_type'] == 'sgr' and context.user_data.get('shelves', 0) > 0:
        await update.message.reply_text("Установка ярусов? (да/нет):")
        return SGR_TIERS
    else:
        await update.message.reply_text("Установка отбойников? (да/нет):")
        return BUMPER_INSTALLATION

async def get_sgr_tiers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() in ['да', 'yes', 'y']:
        context.user_data['sgr_tiers'] = True
        await update.message.reply_text("Количество ярусов:")
        return SGR_ADJUSTMENT
    else:
        context.user_data['sgr_tiers'] = False
        await update.message.reply_text("Подгонка по ширине? (да/нет):")
        return SGR_ADJUSTMENT

async def get_sgr_adjustment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('sgr_tiers'):
        try:
            count = int(update.message.text)
            context.user_data['sgr_tiers_count'] = count
            await update.message.reply_text("Подгонка по ширине? (да/нет):")
            return BUMPER_INSTALLATION
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите число:")
            return SGR_ADJUSTMENT
    else:
        if update.message.text.lower() in ['да', 'yes', 'y']:
            context.user_data['sgr_adjustment'] = True
            await update.message.reply_text("Количество комплектов подгонки:")
            return BUMPER_INSTALLATION
        else:
            context.user_data['sgr_adjustment'] = False
            await update.message.reply_text("Установка отбойников? (да/нет):")
            return BUMPER_INSTALLATION

async def get_bumper_installation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('sgr_adjustment') and not context.user_data.get('sgr_tiers'):
        try:
            count = int(update.message.text)
            context.user_data['sgr_adjustment_count'] = count
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите число:")
            return BUMPER_INSTALLATION
    
    if update.message.text.lower() in ['да', 'yes', 'y']:
        context.user_data['bumper_installation'] = True
        await update.message.reply_text("Количество комплектов отбойников:")
        return BUMPER_TRANSFER
    else:
        context.user_data['bumper_installation'] = False
        await update.message.reply_text("Перенос отбойников? (да/нет):")
        return BUMPER_TRANSFER

async def get_bumper_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('bumper_installation'):
        try:
            count = int(update.message.text)
            context.user_data['bumper_installation_count'] = count
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите число:")
            return BUMPER_TRANSFER
    
    if update.message.text.lower() in ['да', 'yes', 'y']:
        context.user_data['bumper_transfer'] = True
        await update.message.reply_text("Количество комплектов переноса:")
        return SECOND_INSTALLER
    else:
        context.user_data['bumper_transfer'] = False
        await update.message.reply_text("Второй монтажник? (да/нет):")
        return SECOND_INSTALLER

async def get_second_installer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('bumper_transfer'):
        try:
            count = int(update.message.text)
            context.user_data['bumper_transfer_count'] = count
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите число:")
            return SECOND_INSTALLER
    
    if update.message.text.lower() in ['да', 'yes', 'y']:
        context.user_data['second_installer'] = True
    else:
        context.user_data['second_installer'] = False
    
    height = context.user_data['height']
    if height >= 3000:
        context.user_data['height_over_3000'] = True
        context.user_data['height_over_2500'] = False
    elif height >= 2500:
        context.user_data['height_over_2500'] = True
        context.user_data['height_over_3000'] = False
    else:
        context.user_data['height_over_2500'] = False
        context.user_data['height_over_3000'] = False
    
    await update.message.reply_text("Расстояние от КАД (км):")
    return DISTANCE_KAD

async def get_distance_kad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        distance = float(update.message.text)
        if distance < 0:
            raise ValueError
        context.user_data['distance_kad'] = distance
        
        keyboard = [[mat] for mat in MATERIALS['wall']]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await update.message.reply_text("Выберите материал для стенок:", reply_markup=reply_markup)
        return WALL_MATERIAL
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число (расстояние в км):")
        return DISTANCE_KAD

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
    
    keyboard = [[opt] for opt in OPTIONS_LIST] + [["Завершить выбор"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(
        "Выберите дополнительные опции (по одной):",
        reply_markup=reply_markup
    )
    context.user_data['selected_options'] = []
    return OPTIONS

async def get_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Завершить выбор":
        await calculate_result(update, context)
        return ConversationHandler.END
    
    if text in OPTIONS_LIST:
        context.user_data['selected_options'].append(text)
        await update.message.reply_text(f"Добавлено: {text}")
    else:
        await update.message.reply_text("Выберите опцию из списка.")
    
    return OPTIONS

async def calculate_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data
    results = []
    total = 0
    
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
        
        if data['floor_covering'] in ["лист оцинк. металла", "лист алюминия (квинтет)"]:
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
    
    shelves = data.get('shelves', 0)
    if shelves > 0 and data['shelf_type'] == 'standard':
        shelf_width = width / 1000
        if data.get('custom_shelf_sizes'):
            if data.get('shelf_widths'):
                avg_width = sum(data['shelf_widths']) / len(data['shelf_widths']) / 1000
                shelf_width = avg_width
        
        if data['shelf_material'] == 'Металл':
            shelf_cost = shelves * shelf_width * PRICE_LIST['Установка полок металл. м/п']
            results.append(f"Установка полок металл: {shelf_cost:.0f} ₽")
            total += shelf_cost
        elif data['shelf_material'] == 'Плита OSB 22 мм':
            shelf_cost = shelves * shelf_width * PRICE_LIST['Установка полок OSB. м/п']
            results.append(f"Установка полок OSB: {shelf_cost:.0f} ₽")
            total += shelf_cost
        
        frame_cost = shelves * shelf_width * PRICE_LIST['Рама стеллажа + упор. м/п']
        results.append(f"Рама стеллажа + упор: {frame_cost:.0f} ₽")
        total += frame_cost
    
    elif shelves > 0 and data['shelf_type'] == 'sgr':
        frame_cost = shelves * PRICE_LIST['Рама стеллаж. шт']
        results.append(f"Рама стеллажа СГР: {frame_cost} ₽")
        total += frame_cost
        
        if data.get('sgr_tiers'):
            tier_cost = (width / 1000) * data.get('sgr_tiers_count', 0) * PRICE_LIST['Установка ярусов. м/п']
            results.append(f"Установка ярусов СГР: {tier_cost:.0f} ₽")
            total += tier_cost
        
        if data.get('sgr_adjustment'):
            adj_cost = data.get('sgr_adjustment_count', 0) * PRICE_LIST['Подгонка по ширине на месте. Комплек']
            results.append(f"Подгонка по ширине СГР: {adj_cost} ₽")
            total += adj_cost
    
    selected_opts = data.get('selected_options', [])
    opt_counts = {
        "Вент. решетка": 1,
        "LED светильник": 1,
        "Электропривод": 1,
        "Стойки для колес": 1,
        "Фото заказчика": 1,
        "Видеоотзыв": 1
    }
    
    for opt in selected_opts:
        if opt == "Вент. решетка":
            cost = opt_counts[opt] * PRICE_LIST['Вент решетки (стенки) шт']
            results.append(f"Вент. решетка: {cost} ₽")
            total += cost
        elif opt == "LED светильник":
            cost = opt_counts[opt] * PRICE_LIST['LED светильник. шт']
            results.append(f"LED светильник: {cost} ₽")
            total += cost
        elif opt == "Электропривод":
            cost = opt_counts[opt] * PRICE_LIST['Электропривод (подключение) шт']
            results.append(f"Электропривод: {cost} ₽")
            total += cost
        elif opt == "Стойки для колес":
            cost = opt_counts[opt] * PRICE_LIST['Стойки для колес. шт']
            results.append(f"Стойки для колес: {cost} ₽")
            total += cost
        elif opt == "Фото заказчика":
            cost = opt_counts[opt] * PRICE_LIST['Фото заказчика на фоне шкафа. шт']
            results.append(f"Фото заказчика: {cost} ₽")
            total += cost
        elif opt == "Видеоотзыв":
            cost = opt_counts[opt] * PRICE_LIST['Видеоотзыв']
            results.append(f"Видеоотзыв: {cost} ₽")
            total += cost
    
    if data.get('second_installer'):
        total += PRICE_LIST['Второй монтажник']
        results.append("Второй монтажник: 2000 ₽")
    
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
    
    result_text = "📋 Результаты расчёта:\n\n" + "\n".join(results) + f"\n\n💰 ИТОГО: {total:.0f} ₽"
    await update.message.reply_text(result_text, reply_markup=ReplyKeyboardRemove())
    
    keyboard = [["/start"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Хотите сделать новый расчёт?", reply_markup=reply_markup)
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Расчёт отменён.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    TOKEN = os.environ.get("BOT_TOKEN")
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
    application.run_polling()

if __name__ == '__main__':
    main()
