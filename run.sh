#!/bin/bash

echo "🚀 Modern Escrow Bot 2025 - Linux/macOS Launcher"
echo "================================================"

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден! Установите Python 3.8+"
    exit 1
fi

# Проверяем версию Python
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Требуется Python 3.8+, найден Python $python_version"
    exit 1
fi

echo "✅ Python $python_version найден"

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "⚠️ Файл .env не найден!"
    echo "Запускаем установку..."
    python3 install.py
    echo ""
    echo "✅ Теперь заполните .env файл и запустите скрипт снова"
    exit 0
fi

# Запускаем бота
echo "🤖 Запуск бота..."
python3 start.py