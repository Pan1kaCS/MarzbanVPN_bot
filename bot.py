"""
Главный файл бота
"""
import asyncio
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, 
    ContextTypes, filters, ChatMemberHandler
)
import config
from database import init_db, get_db, User
from user import start, button_handler, show_plans, show_profile, show_subscription, show_referrals, show_help
from admin import admin_menu, admin_stats
from payments import process_paid_payment, check_payment_status
from marzban_api import marzban
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import base64  # for referral code

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def activate_subscription(telegram_id: int, plan: str):
    """Активация после оплаты"""
    db = next(get_db())
    user = get_user(db, telegram_id)
    if not user:
        return False
    
    info = config.PLANS[plan]
    username = f"user_{user.telegram_id}_{int(datetime.now().timestamp())}"
    
    # Create Marzban user
    result = marzban.create_user(username, info['data_limit_gb'], info['days'])
    if result:
        user.marzban_username = username
        user.subscription_url = marzban.get_subscription_url(username)
        user.plan_type = plan
        user.data_limit_gb = info['data_limit_gb']
        user.expire_date = datetime.utcnow() + timedelta(days=info['days'])
        user.is_active = True
        db.commit()
        
        # Referral bonus if referred
        if user.referred_by:
            ref_user = get_user(db, user.referred_by)
            if ref_user:
                payment = db.query(Payment).filter(Payment.telegram_id == telegram_id).order_by(Payment.id.desc()).first()
                bonus = payment.amount * config.REFERRAL_PERCENT if payment else 0
                ref_user.referral_balance += bonus
                db.commit()
                # Notify ref user
        
        logger.info(f"Activated {plan} for {telegram_id}")
        return True
    return False

async def check_payment(query, payment_id: str):
    status = check_payment_status(payment_id)
    if status == 'paid' and not process_paid_payment(payment_id):
        # Find last payment for user
        db = next(get_db())
        payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
        if payment:
            await activate_subscription(payment.telegram_id, payment.plan_type)
    
    if status == 'paid':
        await query.edit_message_text('✅ Оплата получена! Подписка активирована.')
    else:
        keyboard = [[InlineKeyboardButton('✅ Проверить снова', callback_data=f'check_{payment_id}')]]
        await query.edit_message_text('⏳ Оплата не найдена. Попробуйте позже.', reply_markup=InlineKeyboardMarkup(keyboard))

async def daily_expire_check():
    """Ежедневная проверка истечения"""
    db = next(get_db())
    tomorrow = datetime.utcnow() + timedelta(days=config.EXPIRE_NOTIFY_DAYS)
    
    users = db.query(User).filter(
        User.expire_date <= tomorrow,
        User.expire_date > datetime.utcnow(),
        User.is_active
    ).all()
    
    for user in users:
        days_left = (user.expire_date - datetime.utcnow()).days
        text = f"⏰ Ваша подписка истекает через {days_left} дней! Продлите: /start"
        # Send message to user.telegram_id
        # await application.bot.send_message(...)
    
    logger.info(f"Notified {len(users)} expiring users")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    # Init
    config.validate_config()
    init_db()
    
    # App
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_menu))
    application.add_handler(CommandHandler("stats", admin_stats))
    application.add_handler(CallbackQueryHandler(button_handler))
application.add_handler(CallbackQueryHandler(lambda u,c: asyncio.create_task(check_payment(u.callback_query, u.data.split('_',1)[1])) if u.callback_query.data.startswith('check_') else None, pattern='^check_'))
    
    # Error
    application.add_error_handler(error_handler)
    
    # Scheduler
    scheduler = AsyncIOScheduler(timezone=pytz.UTC)
    scheduler.add_job(daily_expire_check, CronTrigger(hour=9, minute=0), id='expire_check')
    scheduler.start()
    
    # Run
    logger.info("🚀 Bot started")
    application.run_polling()

if __name__ == '__main__':
    main()

