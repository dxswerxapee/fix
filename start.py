#!/usr/bin/env python3
"""
Скрипт запуска Modern Escrow Bot 2025 с предварительными проверками
"""

import asyncio
import sys
import os

def check_python_version():
    """Проверка версии Python"""
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        print(f"Текущая версия: {sys.version}")
        return False
    print(f"✅ Python версия: {sys.version}")
    return True

def check_env_file():
    """Проверка файла .env"""
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден!")
        print("Создайте .env файл на основе README.md")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['BOT_TOKEN', 'MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var) == 'YOUR_BOT_TOKEN_HERE':
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Не заполнены переменные окружения: {', '.join(missing_vars)}")
        return False
    
    print("✅ Переменные окружения настроены")
    return True

def check_dependencies():
    """Проверка зависимостей"""
    try:
        import aiogram
        import aiomysql
        import qrcode
        import PIL
        print("✅ Все зависимости установлены")
        return True
    except ImportError as e:
        print(f"❌ Отсутствует зависимость: {e}")
        print("Выполните: pip install -r modern_requirements.txt")
        return False

async def test_database():
    """Тестирование базы данных"""
    try:
        from test_connection import test_database
        return await test_database()
    except Exception as e:
        print(f"❌ Ошибка тестирования БД: {e}")
        return False

async def main():
    """Главная функция запуска с проверками"""
    
    print("🚀 Modern Escrow Bot 2025 - Запуск с проверками")
    print("=" * 50)
    
    # Проверяем Python
    if not check_python_version():
        sys.exit(1)
    
    # Проверяем .env файл
    if not check_env_file():
        sys.exit(1)
    
    # Проверяем зависимости
    if not check_dependencies():
        sys.exit(1)
    
    # Тестируем базу данных
    print("🔄 Тестирование базы данных...")
    if not await test_database():
        print("❌ Проблемы с базой данных!")
        choice = input("Продолжить запуск? (y/N): ")
        if choice.lower() != 'y':
            sys.exit(1)
    
    print("=" * 50)
    print("🎉 Все проверки пройдены! Запуск бота...")
    print("=" * 50)
    
    # Запускаем основной бот
    try:
        from run_bot import main as run_main
        await run_main()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())