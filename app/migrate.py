import time
import sqlite3
from loguru import logger
from app.settings import DATABASE_URL

def migrate_add_last_alert_time():
    """Add last_alert_time column to token_alerts table if it doesn't exist and fixes any null values."""
    try:
        # Extract path from SQLAlchemy URL
        db_path = DATABASE_URL.replace('sqlite:///', '')
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(token_alerts)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        current_time = time.time()
        # Устанавливаем время на 1 час назад для существующих записей
        past_time = current_time - 3600
        
        if 'last_alert_time' not in column_names:
            # Add column with default value of one hour ago
            logger.info("Adding last_alert_time column to token_alerts table")
            cursor.execute("ALTER TABLE token_alerts ADD COLUMN last_alert_time REAL DEFAULT ?", (past_time,))
            conn.commit()
            logger.info("Migration completed successfully")
        else:
            logger.info("Column last_alert_time already exists in token_alerts table")
            
        # Проверим и исправим NULL значения в поле last_alert_time
        cursor.execute("SELECT COUNT(*) FROM token_alerts WHERE last_alert_time IS NULL OR last_alert_time = 0")
        null_count = cursor.fetchone()[0]
        
        if null_count > 0:
            logger.warning(f"Found {null_count} records with NULL or zero last_alert_time, fixing...")
            cursor.execute("UPDATE token_alerts SET last_alert_time = ? WHERE last_alert_time IS NULL OR last_alert_time = 0", (past_time,))
            conn.commit()
            logger.info(f"Fixed {null_count} records with NULL or zero last_alert_time")
            
        # Обновляем все записи с текущим временем (last_alert_time = current_time) 
        # на время в прошлом, чтобы избежать "just now"
        cursor.execute("SELECT COUNT(*) FROM token_alerts WHERE ABS(last_alert_time - ?) < 10", (current_time,))
        recent_count = cursor.fetchone()[0]
        
        if recent_count > 0:
            logger.warning(f"Found {recent_count} records with very recent last_alert_time, setting to 1 hour ago")
            cursor.execute("UPDATE token_alerts SET last_alert_time = ? WHERE ABS(last_alert_time - ?) < 10", (past_time, current_time))
            conn.commit()
            logger.info(f"Fixed {recent_count} records with very recent last_alert_time")
            
        return True
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate_add_last_alert_time() 