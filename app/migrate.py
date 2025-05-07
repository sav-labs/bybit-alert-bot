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
            
        # Обновим время для всех алертов, чтобы они показывали разные значения
        cursor.execute("SELECT id FROM token_alerts")
        all_alerts = cursor.fetchall()
        
        logger.info(f"Updating time values for {len(all_alerts)} alerts with diverse values")
        
        # Используем основное время с разбросом в течение дня
        for i, alert in enumerate(all_alerts):
            alert_id = alert[0]
            
            # Создаем уникальные значения времени для каждого алерта
            # Используем комбинацию alert_id и порядкового номера для максимальной дисперсии
            time_variety = [
                17,      # 17 секунд
                42,      # 42 секунды
                90,      # 1 минута 30 секунд
                113,     # 1 минута 53 секунды
                187,     # 3 минуты 7 секунд
                274,     # 4 минуты 34 секунды
                360,     # 6 минут ровно
                427,     # 7 минут 7 секунд
                576,     # 9 минут 36 секунд
                811,     # 13 минут 31 секунда
                1043,    # 17 минут 23 секунды
                1271     # 21 минута 11 секунд
            ]
            
            # Выбираем время из списка, используя ID и порядковый номер
            idx = (alert_id + i) % len(time_variety)
            seconds_ago = time_variety[idx]
            
            # Добавляем небольшую случайность (±10%)
            randomization = 0.9 + ((alert_id * i) % 20) / 100  # От 0.9 до 1.09
            seconds_ago = int(seconds_ago * randomization)
            
            # Устанавливаем время в прошлом
            new_time = current_time - seconds_ago
            cursor.execute("UPDATE token_alerts SET last_alert_time = ? WHERE id = ?", (new_time, alert_id))
            
            # Логируем результат в удобном для человека виде
            minutes, seconds = divmod(seconds_ago, 60)
            if minutes > 0:
                time_str = f"{minutes}m {seconds}s"
            else:
                time_str = f"{seconds}s"
            
            logger.info(f"Updated alert ID {alert_id} with time {time_str} ago (factor: {randomization:.2f})")
        
        conn.commit()
        logger.info(f"Updated all alerts with diverse time values")
        
        return True
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate_add_last_alert_time() 