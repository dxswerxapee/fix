# 🚀 Быстрый запуск Modern Escrow Bot 2025

## ⚡ За 3 минуты до запуска!

### Шаг 1: Получите токен бота
1. Напишите @BotFather в Telegram
2. Создайте нового бота: `/newbot`
3. Скопируйте токен

### Шаг 2: Установите MySQL
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install mysql-server

# CentOS/RHEL
sudo yum install mysql-server

# macOS
brew install mysql

# Windows - скачайте с mysql.com
```

### Шаг 3: Запустите установку
```bash
# Windows - двойной клик
run.bat

# Linux/macOS
./run.sh
```

### Шаг 4: Заполните .env файл
Откройте `.env` и замените:
```env
BOT_TOKEN=ваш_токен_от_botfather
MYSQL_PASSWORD=ваш_пароль_mysql
ADMIN_CHAT_ID=ваш_telegram_id
```

### Шаг 5: Настройте базу данных
```bash
python setup_database.py
```

### Шаг 6: Запустите бота
```bash
# Windows
run.bat

# Linux/macOS  
./run.sh
```

## 🎯 Готово!

Ваш эскроу-бот запущен и готов к работе!

### Основные команды:
- `/start` - начать работу с ботом
- `/admin` - админ панель (только для админа)

### Функции:
- ✅ Создание эскроу-сделок
- ✅ Присоединение к сделкам
- ✅ Оплата USDT (TRC20) и TON
- ✅ QR-коды для оплаты
- ✅ Админ панель со статистикой

---
**Поддержка:** Все логи в файле `modern_escrow_bot.log`