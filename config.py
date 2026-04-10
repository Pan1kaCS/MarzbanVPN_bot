"""
Конфигурация бота: загрузка .env, константы, тарифы
"""
import os
from dotenv import load_dotenv
from datetime import timedelta
from typing import Dict, Any

# Загрузка .env
load_dotenv()

# Основные настройки
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
DB_PATH = os.getenv('DB_PATH', 'bot.db')

# Marzban
MARZBAN_URL = os.getenv('MARZBAN_URL', '').rstrip('/')
MARZBAN_TOKEN = os.getenv('MARZBAN_TOKEN')

# YooMoney
YOOMOONEY_WALLET = os.getenv('YOOMOONEY_WALLET')
YOOMOONEY_TOKEN = os.getenv('YOOMOONEY_TOKEN')

# Рефералы
REFERRAL_DAYS_BONUS = int(os.getenv('REFERRAL_DAYS_BONUS', '3'))
REFERRAL_PERCENT = float(os.getenv('REFERRAL_PERCENT', '0.10'))

# Тарифы {plan_key: {'days':int, 'gb':int, 'price':int}}
PLANS: Dict[str, Dict[str, int]] = {
    '30d': {'days': 30, 'gb': 50, 'price': 300},
    '90d': {'days': 90, 'gb': 200, 'price': 700},
    '180d': {'days': 180, 'gb': 500, 'price': 1200},
    '365d': {'days': 365, 'gb': 1000, 'price': 2000}
}

PLAN_EMOJIS = {
    '30d': '📱',
    '90d': '💻',
    '180d': '⚡',
    '365d': '🔥'
}

# Маркировка платежей
PAYMENT_PREFIX = 'VPN_'

# Уведомления за N дней
EXPIRE_NOTIFY_DAYS = 3

# Клавиатуры (тексты)
MAIN_MENU = [
    ['🛒 Купить VPN', '👤 Мой профиль'],
    ['📊 Моя подписка', '🔗 Рефералы'],
    ['❓ Помощь']
]

ADMIN_MENU = [
    ['📈 Статистика', '👥 Пользователи'],
    ['📢 Рассылка', '💰 Доходы'],
    ['🔧 Админ помощь']
]

def validate_config() -> bool:
    """Проверка обязательных переменных"""
    required = ['BOT_TOKEN', 'ADMIN_ID', 'MARZBAN_URL', 'MARZBAN_TOKEN', 'YOOMOONEY_WALLET', 'YOOMOONEY_TOKEN']
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise ValueError(f"Отсутствуют переменные: {', '.join(missing)}")
    if ADMIN_ID <= 0:
        raise ValueError("ADMIN_ID должен быть числом > 0")
    return True

if __name__ == '__main__':
    validate_config()
    print("✅ Конфигурация OK")

