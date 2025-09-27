import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler, CallbackQueryHandler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния диалога
(
    ADDRESS,
    WIDTH,
    HEIGHT,
    DEPTH,
    ELEMENTS,
    RS_COUNT,
    POSTS,
    SHELVES,
    ROD,
    FALSE_PANEL,
    METAL_CUTTING,
    SHELF_SIZES_CHOICE,
    CUSTOM_SHELF_SIZES,
    RS_TYPE,
    SHELF_TYPE,
    SGR_TIERS,
    SGR_ADJUSTMENT,
    BUMPER_INSTALLATION,
    BUMPER_TRANSFER,
    SECOND_INSTALLER,
    HEIGHT_CONDITION,
    DISTANCE_KAD,
    WALL_MATERIAL,
    ROOF_MATERIAL,
    RS_PROFILE,
    FLOOR_COVERING,
    COLOR,
    SHELF_MATERIAL,
    OPTIONS,
    CALCULATE
) = range(30)

# Прайс-лист (как в вашем калькуляторе)
