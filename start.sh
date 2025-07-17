#!/bin/bash

echo "🎄 Запуск OZER GARANT BOT 🎄"
echo "================================"

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.8+"
    exit 1
fi

# Проверка pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 не найден. Установите pip"
    exit 1
fi

# Установка зависимостей
echo "📦 Установка зависимостей..."
echo "⚠️  Для установки зависимостей выполните:"
echo "sudo apt update"
echo "sudo apt install python3-pip python3-venv python3-dev"
echo "python3 -m venv venv"
echo "source venv/bin/activate"
echo "pip install -r requirements.txt"
echo ""
echo "Или используйте --break-system-packages (не рекомендуется):"
echo "pip3 install -r requirements.txt --break-system-packages"

# Проверка файла .env
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден!"
    echo "📝 Создайте файл .env с настройками:"
    echo "BOT_TOKEN=YOUR_BOT_TOKEN_HERE"
    echo "DB_HOST=138.201.65.234"
    echo "DB_USER=mgknx210_telegram"
    echo "DB_PASSWORD=mgknx210_telegram"
    echo "DB_NAME=mgknx210_telegram"
    echo "COMMISSION_RATE=1.0"
    exit 1
fi

# Проверка токена бота
if grep -q "YOUR_BOT_TOKEN_HERE" .env; then
    echo "❌ Не задан токен бота в файле .env!"
    echo "📝 Получите токен у @BotFather и обновите файл .env"
    exit 1
fi

echo "🚀 Запуск бота..."
python3 bot.py