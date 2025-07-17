#!/usr/bin/env python3
"""
Modern Escrow Bot 2025
Современный эскроу-бот для Telegram с поддержкой MySQL и QR-кодов
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Добавляем текущую директорию в Python path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Импортируем наши модули
from config import BOT_TOKEN, validate_config
from modern_escrow_bot import escrow_bot, dp, bot
from admin_panel import AdminPanel

# Загружаем переменные окружения
load_dotenv()

# Настройка улучшенного логирования
def setup_logging():
    """Настройка системы логирования"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Настройка основного логгера
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler('modern_escrow_bot.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Отдельный логгер для ошибок
    error_logger = logging.getLogger('errors')
    error_handler = logging.FileHandler('bot_errors.log', encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(log_format))
    error_logger.addHandler(error_handler)
    
    # Уменьшаем уровень логирования для aiogram
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('aiomysql').setLevel(logging.WARNING)

async def on_startup():
    """Действия при запуске бота"""
    logger = logging.getLogger(__name__)
    
    try:
        # Проверяем конфигурацию
        validate_config()
        logger.info("✅ Конфигурация проверена")
        
        # Инициализируем базу данных
        await escrow_bot.db.initialize()
        logger.info("✅ База данных инициализирована")
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        logger.info(f"🤖 Бот запущен: @{bot_info.username} ({bot_info.full_name})")
        
        # Проверяем, что бот может отправлять сообщения админу
        from config import NOTIFICATION_SETTINGS
        admin_id = NOTIFICATION_SETTINGS.get('admin_chat_id')
        
        if admin_id:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text="🚀 <b>Modern Escrow Bot 2025 запущен!</b>\n\n"
                         f"🤖 Бот: @{bot_info.username}\n"
                         f"📅 Время запуска: {asyncio.get_event_loop().time()}\n"
                         f"✅ Все системы работают нормально",
                    parse_mode="HTML"
                )
                logger.info("✅ Уведомление админу отправлено")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось отправить уведомление админу: {e}")
        
        logger.info("🎉 Бот успешно запущен и готов к работе!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
        raise

async def on_shutdown():
    """Действия при остановке бота"""
    logger = logging.getLogger(__name__)
    
    try:
        # Закрываем соединение с БД
        await escrow_bot.db.close()
        logger.info("🔒 Соединение с базой данных закрыто")
        
        # Уведомляем админа об остановке
        from config import NOTIFICATION_SETTINGS
        admin_id = NOTIFICATION_SETTINGS.get('admin_chat_id')
        
        if admin_id:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text="🛑 <b>Modern Escrow Bot 2025 остановлен</b>\n\n"
                         f"📅 Время остановки: {asyncio.get_event_loop().time()}\n"
                         f"💾 Все данные сохранены",
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.warning(f"⚠️ Не удалось отправить уведомление об остановке: {e}")
        
        # Закрываем сессию бота
        await bot.session.close()
        logger.info("🔒 Сессия бота закрыта")
        
        logger.info("👋 Бот корректно остановлен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при остановке бота: {e}")

def check_requirements():
    """Проверка наличия необходимых зависимостей"""
    required_packages = [
        'aiogram', 'aiomysql', 'qrcode', 'Pillow', 'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Отсутствуют необходимые пакеты: {', '.join(missing_packages)}")
        print("Установите их командой: pip install -r modern_requirements.txt")
        sys.exit(1)

async def main():
    """Главная функция запуска бота"""
    # Настраиваем логирование
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Проверяем зависимости
    check_requirements()
    
    # Выводим информацию о запуске
    print("🚀 Запуск Modern Escrow Bot 2025...")
    print("📋 Загружаем конфигурацию...")
    
    try:
        # Выполняем действия при запуске
        await on_startup()
        
        # Запускаем polling
        logger.info("🔄 Запуск polling...")
        await dp.start_polling(bot, skip_updates=True)
        
    except KeyboardInterrupt:
        logger.info("⏹️ Получен сигнал остановки")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise
    finally:
        # Выполняем действия при остановке
        await on_shutdown()

if __name__ == "__main__":
    # Проверяем версию Python
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        sys.exit(1)
    
    # Запускаем бота
    try:
        if sys.platform == 'win32':
            # Для Windows используем ProactorEventLoop
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)