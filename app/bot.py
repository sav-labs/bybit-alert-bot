import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import logging
import sys
from loguru import logger

# Импортируем необходимые зависимости
from app.settings import BOT_TOKEN, BOT_ADMINS, POLLING_INTERVAL
from app.handlers import routers
from app.services.token_alert_service import TokenAlertService
from app.migrate import migrate_add_last_alert_time

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
    """Main function to start the bot."""
    # Configure logger
    from app.utils.logger import setup_logger
    setup_logger()
    logger.info("Starting Bybit Alert Bot")
    
    # Initialize database from app.db module
    from app.db import init_db
    init_db()
    logger.info("Database initialized")
    
    # Apply migrations
    success = migrate_add_last_alert_time()
    logger.info("Database migration completed")
    
    # Initialize Dispatcher with memory storage
    dp = Dispatcher(storage=MemoryStorage())
    
    # Include all routers
    for router in routers:
        dp.include_router(router)
    
    # Start alert worker
    asyncio.create_task(alert_worker())
    logger.info("Alert worker started")
    
    # Start polling
    logger.info("Starting bot")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 