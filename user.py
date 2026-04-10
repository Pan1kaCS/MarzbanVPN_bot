"""
Обработчики для пользователей
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_db, User
import config
import logging
from marzban_api import marzban
from payments import create_invoice

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = next(get_db())
    db_user = get_user(db, user.id)
    
    if not db_user:
        # Регистрация
        db_user = User(
            telegram_id=user.id,
            username=user.username,
            full_name=user.full_name,
            referral_code=base64.b64encode(str(user.id).encode()).decode()[:8]
        )
        db.add(db_user)
        db.commit()
        logging.info(f"New user registered: {user.id}")
    
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(text, callback_data=text.replace(' ', '_')) 
                 for text in row] for row in config.MAIN_MENU]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('🏠 Главное меню:', reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.lower()
    
    if data == 'купить_vpn':
        await show_plans(query)
    elif data == 'мой_профиль':
        await show_profile(query)
    elif data == 'моя_подписка':
        await show_subscription(query)
    elif data == 'рефералы':
        await show_referrals(query)
    elif data == 'помощь':
        await show_help(query)
    elif data.startswith('buy_'):
        plan = data[4:]
        await buy_plan(query, plan)

async def show_plans(update, reply=True):
    keyboard = []
    for plan, info in config.PLANS.items():
        text = f"{config.PLAN_EMOJIS.get(plan, '')} {info['days']}д / {info['gb']}GB — {info['price']}₽"
        keyboard.append([InlineKeyboardButton(text, callback_data=f'buy_{plan}')])
    
    keyboard.append([[InlineKeyboardButton('🔙 Назад', callback_data='main_menu')]])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = '💳 Выберите тариф:'
    if reply:
        await update.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def buy_plan(query, plan: str):
    info = config.PLANS[plan]
    invoice_url, payment_id = create_invoice(query.from_user.id, info['price'], plan)
    
    keyboard = [
        [InlineKeyboardButton('💳 Оплатить', url=invoice_url)],
        [InlineKeyboardButton('✅ Проверить оплату', callback_data=f'check_{payment_id}')],
        [InlineKeyboardButton('🔙 Назад', callback_data='buy_vpn')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"✅ Счёт создан #{payment_id}\n\n"
        f"{config.PLAN_EMOJIS.get(plan, '')} {info['days']} дней / {info['gb']} GB\n"
        f"💰 Сумма: {info['price']} ₽\n\n"
        "Перейдите по ссылке и оплатите. Затем нажмите 'Проверить оплату'",
        reply_markup=reply_markup
    )

import base64

async def show_profile(query):
    db = next(get_db())
    user = get_user(db, query.from_user.id)
    
    balance = user.referral_balance if user else 0
    ref_link = f"https://t.me/{(await query.bot.get_me()).username}?start={user.referral_code}" if user.referral_code else "N/A"
    
    text = f"👤 {query.from_user.full_name}\n"
    text += f"🆔 ID: {query.from_user.id}\n"
    text += f"💰 Баланс рефералов: {balance:.0f}₽\n"
    text += f"🔗 Ваша ссылка: {ref_link}"
    
    keyboard = [[InlineKeyboardButton('🔙 Главное меню', callback_data='main_menu')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_subscription(query):
    db = next(get_db())
    user = get_user(db, query.from_user.id)
    
    if not user or not user.subscription_url:
        text = "❌ Подписка не активна"
    else:
        days_left = (user.expire_date - datetime.utcnow()).days if user.expire_date else 0
        status = "✅ Активна" if days_left > 0 else "⏰ Истекла"
        text = f"📡 {status}\n\n{user.subscription_url}"
    
    keyboard = [[InlineKeyboardButton('🔙 Главное меню', callback_data='main_menu')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_referrals(query):
    # TODO: список рефералов, их покупки
    text = "🔗 Реферальная система\n\nПриглашайте друзей по вашей ссылке:\n"
    # Get ref link...
    keyboard = [[InlineKeyboardButton('🔙 Главное меню', callback_data='main_menu')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_help(query):
    text = """
ℹ️ Помощь:

• /start - главное меню
• 🛒 Купить VPN - выбрать тариф и оплатить
• 👤 Профиль - баланс, реф. ссылка
• 📊 Подписка - статус и ссылка

💳 Оплата через YooMoney
🔗 Подписка для приложений VPN
    """
    keyboard = [[InlineKeyboardButton('🔙 Главное меню', callback_data='main_menu')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# Дополнительно check payment callback в bot.py

