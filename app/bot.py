import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from app.settings import BOT_TOKEN
from app.handlers import routers
from app.utils import setup_logger
from app.db import init_db
from app.services.token_alert_service import TokenAlertService

# Global bot instance for access from other modules
bot = Bot(token=BOT_TOKEN)

async def alert_worker():
    """Background worker that checks for price alerts."""
    while True:
        try:
            # Check for alerts that need to be sent
            alerts_to_send = await TokenAlertService.check_price_alerts()
            
            # Send notifications for each alert
            for item in alerts_to_send:
                alert = item["alert"]
                current_price = item["current_price"]
                
                # Format message
                message = (
                    f"🔔 *Price Alert for {alert.symbol}*\n\n"
                    f"Current price: *${current_price:,.2f}*\n"
                    f"Threshold: *${alert.price_multiplier:g}*\n\n"
                    f"The price has crossed a ${alert.price_multiplier:g} threshold!"
                )
                
                try:
                    # Send message to user
                    await bot.send_message(
                        alert.user_id,
                        message,
                        parse_mode="Markdown"
                    )
                    logger.info(f"Sent alert to user {alert.user_id} for {alert.symbol} at ${current_price}")
                except Exception as e:
                    logger.error(f"Failed to send alert to user {alert.user_id}: {e}")
        
        except Exception as e:
            logger.error(f"Error in alert worker: {e}")
        
        # Wait before next check
        from app.settings import POLLING_INTERVAL
        await asyncio.sleep(POLLING_INTERVAL)

async def main():
    """Main bot function."""
    # Setup logger
    setup_logger()
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
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
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1) 