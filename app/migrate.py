import time
import sqlite3
from loguru import logger
from app.settings import DATABASE_URL

def migrate_add_last_alert_time():
    """Add last_alert_time column to token_alerts table if it doesn't exist."""
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
        
        if 'last_alert_time' not in column_names:
            # Add column with default value of current time
            logger.info("Adding last_alert_time column to token_alerts table")
            cursor.execute("ALTER TABLE token_alerts ADD COLUMN last_alert_time REAL DEFAULT ?", (time.time(),))
            conn.commit()
            logger.info("Migration completed successfully")
            return True
        else:
            logger.info("Column last_alert_time already exists in token_alerts table")
            return True
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate_add_last_alert_time() 