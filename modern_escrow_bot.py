import asyncio
import logging
import random
import qrcode
import io
import base64
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database_manager import DatabaseManager
from config import BOT_TOKEN, MYSQL_CONFIG

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Состояния FSM
class CaptchaStates(StatesGroup):
    waiting_captcha = State()

class DealStates(StatesGroup):
    waiting_amount = State()
    waiting_condition = State()
    waiting_password = State()

class JoinDealStates(StatesGroup):
    waiting_password = State()

# Константы
CAPTCHA_ANIMALS = ["🐱", "🐶", "🐺", "🦊", "🐻", "🐨", "🐯", "🦁", "🐸", "🐧"]
TRC20_ADDRESS = "TREBy39rXoWMTfuZcobHNR49EKfnXPbbdE"
TON_ADDRESS = "UQC337PVpq0748IOjdbQWJlVjDMIdkENC5iimBrexCikKyYo"

class ModernEscrowBot:
    def __init__(self):
        self.db = DatabaseManager()
        
    def generate_captcha_keyboard(self, correct_animal: str) -> InlineKeyboardMarkup:
        """Генерирует клавиатуру капчи с 6 вариантами животных"""
        animals = random.sample(CAPTCHA_ANIMALS, 5)
        if correct_animal not in animals:
            animals[random.randint(0, 4)] = correct_animal
        
        random.shuffle(animals)
        
        builder = InlineKeyboardBuilder()
        for i in range(0, len(animals), 3):
            row = animals[i:i+3]
            for animal in row:
                builder.button(
                    text=animal,
                    callback_data=f"captcha_{animal}_{correct_animal}"
                )
        builder.adjust(3, 2, 1)
        return builder.as_markup()

    def get_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Главное меню с 4 командами"""
        builder = InlineKeyboardBuilder()
        builder.button(text="💼 Создать сделку", callback_data="create_deal")
        builder.button(text="👤 Профиль", callback_data="profile")
        builder.button(text="📋 Мои сделки", callback_data="my_deals")
        builder.button(text="🆘 Поддержка", callback_data="support")
        builder.adjust(2, 2)
        return builder.as_markup()

    def get_deal_cancel_keyboard(self, deal_id: str) -> InlineKeyboardMarkup:
        """Клавиатура с кнопкой отмены сделки"""
        builder = InlineKeyboardBuilder()
        builder.button(text="❌ Отменить сделку", callback_data=f"cancel_deal_{deal_id}")
        return builder.as_markup()

    def generate_qr_code(self, address: str, amount: float = None) -> BufferedInputFile:
        """Генерирует QR код для адреса кошелька"""
        qr_data = address
        if amount:
            qr_data = f"{address}?amount={amount}"
            
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        bio = io.BytesIO()
        img.save(bio, 'PNG')
        bio.seek(0)
        
        return BufferedInputFile(bio.read(), filename=f"qr_{address[:10]}.png")

    async def send_payment_info(self, chat_id: int, amount: float):
        """Отправляет информацию для оплаты с QR кодами"""
        # TRC20 USDT
        trc20_qr = self.generate_qr_code(TRC20_ADDRESS, amount)
        await bot.send_photo(
            chat_id=chat_id,
            photo=trc20_qr,
            caption=f"💳 <b>Оплата TRC20 USDT</b>\n\n"
                   f"💰 Сумма: <code>{amount}</code> USDT\n"
                   f"🏦 Адрес: <code>{TRC20_ADDRESS}</code>\n\n"
                   f"⚠️ Внимание! Отправляйте точную сумму на указанный адрес",
            parse_mode="HTML"
        )
        
        # TON
        ton_qr = self.generate_qr_code(TON_ADDRESS, amount)
        await bot.send_photo(
            chat_id=chat_id,
            photo=ton_qr,
            caption=f"💎 <b>Оплата TON</b>\n\n"
                   f"💰 Сумма: <code>{amount}</code> TON\n"
                   f"🏦 Адрес: <code>{TON_ADDRESS}</code>\n\n"
                   f"⚠️ Внимание! Отправляйте точную сумму на указанный адрес",
            parse_mode="HTML"
        )

# Инициализация бота
escrow_bot = ModernEscrowBot()

@dp.message(CommandStart())
async def start_command(message: types.Message, state: FSMContext):
    """Обработка команды /start с капчей"""
    user_id = message.from_user.id
    
    # Проверяем, зарегистрирован ли пользователь
    if await escrow_bot.db.is_user_registered(user_id):
        await message.answer(
            "🎉 <b>Добро пожаловать обратно!</b>\n\n"
            "Выберите действие из меню ниже:",
            reply_markup=escrow_bot.get_main_menu_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Генерируем капчу
    correct_animal = random.choice(CAPTCHA_ANIMALS)
    await state.update_data(correct_animal=correct_animal)
    await state.set_state(CaptchaStates.waiting_captcha)
    
    await message.answer(
        f"🤖 <b>Добро пожаловать в Modern Escrow Bot!</b>\n\n"
        f"🔐 Для продолжения пройдите верификацию:\n"
        f"Выберите животное: <b>{correct_animal}</b>",
        reply_markup=escrow_bot.generate_captcha_keyboard(correct_animal),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("captcha_"))
async def handle_captcha(callback: types.CallbackQuery, state: FSMContext):
    """Обработка капчи"""
    data = callback.data.split("_")
    selected_animal = data[1]
    correct_animal = data[2]
    
    if selected_animal == correct_animal:
        # Капча пройдена успешно
        user_id = callback.from_user.id
        username = callback.from_user.username or "NoUsername"
        first_name = callback.from_user.first_name or "User"
        
        # Регистрируем пользователя
        await escrow_bot.db.register_user(user_id, username, first_name)
        await state.clear()
        
        await callback.message.edit_text(
            "✅ <b>Верификация пройдена успешно!</b>\n\n"
            "🎉 Добро пожаловать в Modern Escrow Bot 2025!\n"
            "Выберите действие из меню ниже:",
            reply_markup=escrow_bot.get_main_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Неверный выбор! Попробуйте еще раз.", show_alert=True)

@dp.callback_query(F.data == "create_deal")
async def create_deal_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало создания сделки"""
    user_id = callback.from_user.id
    
    # Проверяем, есть ли активные сделки
    active_deal = await escrow_bot.db.get_active_deal_by_creator(user_id)
    if active_deal:
        await callback.answer("❌ У вас уже есть активная сделка!", show_alert=True)
        return
    
    await state.set_state(DealStates.waiting_amount)
    await callback.message.edit_text(
        "💰 <b>Создание новой сделки</b>\n\n"
        "Введите сумму сделки в USDT:",
        parse_mode="HTML"
    )

@dp.message(DealStates.waiting_amount)
async def process_deal_amount(message: types.Message, state: FSMContext):
    """Обработка суммы сделки"""
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
        
        await state.update_data(amount=amount)
        await state.set_state(DealStates.waiting_condition)
        
        await message.answer(
            f"💰 Сумма: <b>{amount} USDT</b>\n\n"
            f"📝 Теперь введите условие сделки:",
            parse_mode="HTML"
        )
    except ValueError:
        await message.answer("❌ Неверный формат! Введите числовое значение:")

@dp.message(DealStates.waiting_condition)
async def process_deal_condition(message: types.Message, state: FSMContext):
    """Обработка условия сделки"""
    condition = message.text.strip()
    if len(condition) < 10:
        await message.answer("❌ Условие слишком короткое! Минимум 10 символов:")
        return
    
    await state.update_data(condition=condition)
    await state.set_state(DealStates.waiting_password)
    
    await message.answer(
        "🔐 <b>Почти готово!</b>\n\n"
        "Введите пароль для присоединения к сделке:\n"
        "(минимум 4 символа)",
        parse_mode="HTML"
    )

@dp.message(DealStates.waiting_password)
async def process_deal_password(message: types.Message, state: FSMContext):
    """Обработка пароля и создание сделки"""
    password = message.text.strip()
    if len(password) < 4:
        await message.answer("❌ Пароль слишком короткий! Минимум 4 символа:")
        return
    
    # Получаем данные сделки
    data = await state.get_data()
    amount = data['amount']
    condition = data['condition']
    
    # Создаем сделку в БД
    deal_id = str(uuid.uuid4())
    user_id = message.from_user.id
    
    success = await escrow_bot.db.create_deal(
        deal_id=deal_id,
        creator_id=user_id,
        amount=amount,
        condition=condition,
        password=password
    )
    
    if success:
        await state.clear()
        
        # Создаем ссылку для присоединения
        bot_username = (await bot.get_me()).username
        join_link = f"https://t.me/{bot_username}?start=join_{deal_id}"
        
        await message.answer(
            "✅ <b>Сделка создана успешно!</b>\n\n"
            f"🆔 ID сделки: <code>{deal_id}</code>\n"
            f"💰 Сумма: <b>{amount} USDT</b>\n"
            f"📝 Условие: {condition}\n\n"
            f"🔗 <b>Ссылка для присоединения:</b>\n"
            f"<code>{join_link}</code>\n\n"
            f"⚠️ Панель управления заблокирована до завершения сделки",
            reply_markup=escrow_bot.get_deal_cancel_keyboard(deal_id),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Ошибка создания сделки. Попробуйте позже.")

@dp.callback_query(F.data == "profile")
async def show_profile(callback: types.CallbackQuery):
    """Показ профиля пользователя"""
    user_id = callback.from_user.id
    
    # Проверяем блокировку
    if await escrow_bot.db.is_user_in_active_deal(user_id):
        await callback.answer("❌ Панель заблокирована до завершения сделки!", show_alert=True)
        return
    
    user_stats = await escrow_bot.db.get_user_stats(user_id)
    
    await callback.message.edit_text(
        f"👤 <b>Ваш профиль</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"👤 Имя: {callback.from_user.first_name}\n"
        f"📊 Завершенных сделок: {user_stats['completed_deals']}\n"
        f"💰 Общий объем: {user_stats['total_volume']} USDT\n"
        f"📅 Дата регистрации: {user_stats['registration_date']}\n\n"
        f"⬅️ Назад в меню",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]
        ]),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "my_deals")
async def show_my_deals(callback: types.CallbackQuery):
    """Показ сделок пользователя"""
    user_id = callback.from_user.id
    
    # Проверяем блокировку
    if await escrow_bot.db.is_user_in_active_deal(user_id):
        await callback.answer("❌ Панель заблокирована до завершения сделки!", show_alert=True)
        return
    
    deals = await escrow_bot.db.get_user_deals(user_id)
    
    if not deals:
        text = "📋 <b>Ваши сделки</b>\n\nУ вас пока нет сделок."
    else:
        text = "📋 <b>Ваши сделки</b>\n\n"
        for deal in deals:
            status_emoji = "🟢" if deal['status'] == 'completed' else "🟡" if deal['status'] == 'active' else "🔴"
            text += f"{status_emoji} {deal['amount']} USDT - {deal['status']}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]
        ]),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "support")
async def show_support(callback: types.CallbackQuery):
    """Показ поддержки"""
    user_id = callback.from_user.id
    
    # Проверяем блокировку
    if await escrow_bot.db.is_user_in_active_deal(user_id):
        await callback.answer("❌ Панель заблокирована до завершения сделки!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🆘 <b>Поддержка</b>\n\n"
        "📞 Контакты службы поддержки:\n"
        "• Telegram: @support_admin\n"
        "• Email: support@escrowbot.com\n\n"
        "⏰ Время работы: 24/7\n"
        "⚡ Среднее время ответа: 15 минут",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]
        ]),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "🎉 <b>Modern Escrow Bot 2025</b>\n\n"
        "Выберите действие из меню ниже:",
        reply_markup=escrow_bot.get_main_menu_keyboard(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("cancel_deal_"))
async def cancel_deal(callback: types.CallbackQuery):
    """Отмена сделки"""
    deal_id = callback.data.replace("cancel_deal_", "")
    user_id = callback.from_user.id
    
    # Проверяем, что пользователь создатель сделки
    deal = await escrow_bot.db.get_deal(deal_id)
    if not deal or deal['creator_id'] != user_id:
        await callback.answer("❌ Вы не можете отменить эту сделку!", show_alert=True)
        return
    
    # Отменяем сделку
    success = await escrow_bot.db.cancel_deal(deal_id)
    if success:
        await callback.message.edit_text(
            "✅ <b>Сделка отменена</b>\n\n"
            "Возвращаемся в главное меню...",
            reply_markup=escrow_bot.get_main_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Ошибка отмены сделки!", show_alert=True)

# Обработка команды для присоединения к сделке
@dp.message(Command("start"))
async def handle_join_deal(message: types.Message, state: FSMContext):
    """Обработка присоединения к сделке через ссылку"""
    if not message.text.startswith("/start join_"):
        return
    
    deal_id = message.text.replace("/start join_", "")
    user_id = message.from_user.id
    
    # Проверяем существование сделки
    deal = await escrow_bot.db.get_deal(deal_id)
    if not deal:
        await message.answer("❌ Сделка не найдена или уже завершена!")
        return
    
    # Проверяем, что пользователь не создатель
    if deal['creator_id'] == user_id:
        await message.answer("❌ Вы не можете присоединиться к собственной сделке!")
        return
    
    # Проверяем, что сделка активна
    if deal['status'] != 'active':
        await message.answer("❌ Эта сделка уже недоступна!")
        return
    
    await state.update_data(deal_id=deal_id)
    await state.set_state(JoinDealStates.waiting_password)
    
    await message.answer(
        f"🔐 <b>Присоединение к сделке</b>\n\n"
        f"💰 Сумма: {deal['amount']} USDT\n"
        f"📝 Условие: {deal['condition']}\n\n"
        f"Введите пароль для присоединения:",
        parse_mode="HTML"
    )

@dp.message(JoinDealStates.waiting_password)
async def process_join_password(message: types.Message, state: FSMContext):
    """Обработка пароля для присоединения"""
    data = await state.get_data()
    deal_id = data['deal_id']
    password = message.text.strip()
    user_id = message.from_user.id
    
    # Проверяем пароль
    deal = await escrow_bot.db.get_deal(deal_id)
    if not deal or deal['password'] != password:
        await message.answer("❌ Неверный пароль!")
        return
    
    # Присоединяем к сделке
    success = await escrow_bot.db.join_deal(deal_id, user_id)
    if success:
        await state.clear()
        
        # Отправляем информацию для оплаты
        await message.answer(
            f"✅ <b>Вы успешно присоединились к сделке!</b>\n\n"
            f"💰 Сумма к оплате: <b>{deal['amount']} USDT</b>\n"
            f"📝 Условие: {deal['condition']}\n\n"
            f"💳 <b>Информация для оплаты:</b>",
            parse_mode="HTML"
        )
        
        # Отправляем QR коды и адреса
        await escrow_bot.send_payment_info(message.chat.id, deal['amount'])
        
        # Уведомляем создателя
        await bot.send_message(
            deal['creator_id'],
            f"🔔 <b>К вашей сделке присоединился покупатель!</b>\n\n"
            f"💰 Сумма: {deal['amount']} USDT\n"
            f"👤 Покупатель: @{message.from_user.username or 'NoUsername'}\n\n"
            f"⏳ Ожидаем оплату...",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Ошибка присоединения к сделке!")

@dp.message(Command("admin"))
async def admin_command(message: types.Message):
    """Команда для доступа к админ панели"""
    from config import NOTIFICATION_SETTINGS
    admin_id = NOTIFICATION_SETTINGS.get('admin_chat_id')
    
    if str(message.from_user.id) == str(admin_id):
        # Отложенный импорт для избежания циклических импортов
        from admin_panel import AdminPanel
        admin_panel = AdminPanel(escrow_bot.db, bot)
        await admin_panel.send_admin_menu(message.chat.id)
    else:
        await message.answer("❌ У вас нет прав доступа к административной панели!")

# Инициализация экземпляра бота для использования в других модулей
escrow_bot = ModernEscrowBot()

def register_handlers():
    """Регистрация всех обработчиков бота"""
    # Обработчики уже зарегистрированы через декораторы выше
    
    # Регистрируем админ панель
    from admin_panel import AdminPanel, register_admin_handlers
    admin_panel = AdminPanel(escrow_bot.db, bot)
    register_admin_handlers(dp, admin_panel)
    
    logger.info("✅ Все обработчики зарегистрированы")
    
def setup_bot():
    """Настройка бота и регистрация обработчиков"""
    register_handlers()
    return escrow_bot, dp, bot