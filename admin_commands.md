# 🛠️ Команды администрирования OZER GARANT BOT

## 🚀 Управление сервисом

```bash
# Запуск бота
sudo systemctl start ozer-garant-bot

# Остановка бота
sudo systemctl stop ozer-garant-bot

# Перезапуск бота
sudo systemctl restart ozer-garant-bot

# Статус бота
sudo systemctl status ozer-garant-bot

# Включить автозапуск
sudo systemctl enable ozer-garant-bot

# Отключить автозапуск
sudo systemctl disable ozer-garant-bot
```

## 📋 Просмотр логов

```bash
# Просмотр логов в реальном времени
sudo journalctl -u ozer-garant-bot -f

# Просмотр логов за последний час
sudo journalctl -u ozer-garant-bot --since "1 hour ago"

# Просмотр только ошибок
sudo journalctl -u ozer-garant-bot -p err

# Просмотр логов приложения
tail -f /home/garant-bot/ozer-garant-bot/bot.log

# Поиск ошибок в логах
grep -i error /home/garant-bot/ozer-garant-bot/bot.log
```

## 🗄️ Управление базой данных

### Подключение к базе данных
```bash
mysql -u mgknx210_telegram -p mgknx210_telegram
```

### Полезные SQL запросы
```sql
-- Просмотр всех пользователей
SELECT id, username, first_name, registration_date, is_verified FROM users ORDER BY registration_date DESC LIMIT 10;

-- Просмотр активных сделок
SELECT id, seller_id, buyer_id, amount, status, created_at FROM deals WHERE status IN ('waiting_partner', 'waiting_payment') ORDER BY created_at DESC;

-- Статистика сделок
SELECT status, COUNT(*) as count FROM deals GROUP BY status;

-- Пользователи с наибольшим количеством сделок
SELECT u.id, u.username, COUNT(d.id) as deal_count 
FROM users u 
LEFT JOIN deals d ON (u.id = d.seller_id OR u.id = d.buyer_id) 
GROUP BY u.id 
ORDER BY deal_count DESC 
LIMIT 10;

-- Средняя сумма сделок
SELECT AVG(amount) as avg_amount, COUNT(*) as total_deals FROM deals WHERE status = 'completed';

-- Сделки за последние 24 часа
SELECT * FROM deals WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR);
```

### Резервное копирование
```bash
# Создание бэкапа
mysqldump -u mgknx210_telegram -p mgknx210_telegram > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановление из бэкапа
mysql -u mgknx210_telegram -p mgknx210_telegram < backup_20231225_120000.sql

# Автоматический бэкап (добавить в crontab)
0 3 * * * mysqldump -u mgknx210_telegram -p'PASSWORD' mgknx210_telegram > /home/garant-bot/backups/backup_$(date +\%Y\%m\%d_\%H\%M\%S).sql
```

## 📊 Мониторинг системы

### Использование ресурсов
```bash
# Процессы Python
ps aux | grep python

# Использование памяти
free -h

# Использование диска
df -h

# Загрузка CPU
top -p $(pgrep -f bot.py)

# Сетевые соединения
netstat -tulpn | grep python
```

### Проверка работы бота
```bash
# Тест подключения к базе данных
cd /home/garant-bot/ozer-garant-bot
source venv/bin/activate
python3 test_db.py

# Проверка зависимостей
pip list | grep telegram
pip list | grep mysql
```

## 🔧 Обслуживание

### Очистка логов
```bash
# Очистка системных логов (старше 7 дней)
sudo journalctl --vacuum-time=7d

# Ротация логов приложения
cd /home/garant-bot/ozer-garant-bot
if [ -f bot.log ]; then
    mv bot.log bot.log.$(date +%Y%m%d)
    gzip bot.log.$(date +%Y%m%d)
    sudo systemctl restart ozer-garant-bot
fi
```

### Обновление системы
```bash
# Обновление пакетов
sudo apt update && sudo apt upgrade -y

# Обновление Python пакетов
cd /home/garant-bot/ozer-garant-bot
source venv/bin/activate
pip list --outdated
pip install --upgrade package_name
```

### Очистка базы данных
```sql
-- Удаление старых сессий капчи (старше 1 дня)
DELETE FROM captcha_sessions WHERE created_at < DATE_SUB(NOW(), INTERVAL 1 DAY);

-- Удаление отмененных сделок старше 30 дней
DELETE FROM deals WHERE status = 'cancelled' AND created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);

-- Оптимизация таблиц
OPTIMIZE TABLE users, deals, captcha_sessions;
```

## 🚨 Экстренные ситуации

### Высокая нагрузка
```bash
# Проверка нагрузки
uptime
htop

# Ограничение ресурсов для процесса
sudo systemctl edit ozer-garant-bot
# Добавить:
# [Service]
# MemoryLimit=512M
# CPUQuota=50%

# Перезапуск с новыми ограничениями
sudo systemctl daemon-reload
sudo systemctl restart ozer-garant-bot
```

### Проблемы с базой данных
```bash
# Проверка статуса MySQL
sudo systemctl status mysql

# Перезапуск MySQL
sudo systemctl restart mysql

# Проверка соединений
mysql -e "SHOW PROCESSLIST;"

# Проверка размера базы данных
mysql -e "SELECT table_schema AS 'Database', ROUND(SUM(data_length + index_length) / 1024 / 1024, 1) AS 'DB Size in MB' FROM information_schema.tables WHERE table_schema='mgknx210_telegram';"
```

### Восстановление после сбоя
```bash
# Проверка целостности файлов
cd /home/garant-bot/ozer-garant-bot
ls -la
cat .env | head -1

# Восстановление прав доступа
sudo chown -R garant-bot:garant-bot /home/garant-bot/ozer-garant-bot
sudo chmod 600 .env
sudo chmod +x start.sh test_db.py

# Проверка и восстановление виртуального окружения
source venv/bin/activate
pip install -r requirements.txt

# Полная переустановка (крайний случай)
cd /home/garant-bot
cp -r ozer-garant-bot ozer-garant-bot.backup
rm -rf ozer-garant-bot/venv
cd ozer-garant-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 📈 Масштабирование

### Увеличение производительности
```bash
# Настройка MySQL для высоких нагрузок
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
# Добавить:
# max_connections = 200
# innodb_buffer_pool_size = 512M
# query_cache_size = 64M

# Настройка swap
sudo swapon --show
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Мониторинг с помощью cron
```bash
# Создать скрипт мониторинга
cat > /home/garant-bot/monitor.sh << 'EOF'
#!/bin/bash
if ! systemctl is-active --quiet ozer-garant-bot; then
    echo "$(date): Bot is down, restarting..." >> /home/garant-bot/monitor.log
    systemctl restart ozer-garant-bot
fi
EOF

chmod +x /home/garant-bot/monitor.sh

# Добавить в crontab
echo "*/5 * * * * /home/garant-bot/monitor.sh" | crontab -
```

## 📞 Контакты поддержки

- **Техническая поддержка**: @support_ozer
- **Email**: support@ozer.com
- **Документация**: README.md, INSTALL.md

---

**🎄 Удачного администрирования! 🎄**