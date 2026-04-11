"""
Главный бот - финальная версия с admin callbacks + main_menu admin button
"""
import asyncio
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram import Update
import config
from database import init_db
from user import start, button_handler
from admin import admin_menu, admin_callback, admin_stats, give_subscription
from payments import check_payment_status, process_paid_payment
from marzban_api import marzban

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    payment_id = query.data.split('_', 1)[1]
    status = check_payment_status(payment_id)
    
    if status == 'paid':
        if process_paid_payment(payment_id):
            text = "✅ Оплата подтверждена! Подписка активирована."
        else:
            text = "✅ Оплата найдена, но уже обработана."
    else:
        text = f"⏳ Статус: {status}. Проверьте позже."
        keyboard = [[InlineKeyboardButton("Проверить снова", callback_data=query.data)]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    keyboard = [[InlineKeyboardButton("🔙 Меню", callback_data="main_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error {update} {context.error}")

def main():
    config.validate_config()
    init_db()
    
    app = Application.builder().token(config.BOT_TOKEN).build()
    
    # User
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(buy_|profile|subscription|referrals|help|main_menu)$"))
    
    # Payment
    app.add_handler(CallbackQueryHandler(check_payment_callback, pattern="^check_"))
    
    # Admin
    app.add_handler(CommandHandler("admin", admin_menu))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("give", give_subscription))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    
    app.add_error_handler(error_handler)
    
    logger.info("🚀 VPN Bot запущен!")
    app.run_polling()

if __name__ == '__main__':
    main()

