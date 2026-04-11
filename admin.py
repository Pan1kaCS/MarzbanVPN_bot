"""
Админ панель - полная рабочая
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import config
from database import get_db, User, Payment
from marzban_api import marzban
from datetime import datetime, timedelta
import logging

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.ADMIN_ID:
        await update.message.reply_text('❌ Доступ запрещен. ADMIN_ID: {}'.format(config.ADMIN_ID))
        return
    
    keyboard = [
        [InlineKeyboardButton("📈 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton("💰 Доходы", callback_data="admin_income")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('🔧 Админ панель:', reply_markup=reply_markup)

async def admin_stats(update, context):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
    else:
        query = None
    
    db = next(get_db())
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    paid_payments = db.query(Payment).filter(Payment.status == 'paid').count()
    total_income = db.query(Payment).filter(Payment.status == 'paid').with_entities(sum(Payment.amount)).scalar() or 0
    
    text = f"""
📈 **Статистика**
👥 Всего: {total_users}
✅ Активных: {active_users}
💰 Продаж: {paid_payments}
💵 Доход: {total_income:.0f} руб
    """
    keyboard = [[InlineKeyboardButton("🔙 Админ меню", callback_data="admin_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def admin_users(update, context):
    db = next(get_db())
    users = db.query(User).order_by(User.created_at.desc()).limit(10).all()
    text = "👥 Последние пользователи:\n\n"
    for u in users:
        status = "✅" if u.is_active else "❌"
        expire = u.expire_date.strftime("%d.%m") if u.expire_date else "N/A"
        text += f"{status} ID {u.telegram_id} (@{u.username or 'no'}) - {u.plan_type} - {expire}\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Админ меню", callback_data="admin_menu")]]
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def give_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.ADMIN_ID:
        return
    
    args = context.args
    if len(args) < 3:
        await update.message.reply_text('Использование: /give @username days gb\nПример: /give dem0n_696 30 50')
        return
    
    username = args[0].lstrip('@')
    try:
        days = int(args[1])
        gb = int(args[2])
    except ValueError:
        await update.message.reply_text('Дни и GB должны быть числами')
        return
    
    db = next(get_db())
    user = db.query(User).filter((User.username == username) | (User.username.like(f"%{username}%"))).first()
    if not user:
        await update.message.reply_text(f'Пользователь @{username} не найден')
        return
    
    marzban_username = f"admin_{user.telegram_id}_{int(datetime.now().timestamp())}"
    result = marzban.create_user(marzban_username, gb, days)
    if result:
        user.marzban_username = marzban_username
        user.subscription_url = marzban.get_subscription_url(marzban_username)
        user.data_limit_gb = gb
        user.plan_type = f"admin_{days}d"
        user.expire_date = datetime.utcnow() + timedelta(days=days)
        user.is_active = True
        db.commit()
        text = f"✅ Подписка выдана @{username}:\n{user.subscription_url}"
    else:
        text = "❌ Ошибка создания в Marzban"
    
    await update.message.reply_text(text)

async def cmd_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await admin_stats(update, context)

async def cmd_block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.ADMIN_ID:
        return
    
    args = context.args
    if not args:
        await update.message.reply_text('/block @username')
        return
    
    username = args[0].lstrip('@')
    db = next(get_db())
    user = db.query(User).filter(User.username.like(f"%{username}%")).first()
    if not user:
        await update.message.reply_text('Пользователь не найден')
        return
    
    if marzban.delete_user(user.marzban_username):
        user.is_active = False
        user.subscription_url = None
        db.commit()
        await update.message.reply_text(f'✅ @{username} заблокирован')
    else:
        await update.message.reply_text('Ошибка блокировки')

# Callback handlers
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data == "admin_stats":
        await admin_stats(update, context)
    elif data == "admin_users":
        await admin_users(update, context)
    # add more

if __name__ == '__main__':
    print("Admin module OK")

