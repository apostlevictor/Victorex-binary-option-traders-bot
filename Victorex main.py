#!/usr/bin/env python3
"""
Binary Options Trading Signals Telegram Bot
Main entry point for the application
"""

import asyncio
import logging
import os
from bot.telegram_bot import TradingBot
from utils.logging_config import setup_logging
from config.settings import BOT_TOKEN

def main():
    """Main function to start the trading bot"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Check for bot token
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is required")
        return
    
    logger.info("Starting Binary Options Trading Signals Bot...")
    
    # Create and run the bot
    bot = TradingBot(BOT_TOKEN)
    
    try:
        # Run the bot
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise

if __name__ == "__main__":
    main()
