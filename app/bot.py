import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import logging
from loguru import logger

from app.settings import BOT_TOKEN, BOT_ADMINS, POLLING_INTERVAL
from app.handlers import routers
from app.db import init_db, get_session, Base, engine
from app.services.token_alert_service import TokenAlertService
from app.migrate import migrate_add_last_alert_time, apply_migrations
from app.states import wait_for_token_step
from app.keyboards import get_main_keyboard, get_alert_keyboard, get_dashboard_keyboard

# Global bot instance for access from other modules
bot = Bot(token=BOT_TOKEN)

# Функция для форматирования временных интервалов
def format_time_interval(seconds):
    """Format time interval in seconds to human-readable string."""
    if seconds < 0:
        return "N/A"
    elif seconds < 1:
        return "just now"
    
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

async def alert_worker():
    """Separate worker to check prices and send alerts."""
    while True:
        try:
            alerts = await TokenAlertService.check_price_alerts()
            
            for alert_data in alerts:
                alert = alert_data["alert"]
                current_price = alert_data["current_price"]
                previous_price = alert_data["previous_price"]
                time_passed = alert_data["time_passed"]
                
                # Format time passed in a human-readable way
                time_str = format_time_interval(time_passed)
                
                # Calculate price change percentage
                if previous_price > 0:
                    change_pct = (current_price - previous_price) / previous_price * 100
                    direction = "📈" if change_pct >= 0 else "📉"
                else:
                    change_pct = 0
                    direction = ""
                
                # Format message
                message = (
                    f"🚨 <b>Price Alert: {alert.symbol}</b> 🚨\n\n"
                    f"Current Price: ${current_price:,.2f}\n"
                    f"Previous Alert: ${previous_price:,.2f}\n"
                    f"Change: {direction} ${abs(current_price - previous_price):,.2f} ({change_pct:.2f}%)\n"
                    f"Time since last alert: {time_str}\n\n"
                    f"Alert Step: ${alert.price_multiplier:g}"
                )
                
                try:
                    await bot.send_message(chat_id=alert.user_id, text=message, parse_mode="HTML")
                    logger.info(f"Sent price alert to user {alert.user_id} for {alert.symbol} (${current_price:,.2f})")
                except Exception as e:
                    logger.error(f"Failed to send alert to user {alert.user_id}: {e}")
            
        except Exception as e:
            logger.error(f"Error in alert worker: {e}")
        
        # Ждем перед следующей проверкой
        await asyncio.sleep(POLLING_INTERVAL)  
        logger.debug(f"Alert worker checked prices after {POLLING_INTERVAL}s interval")

async def main():
    """Main bot function."""
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized")
        
        # Запускаем миграцию для добавления поля last_alert_time
        migrate_result = migrate_add_last_alert_time()
        if migrate_result:
            logger.info("Database migration completed")
        else:
            logger.warning("Database migration failed or was not needed")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        return
    
    # Create dispatcher
    dp = Dispatcher(storage=MemoryStorage())
    
    # Register all routers
    for router in routers:
        dp.include_router(router)
    
    # Start alert worker
    asyncio.create_task(alert_worker())
    logger.info("Alert worker started")
    
    # Start polling
    logger.info("Starting bot")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        # Запуск через main.py рекомендуется
        logger.warning("Direct execution of bot.py is not recommended. Use 'python main.py' instead.")
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1) 