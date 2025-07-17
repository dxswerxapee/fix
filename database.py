import mysql.connector
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.host = os.getenv('DB_HOST')
        self.user = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.database = os.getenv('DB_NAME')
        self.connection = None
        
    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                autocommit=True
            )
            logger.info("База данных подключена успешно")
            return True
        except mysql.connector.Error as err:
            logger.error(f"Ошибка подключения к базе данных: {err}")
            return False
    
    def create_tables(self):
        if not self.connection:
            if not self.connect():
                return False
                
        cursor = self.connection.cursor()
        
        # Таблица пользователей
        users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY,
            username VARCHAR(255),
            first_name VARCHAR(255),
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_verified BOOLEAN DEFAULT FALSE
        )
        """
        
        # Таблица сделок
        deals_table = """
        CREATE TABLE IF NOT EXISTS deals (
            id INT AUTO_INCREMENT PRIMARY KEY,
            seller_id BIGINT,
            buyer_id BIGINT,
            amount DECIMAL(10,2),
            `conditions` TEXT,
            `password` VARCHAR(255),
            status ENUM('waiting_partner', 'waiting_payment', 'payment_sent', 'completed', 'cancelled') DEFAULT 'waiting_partner',
            payment_method VARCHAR(50),
            payment_address VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seller_id) REFERENCES users(id),
            FOREIGN KEY (buyer_id) REFERENCES users(id)
        )
        """
        
        # Таблица сессий капчи
        captcha_table = """
        CREATE TABLE IF NOT EXISTS captcha_sessions (
            user_id BIGINT PRIMARY KEY,
            captcha_code VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        try:
            cursor.execute(users_table)
            cursor.execute(deals_table)
            cursor.execute(captcha_table)
            logger.info("Таблицы созданы успешно")
            return True
        except mysql.connector.Error as err:
            logger.error(f"Ошибка создания таблиц: {err}")
            return False
        finally:
            cursor.close()
    
    def add_user(self, user_id, username=None, first_name=None):
        if not self.connection:
            if not self.connect():
                return False
                
        cursor = self.connection.cursor()
        try:
            query = """
            INSERT INTO users (id, username, first_name) 
            VALUES (%s, %s, %s) 
            ON DUPLICATE KEY UPDATE 
            username = VALUES(username), 
            first_name = VALUES(first_name)
            """
            cursor.execute(query, (user_id, username, first_name))
            return True
        except mysql.connector.Error as err:
            logger.error(f"Ошибка добавления пользователя: {err}")
            return False
        finally:
            cursor.close()
    
    def verify_user(self, user_id):
        if not self.connection:
            if not self.connect():
                return False
                
        cursor = self.connection.cursor()
        try:
            query = "UPDATE users SET is_verified = TRUE WHERE id = %s"
            cursor.execute(query, (user_id,))
            return True
        except mysql.connector.Error as err:
            logger.error(f"Ошибка верификации пользователя: {err}")
            return False
        finally:
            cursor.close()
    
    def is_user_verified(self, user_id):
        if not self.connection:
            if not self.connect():
                return False
                
        cursor = self.connection.cursor()
        try:
            query = "SELECT is_verified FROM users WHERE id = %s"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            return result[0] if result else False
        except mysql.connector.Error as err:
            logger.error(f"Ошибка проверки верификации: {err}")
            return False
        finally:
            cursor.close()
    
    def save_captcha(self, user_id, captcha_code):
        if not self.connection:
            if not self.connect():
                return False
                
        cursor = self.connection.cursor()
        try:
            query = """
            INSERT INTO captcha_sessions (user_id, captcha_code) 
            VALUES (%s, %s) 
            ON DUPLICATE KEY UPDATE 
            captcha_code = VALUES(captcha_code), 
            created_at = CURRENT_TIMESTAMP
            """
            cursor.execute(query, (user_id, captcha_code))
            return True
        except mysql.connector.Error as err:
            logger.error(f"Ошибка сохранения капчи: {err}")
            return False
        finally:
            cursor.close()
    
    def verify_captcha(self, user_id, captcha_code):
        if not self.connection:
            if not self.connect():
                return False
                
        cursor = self.connection.cursor()
        try:
            query = "SELECT captcha_code FROM captcha_sessions WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            if result and result[0] == captcha_code:
                # Удаляем капчу после успешной проверки
                delete_query = "DELETE FROM captcha_sessions WHERE user_id = %s"
                cursor.execute(delete_query, (user_id,))
                return True
            return False
        except mysql.connector.Error as err:
            logger.error(f"Ошибка проверки капчи: {err}")
            return False
        finally:
            cursor.close()
    
    def create_deal(self, creator_id, amount, conditions, password, role):
        if not self.connection:
            if not self.connect():
                return None
                
        cursor = self.connection.cursor()
        try:
            if role == 'seller':
                query = """
                INSERT INTO deals (seller_id, amount, `conditions`, `password`) 
                VALUES (%s, %s, %s, %s)
                """
            else:  # buyer
                query = """
                INSERT INTO deals (buyer_id, amount, `conditions`, `password`) 
                VALUES (%s, %s, %s, %s)
                """
            
            cursor.execute(query, (creator_id, amount, conditions, password))
            deal_id = cursor.lastrowid
            return deal_id
        except mysql.connector.Error as err:
            logger.error(f"Ошибка создания сделки: {err}")
            return None
        finally:
            cursor.close()
    
    def join_deal(self, deal_id, user_id, password):
        if not self.connection:
            if not self.connect():
                return False
                
        cursor = self.connection.cursor()
        try:
            # Проверяем пароль и получаем информацию о сделке
            query = "SELECT seller_id, buyer_id, `password` FROM deals WHERE id = %s"
            cursor.execute(query, (deal_id,))
            result = cursor.fetchone()
            
            if not result or result[2] != password:
                return False
            
            seller_id, buyer_id, _ = result
            
            # Определяем, кто присоединяется
            if seller_id is None:
                update_query = "UPDATE deals SET seller_id = %s, status = 'waiting_payment' WHERE id = %s"
                cursor.execute(update_query, (user_id, deal_id))
            elif buyer_id is None:
                update_query = "UPDATE deals SET buyer_id = %s, status = 'waiting_payment' WHERE id = %s"
                cursor.execute(update_query, (user_id, deal_id))
            else:
                return False  # Сделка уже полная
            
            return True
        except mysql.connector.Error as err:
            logger.error(f"Ошибка присоединения к сделке: {err}")
            return False
        finally:
            cursor.close()
    
    def get_deal(self, deal_id):
        if not self.connection:
            if not self.connect():
                return None
                
        cursor = self.connection.cursor()
        try:
            query = "SELECT * FROM deals WHERE id = %s"
            cursor.execute(query, (deal_id,))
            result = cursor.fetchone()
            
            if result:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, result))
            return None
        except mysql.connector.Error as err:
            logger.error(f"Ошибка получения сделки: {err}")
            return None
        finally:
            cursor.close()
    
    def get_user_deals(self, user_id):
        if not self.connection:
            if not self.connect():
                return []
                
        cursor = self.connection.cursor()
        try:
            query = "SELECT * FROM deals WHERE seller_id = %s OR buyer_id = %s ORDER BY created_at DESC"
            cursor.execute(query, (user_id, user_id))
            results = cursor.fetchall()
            
            deals = []
            columns = [desc[0] for desc in cursor.description]
            for result in results:
                deals.append(dict(zip(columns, result)))
            
            return deals
        except mysql.connector.Error as err:
            logger.error(f"Ошибка получения сделок пользователя: {err}")
            return []
        finally:
            cursor.close()
    
    def update_deal_payment(self, deal_id, payment_method, payment_address):
        if not self.connection:
            if not self.connect():
                return False
                
        cursor = self.connection.cursor()
        try:
            query = "UPDATE deals SET payment_method = %s, payment_address = %s WHERE id = %s"
            cursor.execute(query, (payment_method, payment_address, deal_id))
            return True
        except mysql.connector.Error as err:
            logger.error(f"Ошибка обновления платежных данных: {err}")
            return False
        finally:
            cursor.close()
    
    def close(self):
        if self.connection:
            self.connection.close()
            logger.info("Соединение с базой данных закрыто")