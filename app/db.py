from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from app.settings import DATABASE_URL
import time

# Create directory for SQLite database if it doesn't exist
os.makedirs(os.path.dirname(DATABASE_URL.replace('sqlite:///', '')), exist_ok=True)

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    is_admin = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    created_at = Column(Float, default=time.time)

class TokenAlert(Base):
    __tablename__ = 'token_alerts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    symbol = Column(String, nullable=False)
    price_multiplier = Column(Float, nullable=False)
    last_alert_price = Column(Float)
    last_alert_time = Column(Float, default=time.time)
    is_active = Column(Boolean, default=True)
    created_at = Column(Float, default=time.time)

# Создаем и возвращаем сессию для работы с БД
def get_session():
    # Create all tables if they don't exist
    Base.metadata.create_all(engine)
    # Create session
    Session = sessionmaker(bind=engine)
    return Session()

def init_db():
    """Initialize the database and create all tables."""
    Base.metadata.create_all(engine)
    return True 