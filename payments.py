"""
YooMoney - ручное создание Quickpay URL (стабильно)
"""
import uuid
from database import get_db, Payment
import config

def create_invoice(telegram_id: int, amount: float, plan_type: str):
    """Создать ссылку на оплату"""
    payment_id = f"{config.PAYMENT_PREFIX}{uuid.uuid4().hex[:12]}"
    
    # Сохранить платёж в БД
    db = next(get_db())
    payment = Payment(
        telegram_id=telegram_id,
        amount=amount,
        plan_type=plan_type,
        payment_id=payment_id,
        status='pending'
    )
    db.add(payment)
    db.commit()
    
    # Quickpay URL
    targets = f"VPN {plan_type}"
    invoice_url = (
        f"https://yoomoney.ru/quickpay/confirm.xml?"
        f"receiver={config.YOOMOONEY_WALLET}&"
        f"targets={targets}&"
        f"paymentType=PC&"  # card
        f"sum={amount}&"
        f"label={payment_id}"
    )
    
    return invoice_url, payment_id

def check_payment_status(payment_id: str):
    """Проверить статус (mock/real webhook better)"""
    # TODO: real check with token
    # For demo: assume pending/paid after time
    db = next(get_db())
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    if payment:
        if payment.status == 'paid':
            return 'paid'
    return 'pending'

def process_paid_payment(payment_id: str):
    """Отметить paid"""
    db = next(get_db())
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    if payment and payment.status == 'pending':
        payment.status = 'paid'
        db.commit()
        return True
    return False

if __name__ == '__main__':
    url, id = create_invoice(123, 300, '30d')
    print(f"URL: {url}\nID: {id}")

