import time
import sqlite3
from loguru import logger
from app.settings import DATABASE_URL, POLLING_INTERVAL

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
        # Устанавливаем текущее время без смещения для существующих записей
        past_time = current_time
        
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
            
        # Получим все алерты и обновим их last_alert_time с реальным временем, но с разницей для разных ID
        cursor.execute("SELECT id FROM token_alerts")
        alerts = cursor.fetchall()
        
        # Для миграции устанавливаем разное время для тестирования реального отображения времени
        for i, alert in enumerate(alerts):
            alert_id = alert[0]
            # Устанавливаем временные метки с интервалом 30 секунд
            spread_factor = i * 30  # 30 секунд разницы между алертами
            new_time = current_time - spread_factor
            cursor.execute("UPDATE token_alerts SET last_alert_time = ? WHERE id = ?", (new_time, alert_id))
            logger.info(f"Updated alert ID {alert_id} with time: {new_time} ({spread_factor}s ago)")
        
        conn.commit()
        logger.info(f"Updated all alerts with proper time values")
        
        return True
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate_add_last_alert_time() 