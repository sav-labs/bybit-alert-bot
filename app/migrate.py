import sqlite3
import time
import os
from pathlib import Path
from app.settings import DATABASE_URL
from loguru import logger

def migrate_add_last_alert_time():
    """
    Добавляет поле last_alert_time в таблицу token_alerts, если оно отсутствует,
    и заполняет его текущим временем для существующих записей.
    """
    # Получаем путь к файлу SQLite из DATABASE_URL
    db_path = DATABASE_URL.replace('sqlite:///', '')
    
    # Проверяем, существует ли база данных
    if not os.path.exists(db_path):
        logger.error(f"Database file {db_path} not found")
        return False
    
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем, есть ли уже колонка last_alert_time
        cursor.execute("PRAGMA table_info(token_alerts)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'last_alert_time' not in column_names:
            logger.info("Adding last_alert_time column to token_alerts table")
            
            # Добавляем колонку
            cursor.execute("ALTER TABLE token_alerts ADD COLUMN last_alert_time FLOAT")
            
            # Заполняем новую колонку текущим временем
            current_time = time.time()
            cursor.execute("UPDATE token_alerts SET last_alert_time = ?", (current_time,))
            
            # Применяем изменения
            conn.commit()
            logger.info("Migration completed successfully")
        else:
            logger.info("Column last_alert_time already exists in token_alerts table")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return False

if __name__ == "__main__":
    migrate_add_last_alert_time() 