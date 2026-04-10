# 🛡️ MarzbanVPN Telegram Bot

## Описание
**Полноценный Telegram бот для продажи VPN-подписок** через панель управления **Marzban**. 

Автоматизирует:
- Регистрацию и управление пользователями
- Продажу тарифов с оплатой через **YooMoney**
- Создание пользователей в **Marzban** 
- Генерацию подписочных ссылок
- **Реферальную систему** (10% кэшбэк + бонусные дни)
- **Админ-панель** со статистикой и рассылкой

## 🎯 Функционал

### 👤 Пользователи:
- `/start` - регистрация + главное меню
- 🛒 **Купить VPN** - выбор тарифа → оплата → активация
- 👤 **Профиль** - баланс, реф. ссылка 
- 📊 **Моя подписка** - статус + ссылка
- 🔗 **Рефералы** - уникальная ссылка
- ❓ **Помощь**

**Тарифы:**
| Тариф | Дней | Трафик | Цена |
|-------|------|--------|------|
| 📱 30д | 30 | 50 GB | 300₽ |
| 💻 90д | 90 | 200 GB | 700₽ |
| ⚡ 180д | 180 | 500 GB | 1200₽ |
| 🔥 365д | 365 | 1000 GB | 2000₽ |

### 🔧 Админ (/admin):
- 📈 **Статистика** - пользователи, доход
- 👥 **Список пользователей** 
- 📢 **Рассылка** (HTML)
- `/give @username days gb` - ручная подписка
- `/block @username` - блокировка
- `/income` - доходы

### ⚙️ Автоматика:
- Проверка оплат после создания счёта
- Ежедневные уведомления об истечении (за 3 дня)
- Бонусы рефералам (3 дня + 10% cashback)

## 🚀 Установка (локально/Windows)

```bash
cd /path/to/project
pip install -r requirements.txt
cp .env.example .env
# Edit .env: BOT_TOKEN, ADMIN_ID, MARZBAN_*, YOOMOONEY_*
python bot.py
```

## 🖥️ Развёртывание на VPS (Ubuntu/Debian) из GitHub

```bash
# 1. Обновление системы
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git screen ufw -y

# 2. Клонировать репозиторий (замените URL на ваш GitHub)
git clone https://github.com/yourusername/marzban-vpn-bot.git
cd marzban-vpn-bot

# 3. Virtualenv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Конфиг
cp .env.example .env
nano .env  # Настройте токены!

# 5. Firewall
sudo ufw allow 22
sudo ufw allow 443/tcp  # если нужен
sudo ufw enable

# 6. Тестовый запуск
python bot.py
# Ctrl+C после проверки

# 7. Screen для фона
screen -S vpn_bot
source venv/bin/activate
python bot.py
# Ctrl+A D - detach

# 8. Systemd сервис (рекомендуется)
sudo nano /etc/systemd/system/vpnbot.service
```

**vpnbot.service содержимое:**
```ini
[Unit]
Description=MarzbanVPN Telegram Bot
After=network.target

[Service]
Type=simple
User=root  # или ваш user
WorkingDirectory=/path/to/marzban-vpn-bot
Environment=PATH=/path/to/marzban-vpn-bot/venv/bin
ExecStart=/path/to/marzban-vpn-bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Активация сервиса
sudo systemctl daemon-reload
sudo systemctl enable vpnbot
sudo systemctl start vpnbot
sudo systemctl status vpnbot  # логи

# Логи:
journalctl -u vpnbot -f
```

## 🔑 Настройка ключей

1. **BOT_TOKEN**: @BotFather → New Bot
2. **ADMIN_ID**: @userinfobot 
3. **Marzban**: Panel → Admin → API → JWT Token
4. **YooMoney**: 
   - Личный кошелёк: Создайте форму приёма платежей
   - Бизнес: YooKassa API

## 🧪 Тестирование
```
# В Telegram:
/start
🛒 Купить → выберите тариф → оплатите тест
/admin  # статистика
/give @testuser 30 50
```

## 📁 Структура проекта
```
├── bot.py          # Главный файл
├── config.py       # Настройки
├── database.py     # SQLite ORM
├── marzban_api.py  # Marzban
├── payments.py     # YooMoney
├── user.py         # User handlers
├── admin.py        # Admin
├── requirements.txt
└── README.md
```

## 🐛 Проблемы?
- `ModuleNotFoundError`: `pip install -r requirements.txt`
- DB ошибки: права на bot.db
- API: проверьте .env токены
- Логи: в терминале или `journalctl -u vpnbot`

**Push на GitHub и deploy!** 🚀
