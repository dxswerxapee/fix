# Отчет об исправлении SQL ошибки в database_manager.py

## Проблема
```
ERROR - * Ошибка инициализации БД: (1064, "You have an error in your SQL syntax; check the manual that corresponds to your MariaDB server version for the right syntax to use near 'condition TEXT NOT NULL, In password VARCHAR(255) NOT NULL, ' at line 6")
```

## Причина
Слова `condition` и `password` являются зарезервированными ключевыми словами в MySQL/MariaDB, поэтому их нельзя использовать как имена столбцов без экранирования.

## Исправления

### 1. В CREATE TABLE (database.py, строки ~47-62)
**Было:**
```sql
conditions TEXT,
password VARCHAR(255),
```

**Стало:**
```sql
`conditions` TEXT,
`password` VARCHAR(255),
```

### 2. В INSERT запросах (database.py, строки ~198-203)
**Было:**
```sql
INSERT INTO deals (seller_id, amount, conditions, password) 
INSERT INTO deals (buyer_id, amount, conditions, password) 
```

**Стало:**
```sql
INSERT INTO deals (seller_id, amount, `conditions`, `password`) 
INSERT INTO deals (buyer_id, amount, `conditions`, `password`) 
```

### 3. В SELECT запросах (database.py, строка ~224)
**Было:**
```sql
SELECT seller_id, buyer_id, password FROM deals WHERE id = %s
```

**Стало:**
```sql
SELECT seller_id, buyer_id, `password` FROM deals WHERE id = %s
```

## Результат
- ✅ SQL синтаксис теперь корректен
- ✅ Зарезервированные слова экранированы обратными кавычками
- ✅ Все SQL запросы обновлены соответственно
- ✅ Бот должен запускаться без ошибок SQL

## Что делать дальше
1. Скопируйте исправленный `database.py` на хостинг как `database_manager.py`
2. Скопируйте `bot.py` на хостинг как `main.py`
3. Запустите бота - ошибка SQL должна исчезнуть

## Файлы для копирования на хостинг
- `database.py` → `database_manager.py` (исправлен)
- `bot.py` → `main.py` (без изменений)