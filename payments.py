"""
YooMoney интеграция
"""
import uuid
from yoomoney import Client
from typing import Dict, Optional
import config
from database import get_db, User, Payment
import logging

client = Client(config.YOOMOONEY_TOKEN)

def create_invoice(telegram_id: int, amount: float, plan_type: str) -> str:
    """Создать счёт YooMoney"""
    payment_id = f"{config.PAYMENT_PREFIX}{uuid.uuid4().hex[:8]}"
    
    # Сохранить в БД
    db = next(get_db())
    payment = Payment(
        telegram_id=telegram_id,
        amount=amount,
        plan_type=plan_type,
        payment_id=payment_id
    )
    db.add(payment)
    db.commit()
    
    # Создать платёж
    quickpay_form = client.quickpay(
        receiver=config.YOOMOONEY_WALLET,
        targets="VPN подписка " + plan_type,
        paymentType="PC",  # card
        successURL="",  # webhook better for prod
        label=payment_id,  # unique ID
        amount=amount
    )
    
    invoice_url = quickpay_form.redirected_url
    logging.info(f"Created invoice {payment_id} for {telegram_id}: {invoice_url}")
    return invoice_url, payment_id

def check_payment_status(payment_id: str) -> str:
    """Проверить статус платежа"""
    try:
        payment = client.operation_history(label=payment_id)
        if payment and payment.status == 'success':
            return 'paid'
        return 'pending'
    except:
        return 'failed'

def process_paid_payment(payment_id: str) -> bool:
    """Обработать успешный платёж"""
    db = next(get_db())
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    if not payment or payment.status != 'pending':
        return False
    
    payment.status = 'paid'
    db.commit()
    
    # Здесь будет логика активации подписки (вызывается из callback)
    logging.info(f"Payment {payment_id} marked paid")
    return True

if __name__ == '__main__':
    print("Test payment system ready")

