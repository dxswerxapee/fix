#!/bin/bash

echo "=================================================="
echo "  End Round Music Plugin - Компиляция"
echo "=================================================="
echo

# Проверка наличия .NET SDK
if ! command -v dotnet &> /dev/null; then
    echo "ОШИБКА: .NET SDK не найден!"
    echo "Установите .NET 8.0 SDK:"
    echo "https://dotnet.microsoft.com/download/dotnet/8.0"
    exit 1
fi

echo "[1/3] Проверка зависимостей..."
dotnet restore
if [ $? -ne 0 ]; then
    echo "ОШИБКА: Не удалось восстановить зависимости!"
    exit 1
fi

echo "[2/3] Компиляция плагина..."
dotnet build -c Release
if [ $? -ne 0 ]; then
    echo "ОШИБКА: Компиляция завершилась с ошибкой!"
    exit 1
fi

echo "[3/3] Создание папки для установки..."
mkdir -p release
cp "bin/Release/net8.0/EndRoundMusicPlugin.dll" "release/"
cp "config.json" "release/"

echo
echo "=================================================="
echo "  КОМПИЛЯЦИЯ ЗАВЕРШЕНА УСПЕШНО!"
echo "=================================================="
echo
echo "Файлы для установки находятся в папке 'release':"
echo "- EndRoundMusicPlugin.dll"
echo "- config.json"
echo
echo "Скопируйте эти файлы на ваш CS2 сервер согласно README.md"
echo