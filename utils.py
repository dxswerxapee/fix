import random
import string
import qrcode
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

def generate_captcha():
    """Генерирует капчу с выбором животного"""
    animals = ['🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐨', '🐯', '🦁', '🐮', '🐷', '🐸', '🐵']
    correct_animal = random.choice(animals)
    
    # Создаем список из 6 животных, включая правильный
    options = [correct_animal]
    while len(options) < 6:
        animal = random.choice(animals)
        if animal not in options:
            options.append(animal)
    
    # Перемешиваем варианты
    random.shuffle(options)
    
    return {
        'correct_animal': correct_animal,
        'options': options
    }

def generate_crypto_address(crypto_type):
    """Генерирует криптовалютный адрес (для демонстрации)"""
    addresses = {
        'TRC20': 'TUfach6g9gPDBTrRsy1jMWfd37z6RQLEB4',
        'BTC': '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
        'BNB': 'bnb1grpf0955h0ykzq3ar5nmum7y6gdfl6lxfn46h2',
        'TRON': 'TLPpXqSKqKWAjQTwKzYqnRkUJEK69A2HE9'
    }
    return addresses.get(crypto_type, addresses['TRC20'])

def generate_qr_code(data):
    """Генерирует QR код и возвращает его как BytesIO объект"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        bio = BytesIO()
        img.save(bio, format='PNG')
        bio.seek(0)
        
        return bio
    except Exception as e:
        logger.error(f"Ошибка генерации QR кода: {e}")
        return None

def format_deal_status(status):
    """Форматирует статус сделки для отображения"""
    status_map = {
        'waiting_partner': 'Ожидание партнера',
        'waiting_payment': 'Ожидание оплаты',
        'payment_sent': 'Оплата отправлена',
        'completed': 'Завершена',
        'cancelled': 'Отменена'
    }
    return status_map.get(status, status)

def format_role(deal_id, user_id, seller_id, buyer_id):
    """Определяет роль пользователя в сделке"""
    if user_id == seller_id:
        return 'Продавец'
    elif user_id == buyer_id:
        return 'Покупатель'
    else:
        return 'Неизвестно'

def validate_amount(amount_str):
    """Проверяет корректность суммы"""
    try:
        amount = float(amount_str)
        if amount <= 0:
            return None, "Сумма должна быть больше 0"
        if amount > 1000000:
            return None, "Сумма слишком большая"
        return amount, None
    except ValueError:
        return None, "Некорректный формат суммы"

def validate_password(password):
    """Проверяет корректность пароля"""
    if len(password) < 4:
        return False, "Пароль должен содержать минимум 4 символа"
    if len(password) > 50:
        return False, "Пароль слишком длинный"
    return True, None