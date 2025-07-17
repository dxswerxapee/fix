import asyncio
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
import aiomysql
from config import MYSQL_CONFIG

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.pool = None
        
    async def initialize(self):
        """Инициализация пула соединений и создание таблиц"""
        try:
            self.pool = await aiomysql.create_pool(
                host=MYSQL_CONFIG['host'],
                port=MYSQL_CONFIG['port'],
                user=MYSQL_CONFIG['user'],
                password=MYSQL_CONFIG['password'],
                db=MYSQL_CONFIG['database'],
                charset='utf8mb4',
                autocommit=True,
                maxsize=20,
                minsize=1
            )
            
            await self._create_tables()
            logger.info("✅ База данных инициализирована успешно")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise
    
    async def _create_tables(self):
        """Создание таблиц базы данных"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Таблица пользователей
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        username VARCHAR(255),
                        first_name VARCHAR(255),
                        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE,
                        completed_deals INT DEFAULT 0,
                        total_volume DECIMAL(15,2) DEFAULT 0.00
                    ) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Таблица сделок
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS deals (
                        deal_id VARCHAR(36) PRIMARY KEY,
                        creator_id BIGINT NOT NULL,
                        buyer_id BIGINT DEFAULT NULL,
                        amount DECIMAL(15,2) NOT NULL,
                        condition TEXT NOT NULL,
                        password VARCHAR(255) NOT NULL,
                        status ENUM('active', 'joined', 'paid', 'completed', 'cancelled') DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (creator_id) REFERENCES users(user_id),
                        FOREIGN KEY (buyer_id) REFERENCES users(user_id),
                        INDEX idx_creator_status (creator_id, status),
                        INDEX idx_buyer_status (buyer_id, status),
                        INDEX idx_status (status)
                    ) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Таблица транзакций
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        transaction_id INT AUTO_INCREMENT PRIMARY KEY,
                        deal_id VARCHAR(36) NOT NULL,
                        user_id BIGINT NOT NULL,
                        transaction_type ENUM('payment', 'refund', 'release') NOT NULL,
                        amount DECIMAL(15,2) NOT NULL,
                        crypto_type ENUM('USDT_TRC20', 'TON') NOT NULL,
                        tx_hash VARCHAR(255),
                        status ENUM('pending', 'confirmed', 'failed') DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (deal_id) REFERENCES deals(deal_id) ON DELETE CASCADE,
                        FOREIGN KEY (user_id) REFERENCES users(user_id),
                        INDEX idx_deal_status (deal_id, status),
                        INDEX idx_user_type (user_id, transaction_type)
                    ) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Таблица логов действий
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS action_logs (
                        log_id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        deal_id VARCHAR(36),
                        action VARCHAR(100) NOT NULL,
                        details TEXT,
                        ip_address VARCHAR(45),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id),
                        INDEX idx_user_action (user_id, action),
                        INDEX idx_deal_action (deal_id, action),
                        INDEX idx_created_at (created_at)
                    ) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
    async def register_user(self, user_id: int, username: str, first_name: str) -> bool:
        """Регистрация нового пользователя"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "INSERT IGNORE INTO users (user_id, username, first_name) VALUES (%s, %s, %s)",
                        (user_id, username, first_name)
                    )
                    
                    # Логируем действие
                    await self._log_action(user_id, None, "user_registration", f"Username: {username}")
                    
                    return True
        except Exception as e:
            logger.error(f"Ошибка регистрации пользователя {user_id}: {e}")
            return False
    
    async def is_user_registered(self, user_id: int) -> bool:
        """Проверка регистрации пользователя"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT user_id FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    result = await cursor.fetchone()
                    return result is not None
        except Exception as e:
            logger.error(f"Ошибка проверки регистрации {user_id}: {e}")
            return False
    
    async def create_deal(self, deal_id: str, creator_id: int, amount: float, condition: str, password: str) -> bool:
        """Создание новой сделки"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """INSERT INTO deals (deal_id, creator_id, amount, condition, password) 
                           VALUES (%s, %s, %s, %s, %s)""",
                        (deal_id, creator_id, amount, condition, password)
                    )
                    
                    # Логируем действие
                    await self._log_action(creator_id, deal_id, "deal_created", f"Amount: {amount} USDT")
                    
                    return True
        except Exception as e:
            logger.error(f"Ошибка создания сделки {deal_id}: {e}")
            return False
    
    async def get_deal(self, deal_id: str) -> Optional[Dict[str, Any]]:
        """Получение информации о сделке"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        "SELECT * FROM deals WHERE deal_id = %s",
                        (deal_id,)
                    )
                    return await cursor.fetchone()
        except Exception as e:
            logger.error(f"Ошибка получения сделки {deal_id}: {e}")
            return None
    
    async def join_deal(self, deal_id: str, buyer_id: int) -> bool:
        """Присоединение покупателя к сделке"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Проверяем, что сделка активна и свободна
                    await cursor.execute(
                        "SELECT status, buyer_id FROM deals WHERE deal_id = %s",
                        (deal_id,)
                    )
                    result = await cursor.fetchone()
                    
                    if not result or result[0] != 'active' or result[1] is not None:
                        return False
                    
                    # Присоединяем покупателя
                    await cursor.execute(
                        "UPDATE deals SET buyer_id = %s, status = 'joined' WHERE deal_id = %s",
                        (buyer_id, deal_id)
                    )
                    
                    # Логируем действие
                    await self._log_action(buyer_id, deal_id, "deal_joined", "Buyer joined the deal")
                    
                    return True
        except Exception as e:
            logger.error(f"Ошибка присоединения к сделке {deal_id}: {e}")
            return False
    
    async def cancel_deal(self, deal_id: str) -> bool:
        """Отмена сделки"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE deals SET status = 'cancelled' WHERE deal_id = %s",
                        (deal_id,)
                    )
                    
                    # Логируем действие
                    await self._log_action(None, deal_id, "deal_cancelled", "Deal cancelled by creator")
                    
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка отмены сделки {deal_id}: {e}")
            return False
    
    async def get_active_deal_by_creator(self, creator_id: int) -> Optional[Dict[str, Any]]:
        """Получение активной сделки пользователя как создателя"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        """SELECT * FROM deals 
                           WHERE creator_id = %s AND status IN ('active', 'joined', 'paid')""",
                        (creator_id,)
                    )
                    return await cursor.fetchone()
        except Exception as e:
            logger.error(f"Ошибка поиска активной сделки создателя {creator_id}: {e}")
            return None
    
    async def is_user_in_active_deal(self, user_id: int) -> bool:
        """Проверка участия пользователя в активной сделке"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """SELECT COUNT(*) FROM deals 
                           WHERE (creator_id = %s OR buyer_id = %s) 
                           AND status IN ('active', 'joined', 'paid')""",
                        (user_id, user_id)
                    )
                    result = await cursor.fetchone()
                    return result[0] > 0
        except Exception as e:
            logger.error(f"Ошибка проверки активных сделок {user_id}: {e}")
            return False
    
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Получение статистики пользователя"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        "SELECT completed_deals, total_volume, registration_date FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    result = await cursor.fetchone()
                    
                    if result:
                        return {
                            'completed_deals': result['completed_deals'],
                            'total_volume': float(result['total_volume']),
                            'registration_date': result['registration_date'].strftime('%d.%m.%Y')
                        }
                    else:
                        return {'completed_deals': 0, 'total_volume': 0.0, 'registration_date': 'N/A'}
        except Exception as e:
            logger.error(f"Ошибка получения статистики {user_id}: {e}")
            return {'completed_deals': 0, 'total_volume': 0.0, 'registration_date': 'N/A'}
    
    async def get_user_deals(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение списка сделок пользователя"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        """SELECT deal_id, amount, status, created_at 
                           FROM deals 
                           WHERE creator_id = %s OR buyer_id = %s 
                           ORDER BY created_at DESC 
                           LIMIT %s""",
                        (user_id, user_id, limit)
                    )
                    return await cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка получения сделок пользователя {user_id}: {e}")
            return []
    
    async def add_transaction(self, deal_id: str, user_id: int, transaction_type: str, 
                            amount: float, crypto_type: str, tx_hash: str = None) -> bool:
        """Добавление транзакции"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """INSERT INTO transactions 
                           (deal_id, user_id, transaction_type, amount, crypto_type, tx_hash) 
                           VALUES (%s, %s, %s, %s, %s, %s)""",
                        (deal_id, user_id, transaction_type, amount, crypto_type, tx_hash)
                    )
                    
                    # Логируем действие
                    await self._log_action(user_id, deal_id, f"transaction_{transaction_type}", 
                                         f"Amount: {amount}, Type: {crypto_type}")
                    
                    return True
        except Exception as e:
            logger.error(f"Ошибка добавления транзакции: {e}")
            return False
    
    async def complete_deal(self, deal_id: str) -> bool:
        """Завершение сделки"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Получаем данные сделки
                    await cursor.execute(
                        "SELECT creator_id, buyer_id, amount FROM deals WHERE deal_id = %s",
                        (deal_id,)
                    )
                    deal_data = await cursor.fetchone()
                    
                    if not deal_data:
                        return False
                    
                    creator_id, buyer_id, amount = deal_data
                    
                    # Обновляем статус сделки
                    await cursor.execute(
                        "UPDATE deals SET status = 'completed' WHERE deal_id = %s",
                        (deal_id,)
                    )
                    
                    # Обновляем статистику пользователей
                    for user_id in [creator_id, buyer_id]:
                        if user_id:
                            await cursor.execute(
                                """UPDATE users 
                                   SET completed_deals = completed_deals + 1, 
                                       total_volume = total_volume + %s 
                                   WHERE user_id = %s""",
                                (amount, user_id)
                            )
                    
                    # Логируем действие
                    await self._log_action(None, deal_id, "deal_completed", f"Amount: {amount}")
                    
                    return True
        except Exception as e:
            logger.error(f"Ошибка завершения сделки {deal_id}: {e}")
            return False
    
    async def _log_action(self, user_id: int, deal_id: str, action: str, details: str = None):
        """Логирование действий пользователей"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "INSERT INTO action_logs (user_id, deal_id, action, details) VALUES (%s, %s, %s, %s)",
                        (user_id, deal_id, action, details)
                    )
        except Exception as e:
            logger.error(f"Ошибка логирования действия: {e}")
    
    async def get_admin_stats(self) -> Dict[str, Any]:
        """Получение административной статистики"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    stats = {}
                    
                    # Общее количество пользователей
                    await cursor.execute("SELECT COUNT(*) FROM users")
                    stats['total_users'] = (await cursor.fetchone())[0]
                    
                    # Активные сделки
                    await cursor.execute("SELECT COUNT(*) FROM deals WHERE status IN ('active', 'joined', 'paid')")
                    stats['active_deals'] = (await cursor.fetchone())[0]
                    
                    # Завершенные сделки
                    await cursor.execute("SELECT COUNT(*) FROM deals WHERE status = 'completed'")
                    stats['completed_deals'] = (await cursor.fetchone())[0]
                    
                    # Общий объем
                    await cursor.execute("SELECT SUM(amount) FROM deals WHERE status = 'completed'")
                    result = await cursor.fetchone()
                    stats['total_volume'] = float(result[0]) if result[0] else 0.0
                    
                    return stats
        except Exception as e:
            logger.error(f"Ошибка получения административной статистики: {e}")
            return {}
    
    async def close(self):
        """Закрытие пула соединений"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("🔒 Пул соединений с БД закрыт")