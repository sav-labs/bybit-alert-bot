from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from app.settings import DATABASE_URL

# Создаем движок с настройкой echo для отладки в режиме DEBUG
engine = create_engine(DATABASE_URL, echo=False)

# Настраиваем фабрику сессий с expire_on_commit=False, чтобы избежать
# проблем с "detached instance" после закрытия сессии
session_factory = sessionmaker(bind=engine, expire_on_commit=False)
Session = scoped_session(session_factory)

Base = declarative_base()

def init_db():
    """Инициализация базы данных - создание таблиц."""
    Base.metadata.create_all(engine)

def get_session():
    """Получение новой сессии базы данных."""
    return Session() 