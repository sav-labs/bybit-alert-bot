import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from app.settings import BOT_TOKEN
from app.handlers import routers
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
                last_price = alert.last_alert_price
                
                # Рассчитываем изменение цены
                price_diff = current_price - last_price
                price_diff_percent = (price_diff / last_price) * 100 if last_price else 0
                
                # Определяем направление движения цены
                is_price_up = current_price > last_price
                direction_emoji = "🟢 🔼" if is_price_up else "🔴 🔽"
                change_text = "increased" if is_price_up else "decreased"
                
                # Форматируем значение изменения
                diff_formatted = f"+${abs(price_diff):,.2f}" if is_price_up else f"-${abs(price_diff):,.2f}"
                percent_formatted = f"+{abs(price_diff_percent):.2f}%" if is_price_up else f"-{abs(price_diff_percent):.2f}%"
                
                # Format message
                message = (
                    f"🔔 *Price Alert for {alert.symbol}*\n\n"
                    f"{direction_emoji} Price has {change_text} to *${current_price:,.2f}*\n"
                    f"Change: *{diff_formatted}* ({percent_formatted})\n"
                    f"Alert threshold: *${alert.price_multiplier:g}*"
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
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized")
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