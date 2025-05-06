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
        
        if 'last_alert_time' not in column_names:
            # Add column with default value of current time
            logger.info("Adding last_alert_time column to token_alerts table")
            cursor.execute("ALTER TABLE token_alerts ADD COLUMN last_alert_time REAL DEFAULT ?", (current_time,))
            conn.commit()
            logger.info("Migration completed successfully")
        else:
            logger.info("Column last_alert_time already exists in token_alerts table")
            
        # Проверим и исправим NULL значения в поле last_alert_time
        cursor.execute("SELECT COUNT(*) FROM token_alerts WHERE last_alert_time IS NULL")
        null_count = cursor.fetchone()[0]
        
        if null_count > 0:
            logger.warning(f"Found {null_count} records with NULL last_alert_time, fixing...")
            cursor.execute("UPDATE token_alerts SET last_alert_time = ? WHERE last_alert_time IS NULL", (current_time,))
            conn.commit()
            logger.info(f"Fixed {null_count} records with NULL last_alert_time")
            
        return True
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate_add_last_alert_time() 