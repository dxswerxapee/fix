@echo off
echo ==================================================
echo   End Round Music Plugin - Компиляция
echo ==================================================
echo.

REM Проверка наличия .NET SDK
dotnet --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ОШИБКА: .NET SDK не найден!
    echo Скачайте и установите .NET 8.0 SDK с https://dotnet.microsoft.com/download/dotnet/8.0
    pause
    exit /b 1
)

echo [1/3] Проверка зависимостей...
dotnet restore
if %errorlevel% neq 0 (
    echo ОШИБКА: Не удалось восстановить зависимости!
    pause
    exit /b 1
)

echo [2/3] Компиляция плагина...
dotnet build -c Release
if %errorlevel% neq 0 (
    echo ОШИБКА: Компиляция завершилась с ошибкой!
    pause
    exit /b 1
)

echo [3/3] Создание папки для установки...
if not exist "release\" mkdir release
copy "bin\Release\net8.0\EndRoundMusicPlugin.dll" "release\"
copy "config.json" "release\"

echo.
echo ==================================================
echo   КОМПИЛЯЦИЯ ЗАВЕРШЕНА УСПЕШНО!
echo ==================================================
echo.
echo Файлы для установки находятся в папке 'release':
echo - EndRoundMusicPlugin.dll
echo - config.json
echo.
echo Скопируйте эти файлы на ваш CS2 сервер согласно README.md
echo.
pause