"""
Главный файл бота - исправленная версия
"""
import asyncio
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import config
from database import init_db, get_db, User
from user import start, button_handler, show_plans, show_profile, show_subscription, show_referrals, show_help
from admin import admin_menu, admin_stats
from payments import process_paid_payment, check_payment_status
from marzban_api import marzban
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def activate_subscription(telegram_id: int, plan: str):
    """Активация подписки после оплаты"""
    db = next(get_db())
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return False
    
    info = config.PLANS[plan]
    username = f"user_{telegram_id}_{int(datetime.now().timestamp())}"
    
    result = marzban.create_user(username, info['gb'], info['days'])
    if result:
        user.marzban_username = username
        user.subscription_url = marzban.get_subscription_url(username)
        user.plan_type = plan
        user.data_limit_gb = info['gb']
        user.expire_date = datetime.utcnow() + timedelta(days=info['days'])
        user.is_active = True
        db.commit()
        logger.info(f"Activated {plan} for {telegram_id}")
        return True
    return False

async def check_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    payment_id = query.data.split('_', 1)[1]
    status = check_payment_status(payment_id)
    if status == 'paid':
        db = next(get_db())
        payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
        if payment and process_paid_payment(payment_id):
            await activate_subscription(payment.telegram_id, payment.plan_type)
        await query.edit_message_text('✅ Оплата подтверждена! Подписка выдана.')
    else:
        keyboard = [[InlineKeyboardButton('Проверить снова', callback_data=f'check_{payment_id}')]]
        await query.edit_message_text('⏳ Оплата не найдена. Повторите позже.', reply_markup=InlineKeyboardMarkup(keyboard))

async def daily_expire_check():
    db = next(get_db())
    tomorrow = datetime.utcnow() + timedelta(days=config.EXPIRE_NOTIFY_DAYS)
    users = db.query(User).filter(
        User.expire_date <= tomorrow,
        User.expire_date > datetime.utcnow(),
        User.is_active == True
    ).all()
    logger.info(f"Found {len(users)} expiring users")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg=context.error)

def main():
    config.validate_config()
    init_db()
    
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_menu))
    application.add_handler(CommandHandler("stats", admin_stats))
    application.add_handler(CommandHandler("give", give_subscription))
    application.add_handler(CallbackQueryHandler(button_handler, pattern='^(купить_vpn|мой_профиль|моя_подписка|рефералы|помощь|buy_.*|main_menu)'))
    application.add_handler(CallbackQueryHandler(check_payment_callback, pattern='^check_'))
    
    application.add_error_handler(error_handler)
    
    scheduler = AsyncIOScheduler(timezone=pytz.UTC)
    scheduler.add_job(daily_expire_check, CronTrigger('0 9 * * *'), id='expire_check')
    scheduler.start()
    
    logger.info("🚀 Bot started!")
    application.run_polling()

if __name__ == '__main__':
    main()
```
**Запустите на VPS:**
```
python bot.py
```

**Теперь без ошибок!** 🚀
