import os
from typing import Dict

# Токен Telegram бота
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Конфигурация MySQL
MYSQL_CONFIG: Dict[str, any] = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'escrow_bot'),
    'password': os.getenv('MYSQL_PASSWORD', 'strong_password_here'),
    'database': os.getenv('MYSQL_DATABASE', 'modern_escrow_bot')
}

# Адреса кошельков
WALLET_ADDRESSES = {
    'TRC20_USDT': 'TREBy39rXoWMTfuZcobHNR49EKfnXPbbdE',
    'TON': 'UQC337PVpq0748IOjdbQWJlVjDMIdkENC5iimBrexCikKyYo'
}

# Настройки безопасности
SECURITY_SETTINGS = {
    'min_password_length': 4,
    'min_condition_length': 10,
    'max_deal_amount': 100000.0,  # максимальная сумма сделки в USDT
    'session_timeout': 3600,  # таймаут сессии в секундах
    'max_active_deals_per_user': 1
}

# Настройки уведомлений
NOTIFICATION_SETTINGS = {
    'admin_chat_id': os.getenv('ADMIN_CHAT_ID', None),
    'notify_new_deals': True,
    'notify_payments': True,
    'notify_completions': True
}

# Настройки логирования
LOG_SETTINGS = {
    'level': 'INFO',
    'file': 'modern_escrow_bot.log',
    'max_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
}

# Настройки Redis (если используется для кеширования)
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': int(os.getenv('REDIS_DB', 0)),
    'password': os.getenv('REDIS_PASSWORD', None)
}

# Текстовые сообщения
MESSAGES = {
    'welcome': "🎉 <b>Добро пожаловать в Modern Escrow Bot 2025!</b>\n\nСамый современный и безопасный эскроу-бот для криптовалютных сделок.",
    'captcha_instruction': "🔐 Для продолжения пройдите верификацию:\nВыберите животное: <b>{animal}</b>",
    'registration_success': "✅ <b>Верификация пройдена успешно!</b>\n\n🎉 Добро пожаловать в Modern Escrow Bot 2025!\nВыберите действие из меню ниже:",
    'deal_created': "✅ <b>Сделка создана успешно!</b>\n\n🆔 ID сделки: <code>{deal_id}</code>\n💰 Сумма: <b>{amount} USDT</b>\n📝 Условие: {condition}\n\n🔗 <b>Ссылка для присоединения:</b>\n<code>{join_link}</code>\n\n⚠️ Панель управления заблокирована до завершения сделки",
    'payment_info_trc20': "💳 <b>Оплата TRC20 USDT</b>\n\n💰 Сумма: <code>{amount}</code> USDT\n🏦 Адрес: <code>{address}</code>\n\n⚠️ Внимание! Отправляйте точную сумму на указанный адрес",
    'payment_info_ton': "💎 <b>Оплата TON</b>\n\n💰 Сумма: <code>{amount}</code> TON\n🏦 Адрес: <code>{address}</code>\n\n⚠️ Внимание! Отправляйте точную сумму на указанный адрес"
}

# Эмодзи для разных статусов
STATUS_EMOJI = {
    'active': '🟡',
    'joined': '🔵',
    'paid': '🟠',
    'completed': '🟢',
    'cancelled': '🔴'
}

# Валидация конфигурации
def validate_config():
    """Проверка корректности конфигурации"""
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        raise ValueError("❌ Необходимо установить BOT_TOKEN в переменных окружения")
    
    if not all(MYSQL_CONFIG.values()):
        raise ValueError("❌ Необходимо заполнить все параметры MySQL конфигурации")
    
    return True

# Автоматическая валидация при импорте
if __name__ != "__main__":
    try:
        validate_config()
    except ValueError as e:
        print(f"Ошибка конфигурации: {e}")