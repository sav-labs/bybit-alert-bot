import asyncio
import sys
from loguru import logger
from app.bot import main
from app.utils import setup_logger

if __name__ == "__main__":
    # Initialize logger
    setup_logger()
    
    try:
        logger.info("Starting Bybit Alert Bot")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1) 