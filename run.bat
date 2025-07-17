@echo off
echo 🚀 Modern Escrow Bot 2025 - Windows Launcher
echo ===============================================

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python 3.8+
    pause
    exit /b 1
)

REM Проверяем наличие .env файла
if not exist .env (
    echo ⚠️ Файл .env не найден!
    echo Запускаем установку...
    python install.py
    echo.
    echo ✅ Теперь заполните .env файл и запустите скрипт снова
    pause
    exit /b 0
)

REM Запускаем бота
echo 🤖 Запуск бота...
python start.py

pause