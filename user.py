"""
Обработчики - финальная без _chat_data error
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_db, User, get_user
from datetime import datetime
import config
import logging
from payments import create_invoice
import base64

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = next(get_db())
    db_user = get_user(db, user.id)
    
    if not db_user:
        db_user = User(
            telegram_id=user.id,
            username=user.username,
            full_name=user.full_name,
            referral_code=base64.b64encode(str(user.id).encode()).decode()[:8]
        )
        db.add(db_user)
        db.commit()
    
    is_admin = user.id == config.ADMIN_ID
    await show_main_menu(update.message, is_admin)

async def show_main_menu(message, is_admin=False):
    keyboard = [
        [InlineKeyboardButton("🛒 Купить VPN", callback_data="buy_vpn"), InlineKeyboardButton("👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton("📊 Подписка", callback_data="subscription"), InlineKeyboardButton("🔗 Рефералы", callback_data="referrals")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton("🔧 Админ", callback_data="admin_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text('🏠 Главное меню:', reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    logging.info(f"Clicked: {data}")
    
    is_admin = query.from_user.id == config.ADMIN_ID
    
    try:
        if data == "buy_vpn":
            await show_plans(query)
        elif data == "profile":
            await show_profile(query)
        elif data == "subscription":
            await show_subscription(query)
        elif data == "referrals":
            await show_referrals(query)
        elif data == "help":
            await show_help(query)
        elif data == "admin_menu" and is_admin:
            await context.bot.send_message(query.from_user.id, "🔧 Админ панель /admin или /stats")
        elif data.startswith("buy_"):
            plan = data[4:]
            await buy_plan(query, plan)
        elif data == "main_menu":
            await show_main_menu(query.message)
    except Exception as e:
        logging.error(f"Button {data}: {e}")
        await query.answer("Ошибка")

async def show_plans(query):
    keyboard = []
    for plan, info in config.PLANS.items():
        emoji = config.PLAN_EMOJIS.get(plan, '')
        text = f"{emoji} {info['days']}д / {info['gb']}GB — {info['price']}₽"
        keyboard.append([InlineKeyboardButton(text, callback_data=f"buy_{plan}")])
    keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text('💳 Выберите тариф:', reply_markup=reply_markup)

async def buy_plan(query, plan):
    info = config.PLANS[plan]
    invoice_url, payment_id = create_invoice(query.from_user.id, info['price'], plan)
    
    keyboard = [
        [InlineKeyboardButton("💳 Оплатить", url=invoice_url)],
        [InlineKeyboardButton("✅ Проверить", callback_data=f"check_{payment_id}")],
        [InlineKeyboardButton("🔙 Тарифы", callback_data="buy_vpn")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"Тариф: {info['days']} дней / {info['gb']} GB\nСумма: {info['price']} ₽\nID счёта: {payment_id}"
    await query.edit_message_text(text, reply_markup=reply_markup)

async def show_profile(query):
    db = next(get_db())
    user = get_user(db, query.from_user.id)
    balance = getattr(user, 'referral_balance', 0)
    ref_code = getattr(user, 'referral_code', '')
    ref_link = f"https://t.me/{config.BOT_USERNAME}?start={ref_code}" if ref_code else "N/A"
    
    text = f"👤 {query.from_user.full_name}\nID: {query.from_user.id}\nБаланс: {balance} ₽\nРеф. ссылка: {ref_link}"
    keyboard = [[InlineKeyboardButton("🔙 Меню", callback_data="main_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_subscription(query):
    db = next(get_db())
    user = get_user(db, query.from_user.id)
    if not user or not user.subscription_url:
        text = "Подписка не активна. Купите VPN."
    else:
        days_left = (user.expire_date - datetime.utcnow()).days if user.expire_date else 0
        text = f"Статус: активна ({days_left} дней)\n{user.subscription_url}"
    keyboard = [[InlineKeyboardButton("🔙 Меню", callback_data="main_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_referrals(query):
    text = "Рефералка: делитесь ссылкой из профиля"
    keyboard = [[InlineKeyboardButton("🔙 Меню", callback_data="main_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_help(query):
    text = "Помощь:\n/start - меню\n/admin - админ\n/give @user days gb"
    keyboard = [[InlineKeyboardButton("🔙 Меню", callback_data="main_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

