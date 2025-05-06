import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from app.settings import BOT_TOKEN
from app.handlers import routers
from app.db import init_db
from app.services.token_alert_service import TokenAlertService
from app.migrate import migrate_add_last_alert_time

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
                last_price = item["previous_price"]  # Получаем предыдущую цену из результата
                time_passed = item.get("time_passed", 0)  # Получаем время в секундах с предыдущего алерта
                
                # Форматируем прошедшее время
                hours, remainder = divmod(int(time_passed), 3600)
                minutes, seconds = divmod(remainder, 60)
                
                if hours > 0:
                    time_str = f"{hours}h {minutes}m {seconds}s"
                elif minutes > 0:
                    time_str = f"{minutes}m {seconds}s"
                else:
                    time_str = f"{seconds}s"
                
                # Рассчитываем изменение цены
                price_diff = current_price - last_price
                price_diff_percent = (price_diff / last_price) * 100 if last_price else 0
                
                # Определяем направление движения цены
                is_price_up = price_diff > 0  # Используем price_diff напрямую для определения направления
                direction_emoji = "🟢" if is_price_up else "🔴"
                
                # Форматируем значение изменения, гарантируя отображение даже маленьких изменений
                sign = "+" if is_price_up else "-"
                abs_diff = abs(price_diff)
                abs_percent = abs(price_diff_percent)
                
                # Используем разные форматы в зависимости от величины изменения
                if abs_diff < 0.0001:
                    diff_formatted = f"{sign}${abs_diff:.10f}"
                elif abs_diff < 0.01:
                    diff_formatted = f"{sign}${abs_diff:.6f}"
                else:
                    diff_formatted = f"{sign}${abs_diff:,.2f}"
                
                # Форматирование процентов
                if abs_percent < 0.0001:
                    percent_formatted = f"{sign}{abs_percent:.10f}%"
                elif abs_percent < 0.01:
                    percent_formatted = f"{sign}{abs_percent:.6f}%"
                else:
                    percent_formatted = f"{sign}{abs_percent:.4f}%"
                
                # Проверка и принудительная коррекция при очень маленьких значениях
                # Если разница меньше чем 0.000001, показываем фактическую разницу без округления
                if abs_diff < 0.000001:
                    diff_formatted = f"{sign}${price_diff:e}"  # Используем научную нотацию
                if abs_percent < 0.000001:
                    percent_formatted = f"{sign}{price_diff_percent:e}%"  # Научная нотация для процентов
                
                # Логирование для отладки
                logger.debug(f"Price change: from {last_price} to {current_price} = {price_diff}")
                logger.debug(f"Formatted: {diff_formatted} ({percent_formatted})")
                
                # Format message
                message = (
                    f"⚡️ *{alert.symbol}* ⚡️\n"
                    f"{direction_emoji} *${current_price:,.2f}*\n"
                    f"Change: *{diff_formatted}* ({percent_formatted})\n"
                    f"Time since last alert: *{time_str}*\n"
                    f"Alert step: *${alert.price_multiplier:g}*"
                )
                
                try:
                    # Send message to user
                    await bot.send_message(
                        alert.user_id,
                        message,
                        parse_mode="Markdown"
                    )
                    logger.info(f"Sent price alert to user {alert.user_id} for {alert.symbol}: ${current_price:,.2f} (change: {diff_formatted})")
                except Exception as e:
                    logger.error(f"Failed to send alert to user {alert.user_id}: {e}")
        
        except Exception as e:
            logger.error(f"Error in alert worker: {e}")
        
        # Wait before next check
        from app.settings import POLLING_INTERVAL
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