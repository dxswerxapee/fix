#!/usr/bin/env python3
"""
Тестирование подключения к базе данных
"""

import asyncio
import os
from dotenv import load_dotenv
from database_manager import DatabaseManager

# Загружаем переменные окружения
load_dotenv()

async def test_database():
    """Тестирование подключения к базе данных"""
    
    print("🔄 Тестирование подключения к базе данных...")
    
    try:
        # Создаем экземпляр менеджера БД
        db = DatabaseManager()
        
        print("📡 Инициализация подключения...")
        await db.initialize()
        
        print("✅ Подключение успешно!")
        
        # Тестируем создание таблиц
        print("🗄️ Проверка таблиц...")
        
        # Проверяем, что можем выполнить простой запрос
        async with db.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT COUNT(*) FROM users")
                result = await cursor.fetchone()
                print(f"📊 Количество пользователей в БД: {result[0] if result else 0}")
                
                await cursor.execute("SELECT COUNT(*) FROM deals")
                result = await cursor.fetchone()
                print(f"💼 Количество сделок в БД: {result[0] if result else 0}")
        
        print("✅ Все тесты пройдены успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return False
    
    finally:
        # Закрываем соединение
        if 'db' in locals():
            await db.close()
            print("🔒 Соединение закрыто")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_database())
    
    if success:
        print("\n🎉 База данных готова к работе!")
    else:
        print("\n💥 Проблемы с базой данных. Проверьте настройки в .env файле")
        exit(1)