#!/usr/bin/env python3
"""
Скрипт для тестирования подключения к базе данных
"""

import os
from dotenv import load_dotenv
from database import Database

def test_database_connection():
    """Тестирует подключение к базе данных"""
    print("🔧 Тестирование подключения к базе данных...")
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Проверяем наличие необходимых переменных
    required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        return False
    
    # Создаем экземпляр базы данных
    db = Database()
    
    # Тестируем подключение
    if db.connect():
        print("✅ Подключение к базе данных успешно!")
        
        # Тестируем создание таблиц
        if db.create_tables():
            print("✅ Таблицы созданы/проверены успешно!")
            
            # Тестируем базовые операции
            test_user_id = 123456789
            
            # Добавляем тестового пользователя
            if db.add_user(test_user_id, "test_user", "Test User"):
                print("✅ Тестовый пользователь добавлен!")
                
                # Проверяем верификацию
                if db.verify_user(test_user_id):
                    print("✅ Верификация пользователя работает!")
                    
                    # Проверяем статус верификации
                    if db.is_user_verified(test_user_id):
                        print("✅ Проверка статуса верификации работает!")
                        
                        print("\n🎉 Все тесты пройдены успешно!")
                        print("💡 База данных готова к работе!")
                        
                        # Удаляем тестовые данные
                        cursor = db.connection.cursor()
                        cursor.execute("DELETE FROM users WHERE id = %s", (test_user_id,))
                        cursor.close()
                        print("🧹 Тестовые данные очищены.")
                        
                        db.close()
                        return True
            
        print("❌ Ошибка при тестировании операций с базой данных")
    else:
        print("❌ Не удалось подключиться к базе данных")
        print("💡 Проверьте настройки в файле .env")
    
    db.close()
    return False

def show_database_info():
    """Показывает информацию о настройках базы данных"""
    print("\n📊 Информация о настройках базы данных:")
    print(f"🌐 Хост: {os.getenv('DB_HOST', 'Не задано')}")
    print(f"👤 Пользователь: {os.getenv('DB_USER', 'Не задано')}")
    print(f"🗄️ База данных: {os.getenv('DB_NAME', 'Не задано')}")
    print(f"🔐 Пароль: {'***' if os.getenv('DB_PASSWORD') else 'Не задано'}")

if __name__ == "__main__":
    print("🎄 OZER GARANT BOT - Тест базы данных 🎄")
    print("=" * 50)
    
    show_database_info()
    print("\n" + "=" * 50)
    
    success = test_database_connection()
    
    if success:
        print("\n🚀 Готово к запуску бота!")
        exit(0)
    else:
        print("\n🔧 Необходимо исправить проблемы перед запуском.")
        exit(1)