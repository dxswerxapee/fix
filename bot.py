import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes
from database import Database
from utils import generate_captcha, generate_crypto_address, generate_qr_code, format_deal_status, format_role, validate_amount, validate_password
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
CAPTCHA, WAITING_AMOUNT, WAITING_CONDITIONS, WAITING_PASSWORD, WAITING_JOIN_PASSWORD = range(5)

# Инициализация базы данных
db = Database()

class GarantBot:
    def __init__(self):
        self.bot_token = os.getenv('BOT_TOKEN')
        self.bot_username = None
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        user_id = user.id
        
        # Добавляем пользователя в базу данных
        db.add_user(user_id, user.username, user.first_name)
        
        # Проверяем, есть ли параметры для присоединения к сделке
        if context.args:
            return await self.handle_deal_join(update, context)
        
        # Проверяем, прошел ли пользователь верификацию
        if db.is_user_verified(user_id):
            return await self.show_main_menu(update, context)
        
        # Показываем капчу
        captcha_code = generate_captcha()
        db.save_captcha(user_id, captcha_code)
        
        message = f"""🔐 Проверка безопасности

Для получения доступа к боту введи простую капчу:
Выберите на клавиатуре: 🔑

Код: {captcha_code}"""
        
        await update.message.reply_text(message)
        return CAPTCHA
    
    async def handle_captcha(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик капчи"""
        user_id = update.effective_user.id
        captcha_input = update.message.text
        
        if db.verify_captcha(user_id, captcha_input):
            db.verify_user(user_id)
            await self.show_main_menu(update, context)
            return ConversationHandler.END
        else:
            await update.message.reply_text("❌ Неверный код капчи. Попробуйте еще раз.")
            return CAPTCHA
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает главное меню"""
        message = """🎄 OZER GARANT BOT 🎄
┏━━━━━━━━━━━━━━━━━━━━━━┓
🟢 Безопасные сделки под защитой Озера
┗━━━━━━━━━━━━━━━━━━━━━━┛

💚 Ваш надежный крипто-гарант 💚
▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄

🔹 Возможности:
├─ 💼 Создать сделку
├─ 🤝 Присоединиться к сделке
├─ 🔍 Просмотр активных сделок
└─ 🛡️ Гарант безопасности

💸 Комиссия: 1.0$
🕒 Поддержка 24/7"""
        
        keyboard = [
            [KeyboardButton("💼 Создать сделку")],
            [KeyboardButton("📊 Мои сделки"), KeyboardButton("👤 Профиль")],
            [KeyboardButton("💬 Поддержка")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        if update.message:
            await update.message.reply_text(message, reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(message)
            await update.callback_query.message.reply_text("Главное меню:", reply_markup=reply_markup)
    
    async def handle_deal_join(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик присоединения к сделке через ссылку"""
        try:
            # Формат: deal_ID_USERID
            deal_data = context.args[0].split('_')
            if len(deal_data) >= 2 and deal_data[0] == 'deal':
                deal_id = int(deal_data[1])
                context.user_data['joining_deal_id'] = deal_id
                
                deal = db.get_deal(deal_id)
                if not deal:
                    await update.message.reply_text("❌ Сделка не найдена.")
                    return ConversationHandler.END
                
                await update.message.reply_text(f"🔐 Введите пароль для присоединения к сделке #{deal_id}:")
                return WAITING_JOIN_PASSWORD
        except (ValueError, IndexError):
            pass
        
        return await self.start(update, context)
    
    async def handle_join_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик пароля для присоединения к сделке"""
        user_id = update.effective_user.id
        password = update.message.text
        deal_id = context.user_data.get('joining_deal_id')
        
        if db.join_deal(deal_id, user_id, password):
            deal = db.get_deal(deal_id)
            await update.message.reply_text("✅ Партнер успешно присоединился к сделке!\nОжидайте подтверждения оплаты от покупателя.")
            
            # Уведомляем создателя сделки
            creator_id = deal['seller_id'] if deal['seller_id'] != user_id else deal['buyer_id']
            if creator_id:
                try:
                    await context.bot.send_message(
                        creator_id,
                        f"✅ К вашей сделке #{deal_id} присоединился партнер!"
                    )
                except:
                    pass
            
            await self.show_deal_payment_info(update, context, deal_id)
        else:
            await update.message.reply_text("❌ Неверный пароль или сделка недоступна.")
        
        return ConversationHandler.END
    
    async def create_deal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начинает процесс создания сделки"""
        keyboard = [
            [InlineKeyboardButton("💰 Продавец", callback_data="role_seller")],
            [InlineKeyboardButton("🛒 Покупатель", callback_data="role_buyer")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text("🎭 Выберите вашу роль в сделке:", reply_markup=reply_markup)
    
    async def handle_role_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора роли"""
        query = update.callback_query
        await query.answer()
        
        role = query.data.split('_')[1]
        context.user_data['deal_role'] = role
        
        await query.edit_message_text("💵 Введите сумму сделки в USD:")
        return WAITING_AMOUNT
    
    async def handle_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ввода суммы"""
        amount_str = update.message.text
        amount, error = validate_amount(amount_str)
        
        if error:
            await update.message.reply_text(f"❌ {error}\nПопробуйте еще раз:")
            return WAITING_AMOUNT
        
        context.user_data['deal_amount'] = amount
        await update.message.reply_text("📝 Введите условия сделки:")
        return WAITING_CONDITIONS
    
    async def handle_conditions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ввода условий сделки"""
        conditions = update.message.text
        
        if len(conditions) < 5:
            await update.message.reply_text("❌ Условия сделки слишком короткие. Минимум 5 символов.")
            return WAITING_CONDITIONS
        
        context.user_data['deal_conditions'] = conditions
        await update.message.reply_text("🔐 Придумайте пароль для сделки (минимум 4 символа):")
        return WAITING_PASSWORD
    
    async def handle_deal_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ввода пароля для сделки"""
        password = update.message.text
        is_valid, error = validate_password(password)
        
        if not is_valid:
            await update.message.reply_text(f"❌ {error}")
            return WAITING_PASSWORD
        
        # Создаем сделку
        user_id = update.effective_user.id
        role = context.user_data['deal_role']
        amount = context.user_data['deal_amount']
        conditions = context.user_data['deal_conditions']
        
        deal_id = db.create_deal(user_id, amount, conditions, password, role)
        
        if deal_id:
            commission = float(os.getenv('COMMISSION_RATE', 1.0))
            total_amount = amount + commission
            
            role_text = "Продавец" if role == "seller" else "Покупатель"
            
            message = f"""✅ Сделка успешно создана!

🆔 ID сделки: {deal_id}
💰 Сумма: {amount}$
📝 Условия: {conditions}
👤 Ваша роль: {role_text}
🔐 Пароль: {password}

❌ Отмена: Вы можете отменить сделку."""
            
            await update.message.reply_text(message)
            
            # Создаем ссылку для присоединения
            bot_username = context.bot.username
            join_link = f"https://t.me/{bot_username}?start=deal_{deal_id}_{user_id}"
            
            link_message = f"""🔗 Ссылка для присоединения к сделке:
{join_link}

Отправьте эту ссылку вашему партнеру для автоматического подключения."""
            
            await update.message.reply_text(link_message)
        else:
            await update.message.reply_text("❌ Ошибка создания сделки. Попробуйте позже.")
        
        return ConversationHandler.END
    
    async def show_deal_payment_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE, deal_id: int):
        """Показывает информацию об оплате сделки"""
        deal = db.get_deal(deal_id)
        if not deal:
            return
        
        commission = float(os.getenv('COMMISSION_RATE', 1.0))
        total_amount = deal['amount'] + commission
        
        message = f"""🟢 Детали оплаты по сделке #{deal_id}!

💵 Сумма: {total_amount}$ (USDT)

📝 Условия: {deal['conditions']}

💳 Инструкции по оплате:
Пожалуйста, выберите способ оплаты, чтобы получить реквизиты.

⏳ Статус: Ожидание оплаты..."""
        
        keyboard = [
            [InlineKeyboardButton("TRC20 USDT", callback_data=f"payment_TRC20_{deal_id}")],
            [InlineKeyboardButton("BTC", callback_data=f"payment_BTC_{deal_id}")],
            [InlineKeyboardButton("BNB", callback_data=f"payment_BNB_{deal_id}")],
            [InlineKeyboardButton("TRON", callback_data=f"payment_TRON_{deal_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            await update.message.reply_text(message, reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
    
    async def handle_payment_method(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора способа оплаты"""
        query = update.callback_query
        await query.answer()
        
        data_parts = query.data.split('_')
        payment_method = data_parts[1]
        deal_id = int(data_parts[2])
        
        # Получаем адрес для оплаты
        address = generate_crypto_address(payment_method)
        
        # Обновляем информацию об оплате в базе данных
        db.update_deal_payment(deal_id, payment_method, address)
        
        deal = db.get_deal(deal_id)
        commission = float(os.getenv('COMMISSION_RATE', 1.0))
        total_amount = deal['amount'] + commission
        
        message = f"""📦 Сделка #{deal_id}

💰 Сумма: {total_amount}$
🔗 Сеть: {payment_method}
🏷 Адрес: {address}

👇 Отсканируйте QR-код или скопируйте адрес"""
        
        # Генерируем QR код
        qr_data = address
        qr_image = generate_qr_code(qr_data)
        
        if qr_image:
            await query.edit_message_text(message)
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=qr_image,
                caption=f"QR-код для оплаты\nАдрес: {address}"
            )
        else:
            await query.edit_message_text(message)
    
    async def show_user_deals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает сделки пользователя"""
        user_id = update.effective_user.id
        deals = db.get_user_deals(user_id)
        
        if not deals:
            await update.message.reply_text("📭 У вас пока нет активных сделок.")
            return
        
        message = "📊 Ваши сделки:\n\n"
        
        for deal in deals[:10]:  # Показываем только последние 10 сделок
            role = format_role(deal['id'], user_id, deal['seller_id'], deal['buyer_id'])
            status = format_deal_status(deal['status'])
            
            message += f"""🆔 Сделка #{deal['id']}
💰 Сумма: {deal['amount']}$
👤 Роль: {role}
📊 Статус: {status}
📅 Дата: {deal['created_at'].strftime('%d.%m.%Y %H:%M')}
━━━━━━━━━━━━━━━━━━━━

"""
        
        await update.message.reply_text(message)
    
    async def show_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает профиль пользователя"""
        user = update.effective_user
        user_deals = db.get_user_deals(user.id)
        
        completed_deals = len([d for d in user_deals if d['status'] == 'completed'])
        active_deals = len([d for d in user_deals if d['status'] in ['waiting_partner', 'waiting_payment', 'payment_sent']])
        
        message = f"""👤 Ваш профиль

🆔 ID: {user.id}
👤 Имя: {user.first_name or 'Не указано'}
📝 Username: @{user.username or 'Не указан'}

📊 Статистика:
✅ Завершенных сделок: {completed_deals}
🔄 Активных сделок: {active_deals}
📈 Всего сделок: {len(user_deals)}

🛡️ Статус: Верифицирован ✅"""
        
        await update.message.reply_text(message)
    
    async def show_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает информацию о поддержке"""
        message = """💬 Поддержка OZER GARANT BOT

🕒 Работаем круглосуточно
📞 Ответим в течение 5 минут

📧 Связаться с нами:
• Telegram: @support_ozer
• Email: support@ozer.com

❓ Часто задаваемые вопросы:
• Как создать сделку?
• Как работает гарант?
• Сколько времени занимает сделка?

🛡️ Ваша безопасность - наш приоритет!"""
        
        await update.message.reply_text(message)
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        text = update.message.text
        
        if text == "💼 Создать сделку":
            await self.create_deal(update, context)
        elif text == "📊 Мои сделки":
            await self.show_user_deals(update, context)
        elif text == "👤 Профиль":
            await self.show_profile(update, context)
        elif text == "💬 Поддержка":
            await self.show_support(update, context)
        else:
            await update.message.reply_text("❓ Неизвестная команда. Используйте меню для навигации.")
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена текущей операции"""
        await update.message.reply_text("❌ Операция отменена.")
        await self.show_main_menu(update, context)
        return ConversationHandler.END
    
    def run(self):
        """Запуск бота"""
        # Инициализация базы данных
        if not db.connect():
            logger.error("Не удалось подключиться к базе данных")
            return
        
        if not db.create_tables():
            logger.error("Не удалось создать таблицы")
            return
        
        # Создание приложения
        app = Application.builder().token(self.bot_token).build()
        
        # Обработчик создания сделки
        deal_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.handle_role_selection, pattern="^role_"),
            ],
            states={
                WAITING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_amount)],
                WAITING_CONDITIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_conditions)],
                WAITING_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_deal_password)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        
        # Обработчик капчи и присоединения к сделке
        main_conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                CAPTCHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_captcha)],
                WAITING_JOIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_join_password)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        
        # Добавление обработчиков
        app.add_handler(main_conv_handler)
        app.add_handler(deal_conv_handler)
        app.add_handler(CallbackQueryHandler(self.handle_payment_method, pattern="^payment_"))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
        
        logger.info("Бот запущен!")
        app.run_polling()

if __name__ == '__main__':
    bot = GarantBot()
    bot.run()