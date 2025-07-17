#!/usr/bin/env python3
"""
Автоматическая установка зависимостей для Modern Escrow Bot 2025
"""

import subprocess
import sys
import os

def run_command(command):
    """Выполнение команды в shell"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def install_dependencies():
    """Установка зависимостей"""
    print("🔄 Установка зависимостей...")
    
    success, output = run_command("pip install -r modern_requirements.txt")
    
    if success:
        print("✅ Зависимости установлены успешно!")
        return True
    else:
        print(f"❌ Ошибка установки зависимостей: {output}")
        return False

def create_env_template():
    """Создание шаблона .env файла"""
    if not os.path.exists('.env'):
        print("📝 Создание шаблона .env файла...")
        
        template = """# Telegram Bot Configuration
BOT_TOKEN=YOUR_BOT_TOKEN_HERE

# MySQL Database Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=escrow_bot
MYSQL_PASSWORD=strong_password_here
MYSQL_DATABASE=modern_escrow_bot

# Admin Configuration
ADMIN_CHAT_ID=YOUR_ADMIN_CHAT_ID

# Redis Configuration (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Security Settings
SESSION_TIMEOUT=3600
MAX_DEAL_AMOUNT=100000
"""
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(template)
        
        print("✅ Шаблон .env создан")
        print("⚠️ Не забудьте заполнить ваши данные в .env файле!")
    else:
        print("✅ Файл .env уже существует")

def main():
    """Главная функция установки"""
    print("🚀 Установка Modern Escrow Bot 2025")
    print("=" * 40)
    
    # Проверяем версию Python
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        print(f"Текущая версия: {sys.version}")
        sys.exit(1)
    
    print(f"✅ Python версия: {sys.version_info.major}.{sys.version_info.minor}")
    
    # Устанавливаем зависимости
    if not install_dependencies():
        sys.exit(1)
    
    # Создаем шаблон .env
    create_env_template()
    
    print("=" * 40)
    print("🎉 Установка завершена!")
    print()
    print("📋 Следующие шаги:")
    print("1. Заполните .env файл вашими данными")
    print("2. Настройте MySQL: python setup_database.py")
    print("3. Протестируйте БД: python test_connection.py")
    print("4. Запустите бота: python start.py")
    print()
    print("📚 Подробные инструкции в README.md")

if __name__ == "__main__":
    main()