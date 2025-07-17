# 📖 Инструкция по установке OZER GARANT BOT

## 🖥️ Системные требования

- Ubuntu 20.04+ / Debian 10+ / CentOS 8+
- Python 3.8+
- MySQL 5.7+ / MariaDB 10.3+
- Минимум 1GB RAM
- 10GB свободного места

## 🔧 Подготовка системы

### 1. Обновление системы
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Установка необходимых пакетов
```bash
# Python и инструменты разработки
sudo apt install python3 python3-pip python3-venv python3-dev -y

# MySQL клиент и библиотеки
sudo apt install mysql-client libmysqlclient-dev -y

# Дополнительные утилиты
sudo apt install git curl wget htop -y
```

### 3. Установка MySQL (если не установлен)
```bash
sudo apt install mysql-server -y
sudo mysql_secure_installation
```

## 📁 Установка бота

### 1. Создание пользователя для бота
```bash
sudo useradd -m -s /bin/bash garant-bot
sudo usermod -aG sudo garant-bot
```

### 2. Скачивание кода
```bash
sudo su - garant-bot
git clone <repository_url> /home/garant-bot/ozer-garant-bot
cd /home/garant-bot/ozer-garant-bot
```

### 3. Создание виртуального окружения
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Настройка базы данных
```bash
# Войти в MySQL как root
sudo mysql -u root -p

# Создать базу данных и пользователя
CREATE DATABASE mgknx210_telegram CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'mgknx210_telegram'@'localhost' IDENTIFIED BY 'STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON mgknx210_telegram.* TO 'mgknx210_telegram'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 5. Настройка .env файла
```bash
cp .env .env.example
nano .env
```

Заполните файл .env:
```env
BOT_TOKEN=1234567890:AABBCCDDEEFFGGHHIIJJKKLLmmnnoopp
DB_HOST=localhost
DB_USER=mgknx210_telegram
DB_PASSWORD=STRONG_PASSWORD_HERE
DB_NAME=mgknx210_telegram
COMMISSION_RATE=1.0
```

### 6. Создание Telegram бота
1. Перейдите к @BotFather в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен в .env файл

### 7. Тестовый запуск
```bash
source venv/bin/activate
python3 bot.py
```

## 🚀 Настройка автозапуска

### 1. Создание systemd сервиса
```bash
sudo nano /etc/systemd/system/ozer-garant-bot.service
```

Содержимое файла:
```ini
[Unit]
Description=OZER Garant Telegram Bot
After=network.target mysql.service

[Service]
Type=simple
User=garant-bot
Group=garant-bot
WorkingDirectory=/home/garant-bot/ozer-garant-bot
Environment=PATH=/home/garant-bot/ozer-garant-bot/venv/bin
ExecStart=/home/garant-bot/ozer-garant-bot/venv/bin/python bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 2. Активация сервиса
```bash
sudo systemctl daemon-reload
sudo systemctl enable ozer-garant-bot
sudo systemctl start ozer-garant-bot
```

### 3. Проверка статуса
```bash
sudo systemctl status ozer-garant-bot
sudo journalctl -u ozer-garant-bot -f
```

## 🔒 Настройка безопасности

### 1. Файрвол
```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 3306  # MySQL (только если нужен внешний доступ)
```

### 2. Права на файлы
```bash
sudo chown -R garant-bot:garant-bot /home/garant-bot/ozer-garant-bot
sudo chmod 600 /home/garant-bot/ozer-garant-bot/.env
sudo chmod +x /home/garant-bot/ozer-garant-bot/start.sh
```

### 3. Резервное копирование
```bash
# Создание скрипта бэкапа
sudo nano /home/garant-bot/backup.sh
```

Содержимое скрипта:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mysqldump -u mgknx210_telegram -p mgknx210_telegram > /home/garant-bot/backups/db_backup_$DATE.sql
find /home/garant-bot/backups -name "*.sql" -mtime +7 -delete
```

```bash
sudo chmod +x /home/garant-bot/backup.sh
mkdir -p /home/garant-bot/backups

# Добавление в crontab
crontab -e
```

Добавить строку:
```
0 2 * * * /home/garant-bot/backup.sh
```

## 📊 Мониторинг

### 1. Просмотр логов
```bash
# Логи сервиса
sudo journalctl -u ozer-garant-bot -f

# Логи приложения
tail -f /home/garant-bot/ozer-garant-bot/bot.log
```

### 2. Мониторинг ресурсов
```bash
# Использование процессора и памяти
htop

# Использование диска
df -h

# Проверка соединений с БД
mysql -u mgknx210_telegram -p -e "SHOW PROCESSLIST;"
```

## 🔄 Обновление

### 1. Остановка сервиса
```bash
sudo systemctl stop ozer-garant-bot
```

### 2. Резервное копирование
```bash
cd /home/garant-bot
cp -r ozer-garant-bot ozer-garant-bot.backup.$(date +%Y%m%d)
```

### 3. Обновление кода
```bash
cd /home/garant-bot/ozer-garant-bot
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Запуск сервиса
```bash
sudo systemctl start ozer-garant-bot
sudo systemctl status ozer-garant-bot
```

## 🆘 Решение проблем

### Бот не отвечает
```bash
# Проверка статуса
sudo systemctl status ozer-garant-bot

# Просмотр ошибок
sudo journalctl -u ozer-garant-bot --since "10 minutes ago"

# Перезапуск
sudo systemctl restart ozer-garant-bot
```

### Проблемы с базой данных
```bash
# Проверка подключения
mysql -u mgknx210_telegram -p -h localhost

# Проверка таблиц
mysql -u mgknx210_telegram -p -e "USE mgknx210_telegram; SHOW TABLES;"
```

### Высокое потребление ресурсов
```bash
# Анализ процессов
ps aux | grep python

# Анализ памяти
free -h

# Проверка логов на ошибки
grep ERROR /home/garant-bot/ozer-garant-bot/bot.log
```

## 📞 Поддержка

- Email: support@ozer.com
- Telegram: @support_ozer
- Документация: README.md

---

**🎄 Удачной установки! 🎄**