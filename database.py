"""
База данных: SQLAlchemy модели и инициализация
"""
from sqlalchemy import create_engine, Column, Integer, String, BigInteger, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
from typing import Optional
import config

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(32))
    full_name = Column(String(128))
    marzban_username = Column(String(32), unique=True)
    subscription_url = Column(Text)
    plan_type = Column(String(8))  # '30d', '90d' etc
    data_limit_gb = Column(Integer)
    expire_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    referral_code = Column(String(16), unique=True)
    referred_by = Column(BigInteger)  # telegram_id
    referral_balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    payments = relationship("Payment", back_populates="user")

class Payment(Base):
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id'), nullable=False)
    amount = Column(Float, nullable=False)
    plan_type = Column(String(8), nullable=False)
    payment_id = Column(String(64), unique=True)
    status = Column(String(20), default='pending')  # pending, paid, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="payments")

class Mailing(Base):
    __tablename__ = 'mailing'
    
    id = Column(Integer, primary_key=True)
    message = Column(Text, nullable=False)
    html = Column(Boolean, default=False)
    sent_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, nullable=False)
    message = Column(Text, nullable=False)
    sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Глобальные объекты
engine = None
SessionLocal = None

def init_db():
    """Инициализация БД"""
    global engine, SessionLocal
    engine = create_engine(f'sqlite:///{config.DB_PATH}', echo=False)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Проверка конфига
    config.validate_config()
    print(f"✅ БД инициализирована: {config.DB_PATH}")

def get_db():
    """Декоратор/генератор сессии"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user(db, telegram_id: int) -> Optional[User]:
    """Получить пользователя по telegram_id"""
    return db.query(User).filter(User.telegram_id == telegram_id).first()

if __name__ == '__main__':
    init_db()

