from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from app.settings import DATABASE_URL, POLLING_INTERVAL
import time
import inspect
import os
from loguru import logger

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
    last_alert_time = Column(Float, default=lambda: time.time() - POLLING_INTERVAL)
    is_active = Column(Boolean, default=True)
    created_at = Column(Float, default=time.time)

# Создаем и возвращаем сессию для работы с БД
def get_session():
    # Create all tables if they don't exist
    Base.metadata.create_all(engine)
    # Create session
    Session = sessionmaker(bind=engine)
    new_session = Session()
    
    # Логируем создание сессии для отладки
    frame = inspect.currentframe().f_back
    filename = os.path.basename(frame.f_code.co_filename)
    line_number = frame.f_lineno
    caller = f"{filename}:{line_number}"
    logger.debug(f"New DB session created from {caller}")
    
    return new_session

def init_db():
    """Initialize the database and create all tables."""
    Base.metadata.create_all(engine)
    return True 