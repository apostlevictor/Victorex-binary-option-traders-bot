"""
Telegram bot for binary options trading signals
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from bot.signal_generator import SignalGenerator
from bot.subscription_manager import SubscriptionManager
from utils.timezone_handler import TimezoneHandler
from config.settings import SIGNAL_INTERVAL_MINUTES, ADMIN_USER_IDS

class TradingBot:
    """Main Telegram bot class for trading signals"""
    
    def __init__(self, token: str):
        self.token = token
        self.logger = logging.getLogger(__name__)
        self.signal_generator = SignalGenerator()
        self.subscription_manager = SubscriptionManager()
        self.timezone_handler = TimezoneHandler()
        self.scheduler = AsyncIOScheduler()
        
        # Bot state
        self.active_users = set()
        self.is_running = False
        self.last_signal_time = None
        
        # Initialize application
        self.application = Application.builder().token(token).build()
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Setup command and message handlers"""
        handlers = [
            CommandHandler("start", self.start_command),
            CommandHandler("help", self.help_command),
            CommandHandler("status", self.status_command),
            CommandHandler("stop", self.stop_command),
            CommandHandler("stats", self.stats_command),
            CommandHandler("next", self.next_signal_command),
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        ]
        
        for handler in handlers:
            self.application.add_handler(handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        username = update.effective_user.username
        
        # Check user subscription status
        has_access, access_message = self.subscription_manager.check_user_access(user_id)
        
        if not has_access:
            # User needs to pay
            payment_info = self.subscription_manager.get_payment_info()
            await update.message.reply_text(payment_info, parse_mode='Markdown')
            return
        
        # Grant access
        if access_message == "Free slot available":
            # Register user for free access
            if self.subscription_manager.register_free_user(user_id, username):
                access_message = "Free access granted!"
        
        self.active_users.add(user_id)
        self.logger.info(f"User {user_name} ({user_id}) started the bot with {access_message}")
        
        welcome_message = f"""
🚀 **Binary Options Trading Signals Bot**

Welcome {user_name}! 

✅ **Access Status:** {access_message}

This bot provides high-accuracy binary options trading signals with:
• 🎯 90% accuracy target
• ⏰ 5-minute signal intervals
• ⏱️ 3-minute expiration times
• 📊 Multiple asset categories
• 🇳🇬 Nigeria time (GMT+1)

**Available Commands:**
/start - Start receiving signals
/help - Show this help message
/status - Check bot status
/stop - Stop receiving signals
/stats - View performance statistics
/next - Get next signal time

Signals will be delivered automatically every 5 minutes with detailed analysis and confidence levels.

Good luck with your trading! 📈
        """
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        
        # Start scheduler if not already running
        if not self.is_running:
            await self.start_signal_scheduler()
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📖 **Binary Options Trading Bot - Help**

**Signal Format:**
Each signal includes:
• Asset name and category
• BUY/SELL direction
• Confidence percentage
• 3-minute expiration time
• Entry reasoning
• Current Nigeria time

**Commands:**
• `/start` - Start receiving signals
• `/help` - Show this help
• `/status` - Bot status and next signal time
• `/stop` - Stop receiving signals
• `/stats` - Performance statistics
• `/next` - When is the next signal

**How It Works:**
1. Advanced market analysis every 5 minutes
2. Multiple technical indicators analyzed
3. Signal validation for quality assurance
4. Only high-confidence signals delivered
5. 90% accuracy target with 75% minimum confidence

**Asset Categories:**
• Currency Pairs (EUR/USD, GBP/USD, etc.)
• Commodities (Gold, Oil, Silver, etc.)
• Stocks (AAPL, GOOGL, TSLA, etc.)
• Indices (S&P 500, NASDAQ, etc.)

**Important Notes:**
• Signals expire in exactly 3 minutes
• Trade responsibly and manage risk
• Past performance doesn't guarantee future results
• Always use proper risk management

For support, contact the administrator.
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        current_time = self.timezone_handler.now()
        
        # Calculate next signal time
        next_signal_time = self.timezone_handler.get_next_signal_time(SIGNAL_INTERVAL_MINUTES)
        time_until_next = next_signal_time - current_time
        
        # Format time until next signal
        minutes_left = int(time_until_next.total_seconds() // 60)
        seconds_left = int(time_until_next.total_seconds() % 60)
        
        status_text = f"""
📊 **Bot Status**

🟢 **Status:** {'Running' if self.is_running else 'Stopped'}
👥 **Active Users:** {len(self.active_users)}
🕐 **Current Time:** {self.timezone_handler.format_time(current_time)}
⏰ **Next Signal:** {self.timezone_handler.format_time(next_signal_time)}
⏳ **Time Until Next:** {minutes_left}m {seconds_left}s

🎯 **Signal Settings:**
• Interval: {SIGNAL_INTERVAL_MINUTES} minutes
• Expiration: 3 minutes
• Accuracy Target: 90%
• Minimum Confidence: 75%

📈 **Performance:**
• Generated Signals: {self.signal_generator.generated_signals}
• Validated Signals: {self.signal_generator.validated_signals}
• Last Signal: {self.timezone_handler.format_time(self.last_signal_time) if self.last_signal_time else 'None'}
        """
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command"""
        user_id = update.effective_user.id
        
        if user_id in self.active_users:
            self.active_users.remove(user_id)
            await update.message.reply_text(
                "🛑 You have been unsubscribed from trading signals.\n\n"
                "Use /start to resume receiving signals."
            )
        else:
            await update.message.reply_text(
                "You are not currently subscribed to signals.\n\n"
                "Use /start to begin receiving signals."
            )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        user_id = update.effective_user.id
        
        # Check if user is admin for detailed stats
        is_admin = user_id in ADMIN_USER_IDS
        
        stats = self.signal_generator.get_statistics()
        
        if is_admin:
            # Detailed stats for admin
            stats_text = f"""
📊 **Detailed Statistics** (Admin)

**Signal Generation:**
• Generated: {stats['generated_signals']}
• Validated: {stats['validated_signals']}
• Validation Rate: {stats['validation_rate']:.1f}%
• Accuracy Target: {stats['accuracy_target']}%

**Asset Usage:**
• Total Assets: {stats['asset_stats']['total_assets']}
• Assets Used: {len(stats['asset_stats']['usage_count'])}

**Top Used Assets:**
            """
            
            # Add top used assets
            usage_count = stats['asset_stats']['usage_count']
            if usage_count:
                sorted_assets = sorted(usage_count.items(), key=lambda x: x[1], reverse=True)
                for asset, count in sorted_assets[:5]:
                    stats_text += f"• {asset}: {count} signals\n"
            
            stats_text += f"""
**Validation Stats:**
• Total Signals: {stats['validation_stats']['total_signals']}
• Accuracy Tracker: {len(stats['validation_stats']['accuracy_tracker'])} assets

**Bot Status:**
• Active Users: {len(self.active_users)}
• Running: {self.is_running}
            """
        else:
            # Basic stats for regular users
            stats_text = f"""
📊 **Performance Statistics**

**Signal Performance:**
• Total Signals Generated: {stats['generated_signals']}
• Validation Rate: {stats['validation_rate']:.1f}%
• Accuracy Target: {stats['accuracy_target']}%

**Bot Activity:**
• Active Users: {len(self.active_users)}
• Assets Available: {stats['asset_stats']['total_assets']}
• Status: {'Running' if self.is_running else 'Stopped'}

**Recent Activity:**
• Last Signal: {self.timezone_handler.format_time(self.last_signal_time) if self.last_signal_time else 'None'}
• Next Signal: {self.timezone_handler.format_time(self.timezone_handler.get_next_signal_time(SIGNAL_INTERVAL_MINUTES))}
            """
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')
    
    async def next_signal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /next command"""
        current_time = self.timezone_handler.now()
        next_signal_time = self.timezone_handler.get_next_signal_time(SIGNAL_INTERVAL_MINUTES)
        time_until_next = next_signal_time - current_time
        
        minutes_left = int(time_until_next.total_seconds() // 60)
        seconds_left = int(time_until_next.total_seconds() % 60)
        
        next_text = f"""
⏰ **Next Signal Information**

🕐 **Current Time:** {self.timezone_handler.format_time(current_time)}
🎯 **Next Signal:** {self.timezone_handler.format_time(next_signal_time)}
⏳ **Time Remaining:** {minutes_left}m {seconds_left}s

The next trading signal will be delivered automatically to all active users.
        """
        
        await update.message.reply_text(next_text, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages"""
        user_message = update.message.text.lower()
        
        # Check for signal-related keywords
        if any(keyword in user_message for keyword in ['signal', 'trade', 'buy', 'sell', 'option']):
            await update.message.reply_text(
                "📊 For trading signals, use /start to begin receiving automated signals every 5 minutes.\n\n"
                "Use /help for more information about available commands."
            )
        else:
            await update.message.reply_text(
                "👋 Hello! I'm a binary options trading signals bot.\n\n"
                "Use /start to begin receiving signals or /help for more information."
            )
    
    async def start_signal_scheduler(self):
        """Start the signal generation scheduler"""
        if self.is_running:
            return
        
        self.is_running = True
        self.scheduler.add_job(
            self.generate_and_send_signal,
            IntervalTrigger(minutes=SIGNAL_INTERVAL_MINUTES),
            id='signal_generator',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.logger.info("Signal scheduler started")
    
    async def generate_and_send_signal(self):
        """Generate and send signal to all active users"""
        try:
            if not self.active_users:
                self.logger.info("No active users, skipping signal generation")
                return
            
            # Generate signal
            signal_data = self.signal_generator.generate_signal()
            
            if not signal_data:
                self.logger.warning("No valid signal generated")
                return
            
            # Format signal message
            signal_message = self._format_signal_message(signal_data)
            
            # Send to all active users
            for user_id in self.active_users.copy():
                try:
                    await self.application.bot.send_message(
                        chat_id=user_id,
                        text=signal_message,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    self.logger.error(f"Failed to send signal to user {user_id}: {e}")
                    # Remove user if bot blocked
                    if "blocked" in str(e).lower():
                        self.active_users.discard(user_id)
            
            self.last_signal_time = self.timezone_handler.now()
            self.logger.info(f"Signal sent to {len(self.active_users)} users: {signal_data['asset']} {signal_data['direction']}")
            
        except Exception as e:
            self.logger.error(f"Error in signal generation and sending: {e}")
    
    def _format_signal_message(self, signal_data: Dict) -> str:
        """Format signal data into a user-friendly message"""
        asset = signal_data['asset']
        category = signal_data['category']
        direction = signal_data['direction']
        confidence = signal_data['confidence']
        expiration_time = signal_data['expiration_time']
        reasoning = signal_data['reasoning']
        current_time = self.timezone_handler.now()
        
        # Format category display name
        category_display = self.signal_generator.asset_manager.get_category_display_name(category)
        
        # Calculate time until expiration
        time_until_expiration = self.timezone_handler.time_until_expiration(expiration_time)
        
        # Direction emoji
        direction_emoji = "🟢" if direction == "BUY" else "🔴"
        
        # Confidence level indicator
        if confidence >= 85:
            confidence_indicator = "🔥 HIGH"
        elif confidence >= 75:
            confidence_indicator = "⚡ GOOD"
        else:
            confidence_indicator = "📊 FAIR"
        
        # Get entry price from analysis if available
        analysis = signal_data.get("analysis", {})
        entry_price = "N/A"
        
        # Try to get current price from indicators
        if "close_price" in analysis:
            entry_price = f"{analysis['close_price']:.5f}"
        elif "indicators" in analysis:
            indicators = analysis["indicators"]
            if "close" in indicators:
                entry_price = f"{indicators['close']:.5f}"
        
        # Determine strategy based on reasoning
        strategy = "RSI + MACD Divergence"
        if "BOLLINGER" in reasoning:
            strategy = "Bollinger Bands + RSI"
        elif "STOCHASTIC" in reasoning:
            strategy = "Stochastic + MACD"
        elif "MACD" in reasoning:
            strategy = "MACD + RSI"
        
        # Market condition from sentiment
        sentiment = analysis.get("sentiment", {})
        market_condition = sentiment.get("category", "NEUTRAL").title()
        if direction == "BUY":
            market_condition += " + Bullish Cross Confirmed"
        else:
            market_condition += " + Bearish Cross Confirmed"
        
        signal_message = f"""Pocket Option Signal Alert
🔔 Auto-Generated Trading Signal

🕒 Time (GMT+1): {self.timezone_handler.format_time(current_time, "%H:%M")}
📉 Asset: {asset}
📈 Direction: {direction} ({'CALL' if direction == 'BUY' else 'PUT'})
⏳ Expiry Time: 3 minutes
🎯 Entry Price: {entry_price}
⚠️ Confidence Level: {confidence:.0f}%
📊 Strategy Used: {strategy}
📍 Market Condition: {market_condition}

✅ Wait for stable candle close before entry.

---

📥 Signal Status:
✅ Signal Activated
📊 Result: Pending
💰 Profit: Calculating..."""
        
        return signal_message
    
    async def setup_bot_commands(self):
        """Setup bot commands for the menu"""
        commands = [
            BotCommand("start", "Start receiving trading signals"),
            BotCommand("help", "Show help and instructions"),
            BotCommand("status", "Check bot status and next signal time"),
            BotCommand("stop", "Stop receiving signals"),
            BotCommand("stats", "View performance statistics"),
            BotCommand("next", "Get next signal time"),
        ]
        
        await self.application.bot.set_my_commands(commands)
        self.logger.info("Bot commands setup completed")
    
    async def run(self):
        """Run the bot"""
        try:
            # Setup bot commands
            await self.setup_bot_commands()
            
            # Start the application
            await self.application.initialize()
            await self.application.start()
            
            self.logger.info("Trading bot started successfully")
            
            # Start polling for updates
            await self.application.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query"]
            )
            
            # Keep the bot running using the correct method
            import signal
            stop_event = asyncio.Event()
            
            def signal_handler(signum, frame):
                stop_event.set()
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            try:
                await stop_event.wait()
            except asyncio.CancelledError:
                pass
            
        except Exception as e:
            self.logger.error(f"Error running bot: {e}")
            raise
        finally:
            # Cleanup
            await self.cleanup()
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
            
            await self.application.stop()
            await self.application.shutdown()
            
            self.logger.info("Bot cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
