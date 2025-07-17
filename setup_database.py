#!/usr/bin/env python3
"""
Скрипт для создания базы данных MySQL для Modern Escrow Bot 2025
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
import aiomysql

# Загружаем переменные окружения
load_dotenv()

async def setup_database():
    """Создание базы данных и пользователя"""
    
    # Конфигурация для подключения к MySQL (как root)
    root_config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': 'root',  # Нужны права root для создания БД и пользователя
        'password': input("Введите пароль root для MySQL: "),
        'charset': 'utf8mb4'
    }
    
    # Параметры для создания
    db_name = os.getenv('MYSQL_DATABASE', 'modern_escrow_bot')
    db_user = os.getenv('MYSQL_USER', 'escrow_bot')
    db_password = os.getenv('MYSQL_PASSWORD', 'strong_password_here')
    
    try:
        print("🔄 Подключение к MySQL...")
        
        # Подключаемся к MySQL
        connection = await aiomysql.connect(**root_config)
        
        async with connection.cursor() as cursor:
            print(f"🗄️ Создание базы данных '{db_name}'...")
            
            # Создаем базу данных
            await cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            
            print(f"👤 Создание пользователя '{db_user}'...")
            
            # Создаем пользователя (удаляем если существует)
            await cursor.execute(f"DROP USER IF EXISTS '{db_user}'@'%'")
            await cursor.execute(f"CREATE USER '{db_user}'@'%' IDENTIFIED BY '{db_password}'")
            
            # Даем права пользователю
            await cursor.execute(f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_user}'@'%'")
            await cursor.execute("FLUSH PRIVILEGES")
            
            print("✅ База данных и пользователь созданы успешно!")
            
        await connection.ensure_closed()
        
        print("🔄 Проверка подключения с новым пользователем...")
        
        # Проверяем подключение с новым пользователем
        test_config = {
            'host': root_config['host'],
            'port': root_config['port'],
            'user': db_user,
            'password': db_password,
            'db': db_name,
            'charset': 'utf8mb4'
        }
        
        test_connection = await aiomysql.connect(**test_config)
        await test_connection.ensure_closed()
        
        print("✅ Подключение с новым пользователем работает!")
        print(f"\n📋 Настройки для .env файла:")
        print(f"MYSQL_HOST={root_config['host']}")
        print(f"MYSQL_PORT={root_config['port']}")
        print(f"MYSQL_USER={db_user}")
        print(f"MYSQL_PASSWORD={db_password}")
        print(f"MYSQL_DATABASE={db_name}")
        
    except Exception as e:
        print(f"❌ Ошибка настройки базы данных: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Настройка базы данных для Modern Escrow Bot 2025")
    print("⚠️ Убедитесь, что MySQL запущен и у вас есть права root")
    
    confirm = input("\nПродолжить? (y/N): ")
    if confirm.lower() != 'y':
        print("❌ Настройка отменена")
        sys.exit(0)
    
    asyncio.run(setup_database())