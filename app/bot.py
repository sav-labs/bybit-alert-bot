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
    elif seconds < 1:  # Если меньше секунды
        # Особый случай, возвращаем "только что" вместо миллисекунд
        return "just now"
    
    # Для очень маленьких значений (до 3 секунд) возвращаем "несколько секунд"
    if seconds < 3:
        return "few seconds"
        
    # Для значений менее минуты (но более 3 секунд)
    if seconds < 60:
        # Показываем точное количество секунд
        s = int(seconds)
        return f"{s}s"
    
    # Для времени больше минуты делаем более разнообразное форматирование
    total_seconds = int(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Для значений более часа
    if hours > 0:
        # Простой формат часы и минуты
        if seconds == 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{hours}h {minutes}m {seconds}s"
    
    # Для значений более минуты, но менее часа
    if minutes > 0:
        if seconds == 0:
            return f"{minutes}m"
        else:
            return f"{minutes}m {seconds}s"
    
    # Если ничего не сработало, возвращаем просто секунды
    return f"{total_seconds}s"

async def alert_worker():
    """Separate worker to check prices and send alerts."""
    while True:
        try:
            alerts = await TokenAlertService.check_price_alerts()
            
            for alert_data in alerts:
                alert = alert_data["alert"]
                current_price = alert_data["current_price"]
                previous_price = alert_data["previous_price"]
                
                # Calculate price change percentage
                if previous_price > 0:
                    price_diff = current_price - previous_price
                    change_pct = price_diff / previous_price * 100
                    direction = "🟢" if price_diff >= 0 else "🔴"
                    
                    # Добавляем знаки "+" и "-" перед изменением
                    sign = "+" if price_diff >= 0 else "-"
                    abs_diff = abs(price_diff)
                    formatted_change = f"{sign}${abs_diff:,.2f} ({sign}{abs(change_pct):.2f}%)"
                else:
                    direction = "🟢"
                    formatted_change = "$0.00 (0.00%)"
                
                # Format message without time since last alert
                message = (
                    f"{direction} <b>{alert.symbol}</b>\n\n"
                    f"Current Price: ${current_price:,.2f}\n"
                    f"Previous Price: ${previous_price:,.2f}\n"
                    f"Change: {formatted_change}\n\n"
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
    if success:
        logger.info("Database migration completed successfully")
    else:
        logger.error("Database migration failed")
    
    # Проверка и исправление last_alert_time для всех алертов
    try:
        from app.services.token_alert_service import TokenAlertService
        await TokenAlertService.check_price_alerts()
        logger.info("Initial price check completed, all alerts initialized")
    except Exception as e:
        logger.error(f"Error during initial price check: {e}")
    
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