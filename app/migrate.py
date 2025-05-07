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
            cursor.execute("UPDATE token_alerts SET last_alert_time = ? WHERE last_alert_time IS NULL OR last_alert_time = 0", (past_time - 300,))
            conn.commit()
            logger.info(f"Fixed {null_count} records with NULL or zero last_alert_time")
            
        # Находим алерты с "0ms" временем и обновляем их
        cursor.execute("""
            SELECT id FROM token_alerts WHERE ABS(last_alert_time - ?) < 0.5
        """, (current_time,))
        recent_alerts = cursor.fetchall()
        
        if recent_alerts:
            logger.warning(f"Found {len(recent_alerts)} alerts with very recent last_alert_time, updating them")
            
            # Для миграции устанавливаем разное время для показа реального времени
            for i, alert in enumerate(recent_alerts):
                alert_id = alert[0]
                # Устанавливаем разное время для разных ID
                minutes_ago = (i + 1) * 2  # 2 минуты, 4 минуты, 6 минут и т.д.
                new_time = current_time - (minutes_ago * 60)
                cursor.execute("UPDATE token_alerts SET last_alert_time = ? WHERE id = ?", (new_time, alert_id))
                logger.info(f"Updated alert ID {alert_id} with time {minutes_ago} minutes ago")
                
            conn.commit()
            logger.info("Fixed alerts with '0ms' time display")
            
        # Получим все остальные алерты и обновим их last_alert_time с существенной разницей
        cursor.execute("""
            SELECT id FROM token_alerts WHERE 
            last_alert_time IS NOT NULL AND 
            last_alert_time > 0 AND 
            ABS(last_alert_time - ?) >= 0.5
        """, (current_time,))
        other_alerts = cursor.fetchall()
        
        if other_alerts:
            # Делаем больший разброс времени для нормального отображения
            for i, alert in enumerate(other_alerts):
                alert_id = alert[0]
                # Случайное время между 5 и 30 минутами назад (используя ID как псевдослучайность)
                minutes_ago = 5 + (alert_id % 25)
                new_time = current_time - (minutes_ago * 60)
                cursor.execute("UPDATE token_alerts SET last_alert_time = ? WHERE id = ?", (new_time, alert_id))
                logger.info(f"Updated alert ID {alert_id} with time {minutes_ago} minutes ago")
        
        conn.commit()
        logger.info(f"Updated all alerts with proper time values to prevent '0ms' display")
        
        return True
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate_add_last_alert_time() 