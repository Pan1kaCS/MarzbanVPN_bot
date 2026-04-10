"""
Админ панель
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_db, User, Payment, Mailing
from datetime import datetime
import config
import logging

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.ADMIN_ID:
        await update.message.reply_text('❌ Нет доступа')
        return
    
    keyboard = [[InlineKeyboardButton(text, callback_data=f'admin_{text.lower().replace(' ', '_')}')] 
                for text in [btn[0] for row in config.ADMIN_MENU for btn in row]]
    keyboard.append([[InlineKeyboardButton('🔙 Главное меню', callback_data='main_menu')]])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('🔧 Админ панель:', reply_markup=reply_markup)

async def admin_stats(update, reply=True):
    db = next(get_db())
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active).count()
    total_payments = db.query(Payment).filter(Payment.status == 'paid').count()
    total_income = db.query(Payment).filter(Payment.status == 'paid').with_entities(func.sum(Payment.amount)).scalar() or 0
    
    text = f"""
📈 Статистика:
👥 Всего пользователей: {total_users}
✅ Активных: {active_users}
💰 Продаж: {total_payments}
💵 Доход: {total_income:.0f}₽
    """
    
    if reply:
        await update.callback_query.edit_message_text(text)
    else:
        await update.message.reply_text(text)

async def admin_users(update):
    # Список пользователей (pagination TODO)
    db = next(get_db())
    users = db.query(User).limit(10).all()
    text = '👥 Последние пользователи:\n\n'
    for u in users:
        text += f"ID {u.telegram_id} - @{u.username or 'no'} - {u.plan_type or 'no'} - {u.expire_date}\n"
    
    keyboard = [[InlineKeyboardButton('🔙 Админ меню', callback_data='admin_статистика')]]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.ADMIN_ID:
        return
    # Сохранить сообщение для рассылки
    # TODO: state for message input
    await update.message.reply_text('📢 Отправьте сообщение для рассылки (HTML поддержка)')

async def give_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.ADMIN_ID:
        return
    
    args = context.args
    if len(args) < 3:
        await update.message.reply_text('/give @username days gb')
        return
    
    username = args[0][1:]  # без @
    days = int(args[1])
    gb = int(args[2])
    
    # Найти/create user, create marzban user
    db = next(get_db())
    user = db.query(User).filter(User.username.ilike(username)).first()
    if not user:
        await update.message.reply_text('Пользователь не найден')
        return
    
    # Create marzban
    marzban_username = f"admin_{user.telegram_id}"
    result = marzban.create_user(marzban_username, gb, days)
    if result:
        user.marzban_username = marzban_username
        user.subscription_url = marzban.get_subscription_url(marzban_username)
        user.plan_type = f"admin_{days}d"
        user.data_limit_gb = gb
        user.expire_date = datetime.utcnow() + timedelta(days=days)
        db.commit()
        await update.message.reply_text(f'✅ Выдана подписка {user.telegram_id}')
    else:
        await update.message.reply_text('❌ Ошибка Marzban')

async def cmd_block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /block @username
    pass  # TODO delete marzban user, set inactive

# Другие админ команды /income = admin_stats income only

