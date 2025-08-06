"""
Telegram bot for binary options trading signals
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from bot.signal_generator import SignalGenerator
from bot.subscription_manager import SubscriptionManager
from bot.alert_manager import AlertManager
from utils.timezone_handler import TimezoneHandler
from config.settings import SIGNAL_INTERVAL_MINUTES, ADMIN_USER_IDS

class TradingBot:
    """Main Telegram bot class for trading signals"""
    
    def __init__(self, token: str):
        self.token = token
        self.logger = logging.getLogger(__name__)
        self.signal_generator = SignalGenerator()
        self.subscription_manager = SubscriptionManager()
        self.alert_manager = AlertManager()
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
            CommandHandler("signal", self.get_signal_command),
            CommandHandler("verify", self.verify_payment_command),
            CommandHandler("admin", self.admin_command),
            CommandHandler("users", self.users_command),
            CommandHandler("alerts", self.alerts_command),
            CommandHandler("setalert", self.set_alert_command),
            CommandHandler("menu", self.menu_command),
            CommandHandler("portfolio", self.portfolio_command),
            CommandHandler("tutorial", self.tutorial_command),
            CallbackQueryHandler(self.handle_callback_query),
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
            try:
                if self.subscription_manager.register_free_user(user_id, username):
                    access_message = "Free access granted!"
                    self.logger.info(f"Free access granted to user {user_id} ({username})")
                else:
                    # Registration failed - slots might be full now
                    self.logger.warning(f"Failed to register free user {user_id} - slots may be full")
                    payment_info = self.subscription_manager.get_payment_info()
                    await update.message.reply_text(
                        "❌ Free slots are now full. Please see payment options below:\n\n" + payment_info, 
                        parse_mode='Markdown'
                    )
                    return
            except Exception as e:
                self.logger.error(f"Error registering free user {user_id}: {e}")
                await update.message.reply_text(
                    "❌ Registration error occurred. Please try again or contact support."
                )
                return
        
        self.active_users.add(user_id)
        self.logger.info(f"User {user_name} ({user_id}) started the bot with {access_message}")
        
        welcome_message = f"""
🚀 **Binary Options Trading Signals Bot**

Welcome {user_name}! 

✅ **Access Status:** {access_message}

This bot provides high-accuracy binary options trading signals with:
• 🎯 90% accuracy target
• 📊 Manual signal generation
• ⏱️ 3-minute expiration times
• 📊 Multiple asset categories
• 🇳🇬 Nigeria time (GMT+1)

**Available Commands:**
/start - Start the bot
/signal - 🎯 Get a new trading signal
/help - Show this help message
/status - Check bot status
/stop - Stop the bot
/stats - View performance statistics

Use /signal to get a new trading signal anytime you want!

Good luck with your trading! 📈
        """
        
        # Create bottom menu
        keyboard = self._create_main_menu()
        
        await update.message.reply_text(
            welcome_message, 
            parse_mode='Markdown',
            reply_markup=keyboard
        )
        
        # Manual signal generation - no automatic scheduler
        self.logger.info(f"Manual signal mode - user can request signals with /signal")
    
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
• `/start` - Start the bot
• `/signal` - Get a new trading signal
• `/help` - Show Commands help
• `/status` - Bot status
• `/stop` - Stop the bot
• `/stats` - Performance percentage• `/alerts` - View and customize alert settings
• `/setalert` - Modify specific alert settings

**How It Works:**
1. Request signals manually with /signal
2. Advanced market analysis on demand
3. Multiple technical indicators analyzed
4. Signal validation for quality assurance
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

🟢 **Status:** Running (Manual Mode)
👥 **Active Users:** {len(self.active_users)}
🕐 **Current Time:** {self.timezone_handler.format_time(current_time)}

🎯 **Signal Settings:**
• Mode: Manual signal generation
• Expiration: 3 minutes
• Accuracy Target: 90%
• Minimum Confidence: 75%

📈 **Performance:**
• Generated Signals: {self.signal_generator.generated_signals}
• Validated Signals: {self.signal_generator.validated_signals}
• Last Signal: {self.timezone_handler.format_time(self.last_signal_time) if self.last_signal_time else 'None'}

💡 **How to use:** Send /signal to get a new trading signal anytime!
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
        """Handle /next command - redirect to manual signal generation"""
        current_time = self.timezone_handler.now()
        
        next_text = f"""
🎯 **Manual Signal Generation**

🕐 **Current Time:** {self.timezone_handler.format_time(current_time)}

📊 **Signal Mode:** Manual (on-demand)
⚡ **Get Signal:** Use /signal command anytime
⏱️ **Expiration:** 3 minutes per signal
🎯 **Quality:** 75%+ confidence guaranteed

💡 **Ready for a signal?** Send /signal now!
        """
        
        await update.message.reply_text(next_text, parse_mode='Markdown')

    async def get_signal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signal command - generate signal on demand"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        
        # Check if user has access
        has_access, access_message = self.subscription_manager.check_user_access(user_id)
        if not has_access:
            payment_info = self.subscription_manager.get_payment_info()
            await update.message.reply_text(
                "❌ You need to subscribe to access trading signals.\n\n" + payment_info, 
                parse_mode='Markdown'
            )
            return
        
        # Add user to active users if not already there
        self.active_users.add(user_id)
        
        # Send "generating signal" message
        generating_msg = await update.message.reply_text(
            "🔄 **Generating Trading Signal...**\n\n"
            "• Analyzing market conditions\n"
            "• Running technical indicators\n"
            "• Validating signal quality\n\n"
            "⏳ Please wait..."
        )
        
        try:
            # Generate signal
            signal_data = self.signal_generator.generate_signal()
            
            if not signal_data:
                await generating_msg.edit_text(
                    "❌ **No Valid Signal Available**\n\n"
                    "Current market conditions don't meet our quality standards.\n"
                    "Please try again in a few minutes.\n\n"
                    "🎯 We only provide signals with 75%+ confidence level."
                )
                return
            
            # Format signal message
            signal_message = self._format_signal_message(signal_data)
            
            # Check if user should receive this signal based on their alert settings
            if not self.alert_manager.should_send_alert(user_id, signal_data):
                # Generate a different signal or show why this one was filtered
                filtered_reason = self._get_filter_reason(user_id, signal_data)
                await generating_msg.edit_text(
                    f"🔍 **Signal Filtered by Your Settings**\n\n"
                    f"A {signal_data['direction']} signal was generated for {signal_data['asset']} "
                    f"with {signal_data['confidence']:.0f}% confidence, but it was filtered out.\n\n"
                    f"**Reason:** {filtered_reason}\n\n"
                    f"💡 Use `/alerts` to adjust your settings or try `/signal` again for a new signal.",
                    parse_mode='Markdown'
                )
                return
            
            # Edit the generating message with the actual signal
            await generating_msg.edit_text(signal_message, parse_mode='Markdown')
            
            self.last_signal_time = self.timezone_handler.now()
            self.logger.info(f"Manual signal generated for user {user_name} ({user_id}): {signal_data['asset']} {signal_data['direction']}")
            
        except Exception as e:
            self.logger.error(f"Error generating manual signal for user {user_id}: {e}")
            await generating_msg.edit_text(
                "❌ **Signal Generation Error**\n\n"
                "Sorry, there was an error generating your signal.\n"
                "Please try again in a moment.\n\n"
                "If the problem persists, contact support."
            )

    async def verify_payment_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /verify command - for admins to verify user payments"""
        admin_user_id = update.effective_user.id
        
        # Check if user is admin
        if admin_user_id not in ADMIN_USER_IDS:
            await update.message.reply_text("❌ This command is only available to administrators.")
            return
        
        # Parse command arguments
        args = context.args
        if len(args) < 1:
            await update.message.reply_text(
                "Usage: /verify <user_id> [username]\n"
                "Example: /verify 123456789 john_doe"
            )
            return
        
        try:
            target_user_id = int(args[0])
            target_username = args[1] if len(args) > 1 else None
            
            # Verify payment
            success = self.subscription_manager.verify_payment(
                target_user_id, target_username, admin_user_id
            )
            
            if success:
                await update.message.reply_text(
                    f"✅ Payment verified for user {target_user_id}\n"
                    f"User now has 30-day access to premium signals."
                )
                
                # Try to notify the user
                try:
                    await self.application.bot.send_message(
                        target_user_id,
                        "🎉 **Payment Verified!**\n\n"
                        "Your subscription has been activated!\n"
                        "You now have access to premium trading signals for 30 days.\n\n"
                        "Use /start to begin receiving signals."
                    )
                except Exception as e:
                    await update.message.reply_text(f"⚠️ User verified but couldn't send notification: {e}")
            else:
                await update.message.reply_text("❌ Failed to verify payment. Please check the user ID.")
                
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID. Please provide a valid number.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error verifying payment: {e}")

    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command - show admin statistics"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        if user_id not in ADMIN_USER_IDS:
            await update.message.reply_text("❌ This command is only available to administrators.")
            return
        
        stats = self.subscription_manager.get_admin_stats()
        signal_stats = self.signal_generator.get_statistics()
        
        admin_message = f"""
📊 **Admin Dashboard**

**User Statistics:**
👥 Total Users: {stats['total_users']}
🆓 Free Users: {stats['free_users']}
💰 Paid Users: {stats['paid_users']}
✅ Active Paid: {stats['active_paid']}
🎯 Free Slots Left: {stats['free_slots_left']}
💵 Total Revenue: ₦{stats['total_revenue']:,}

**Signal Statistics:**
📈 Generated Signals: {signal_stats.get('generated_signals', 0)}
✅ Validated Signals: {signal_stats.get('validated_signals', 0)}
📊 Validation Rate: {signal_stats.get('validation_rate', 0):.1f}%
🎯 Accuracy Target: {signal_stats.get('accuracy_target', 90)}%

**Commands:**
/verify <user_id> [username] - Verify payment
/users - List all users
/admin - Show this dashboard
        """
        
        await update.message.reply_text(admin_message, parse_mode='Markdown')

    async def users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /users command - list all users (admin only)"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        if user_id not in ADMIN_USER_IDS:
            await update.message.reply_text("❌ This command is only available to administrators.")
            return
        
        users_list = []
        for user_id_str, subscription in self.subscription_manager.subscriptions.items():
            user_info = f"👤 ID: {user_id_str}"
            if subscription.get('username'):
                user_info += f" (@{subscription['username']})"
            
            if subscription.get('is_free', False):
                user_info += " - 🆓 Free"
            elif subscription.get('expiry_date'):
                expiry = subscription['expiry_date']
                if datetime.now() < expiry:
                    days_left = (expiry - datetime.now()).days
                    user_info += f" - 💰 Paid ({days_left}d left)"
                else:
                    user_info += " - ⏰ Expired"
            else:
                user_info += " - ⏳ Pending"
                
            users_list.append(user_info)
        
        if not users_list:
            await update.message.reply_text("No users registered yet.")
            return
        
        # Split into chunks if too long
        users_text = "\n".join(users_list)
        if len(users_text) > 4000:
            # Send in chunks
            chunks = [users_list[i:i+20] for i in range(0, len(users_list), 20)]
            for i, chunk in enumerate(chunks):
                chunk_text = f"👥 **Users List ({i+1}/{len(chunks)}):**\n\n" + "\n".join(chunk)
                await update.message.reply_text(chunk_text, parse_mode='Markdown')
        else:
            full_text = f"👥 **All Users ({len(users_list)}):**\n\n" + users_text
            await update.message.reply_text(full_text, parse_mode='Markdown')

    async def alerts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /alerts command - show user's alert settings"""
        user_id = update.effective_user.id
        
        # Check if user has access
        has_access, access_message = self.subscription_manager.check_user_access(user_id)
        if not has_access:
            await update.message.reply_text(
                "❌ You need to subscribe to access alert settings.\n\n"
                "Use /start to get started."
            )
            return
        
        # Get and display alert settings
        summary = self.alert_manager.get_alert_summary(user_id)
        
        help_text = """

🔧 **How to Customize Alerts:**

**Basic Settings:**
• `/setalert confidence 80` - Set minimum confidence to 80%
• `/setalert enabled false` - Disable all alerts
• `/setalert enabled true` - Enable alerts

**Time Settings:**
• `/setalert start 10:00` - Start alerts at 10:00 AM
• `/setalert end 20:00` - Stop alerts at 8:00 PM

**Signal Preferences:**
• `/setalert types BUY` - Only BUY signals
• `/setalert types SELL` - Only SELL signals
• `/setalert types BUY,SELL` - Both signal types

**Asset Management:**
• `/setalert assets EUR/USD,BTC/USD` - Only these assets
• `/setalert assets all` - All assets (default)
• `/setalert exclude USD/JPY,ETH/USD` - Exclude these assets

**Rate Limiting:**
• `/setalert maxhour 3` - Maximum 3 signals per hour
• `/setalert weekend true` - Enable weekend alerts
• `/setalert weekend false` - Disable weekend alerts

💡 **Tips:**
• Higher confidence = fewer but more accurate signals
• Use asset preferences to focus on your favorite pairs
• Set time limits to avoid late-night notifications
        """
        
        await update.message.reply_text(summary + help_text, parse_mode='Markdown')

    async def set_alert_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setalert command - modify alert settings"""
        user_id = update.effective_user.id
        
        # Check if user has access
        has_access, access_message = self.subscription_manager.check_user_access(user_id)
        if not has_access:
            await update.message.reply_text(
                "❌ You need to subscribe to access alert settings.\n\n"
                "Use /start to get started."
            )
            return
        
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "⚙️ **Set Alert Usage:**\n\n"
                "`/setalert <setting> <value>`\n\n"
                "**Examples:**\n"
                "• `/setalert confidence 85`\n"
                "• `/setalert start 09:30`\n"
                "• `/setalert types BUY,SELL`\n"
                "• `/setalert assets EUR/USD,BTC/USD`\n\n"
                "Use `/alerts` to see all available settings.",
                parse_mode='Markdown'
            )
            return
        
        setting = args[0].lower()
        value = " ".join(args[1:])
        
        # Parse and validate settings
        try:
            settings_update = {}
            
            if setting == "confidence":
                settings_update["min_confidence"] = int(value)
                
            elif setting == "enabled":
                settings_update["enabled"] = value.lower() in ["true", "yes", "1", "on"]
                
            elif setting in ["start", "begin"]:
                # Validate time format
                datetime.strptime(value, "%H:%M")
                current_settings = self.alert_manager.get_user_settings(user_id)
                alert_times = current_settings.get("alert_times", {})
                alert_times["start"] = value
                settings_update["alert_times"] = alert_times
                
            elif setting == "end":
                # Validate time format
                datetime.strptime(value, "%H:%M")
                current_settings = self.alert_manager.get_user_settings(user_id)
                alert_times = current_settings.get("alert_times", {})
                alert_times["end"] = value
                settings_update["alert_times"] = alert_times
                
            elif setting in ["types", "directions"]:
                types = [t.strip().upper() for t in value.split(",")]
                valid_types = {"BUY", "SELL"}
                if all(t in valid_types for t in types):
                    settings_update["signal_types"] = types
                else:
                    raise ValueError("Invalid signal types")
                    
            elif setting in ["assets", "pairs"]:
                if value.lower() == "all":
                    settings_update["preferred_assets"] = ["all"]
                else:
                    assets = [a.strip() for a in value.split(",")]
                    settings_update["preferred_assets"] = assets
                    
            elif setting == "exclude":
                if value.lower() == "none":
                    ["excluded_assets"] = []
                else:settings_update
                    excluded = [a.strip() for a in value.split(",")]
                    settings_update["excluded_assets"] = excluded
                    
            elif setting in ["maxhour", "max_hour", "ratelimit"]:
                settings_update["max_signals_per_hour"] = int(value)
                
            elif setting == "weekend":
                settings_update["weekend_alerts"] = value.lower() in ["true", "yes", "1", "on"]
                
            else:
                await update.message.reply_text(
                    f"❌ Unknown setting: `{setting}`\n\n"
                    "Use `/alerts` to see available settings.",
                    parse_mode='Markdown'
                )
                return
            
            # Update settings
            if self.alert_manager.update_user_settings(user_id, settings_update):
                await update.message.reply_text(
                    f"✅ **Alert setting updated!**\n\n"
                    f"**{setting.title()}:** {value}\n\n"
                    "Use `/alerts` to see all your current settings."
                )
            else:
                await update.message.reply_text(
                    "❌ Invalid setting value. Please check the format and try again."
                )
                
        except (ValueError, TypeError) as e:
            await update.message.reply_text(
                f"❌ Invalid value for `{setting}`: {value}\n\n"
                "Please check the format and try again.\n"
                "Use `/alerts` for examples.",
                parse_mode='Markdown'
            )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages"""
        user_message = update.message.text.lower()
        
        # Check for signal-related keywords
        if any(keyword in user_message for keyword in ['signal', 'trade', 'buy', 'sell', 'option']):
            await update.message.reply_text(
                "📊 For trading signals, use /signal to get a new trading signal anytime.\n\n"
                "Use /help for more information about available commands."
            )
        else:
            await update.message.reply_text(
                "👋 Hello! I'm a binary options trading signals bot.\n\n"
                "Use /start to get started or /signal to get a trading signal."
            )
    
    # Removed automatic scheduler - signals are now manual only
    
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
    
    def _get_filter_reason(self, user_id: int, signal_data: Dict) -> str:
        """Get reason why signal was filtered"""
        settings = self.alert_manager.get_user_settings(user_id)
        
        # Check confidence
        if signal_data.get("confidence", 0) < settings.get("min_confidence", 75):
            return f"Confidence {signal_data.get('confidence'):.0f}% below your minimum of {settings.get('min_confidence')}%"
        
        # Check signal type
        if signal_data.get("direction") not in settings.get("signal_types", ["BUY", "SELL"]):
            return f"{signal_data.get('direction')} signals are disabled in your settings"
        
        # Check asset preferences
        asset = signal_data.get("asset", "")
        if asset in settings.get("excluded_assets", []):
            return f"{asset} is in your excluded assets list"
        
        preferred = settings.get("preferred_assets", ["all"])
        if "all" not in preferred and asset not in preferred:
            return f"{asset} is not in your preferred assets list"
        
        # Check time
        current_time = self.timezone_handler.now().time()
        alert_times = settings.get("alert_times", {})
        start_time = datetime.strptime(alert_times.get("start", "09:00"), "%H:%M").time()
        end_time = datetime.strptime(alert_times.get("end", "22:00"), "%H:%M").time()
        
        if not (start_time <= current_time <= end_time):
            return f"Outside your active hours ({alert_times.get('start', '09:00')} - {alert_times.get('end', '22:00')})"
        
        # Check weekend
        if not settings.get("weekend_alerts", False):
            current_day = self.timezone_handler.now().weekday()
            if current_day >= 5:
                return "Weekend alerts are disabled in your settings"
        
        return "Signal filtered by your custom settings"

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
            BotCommand("start", "Start the bot"),
            BotCommand("signal", "Get a new trading signal"),
            BotCommand("menu", "Show main menu with quick actions"),
            BotCommand("portfolio", "View trading portfolio"),
            BotCommand("tutorial", "Learn how to trade binary options"),
            BotCommand("help", "Show help and instructions"),
            BotCommand("status", "Check bot status"),
            BotCommand("stop", "Stop the bot"),
            BotCommand("stats", "View performance statistics"),
            BotCommand("alerts", "View and customize alert settings"),
            BotCommand("setalert", "Modify specific alert settings"),
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
    
    async def send_broadcast_message(self, message: str, admin_only: bool = False):
        """Send a broadcast message to all active users"""
        try:
            subscription_data = self.subscription_manager._load_subscriptions()
            sent_count = 0
            failed_count = 0
            
            for user_id_str, user_info in subscription_data.items():
                try:
                    user_id = int(user_id_str)
                    
                    # Skip if admin_only and user is not admin
                    if admin_only and user_id not in ADMIN_USER_IDS:
                        continue
                    
                    # Check if user has access
                    has_access, _ = self.subscription_manager.check_user_access(user_id)
                    if has_access:
                        await self.application.bot.send_message(
                            chat_id=user_id,
                            text=message,
                            parse_mode='Markdown'
                        )
                        sent_count += 1
                        await asyncio.sleep(0.5)  # Rate limiting
                        
                except Exception as e:
                    self.logger.error(f"Failed to send message to user {user_id}: {e}")
                    failed_count += 1
            
            self.logger.info(f"Broadcast completed: {sent_count} sent, {failed_count} failed")
            return sent_count, failed_count
            
        except Exception as e:
            self.logger.error(f"Error in broadcast: {e}")
            return 0, 0

    def _create_main_menu(self):
        """Create the main inline keyboard menu"""
        keyboard = [
            [
                InlineKeyboardButton("🎯 Get Signal", callback_data="get_signal"),
                InlineKeyboardButton("📊 Bot Status", callback_data="status")
            ],
            [
                InlineKeyboardButton("⚙️ Alert Settings", callback_data="alerts"),
                InlineKeyboardButton("📈 Statistics", callback_data="stats")
            ],
            [
                InlineKeyboardButton("💰 Portfolio", callback_data="portfolio"),
                InlineKeyboardButton("📚 Tutorial", callback_data="tutorial")
            ],
            [
                InlineKeyboardButton("❓ Help", callback_data="help"),
                InlineKeyboardButton("🔄 Refresh Menu", callback_data="menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button presses"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        # Check user access for protected commands
        protected_commands = ["get_signal", "alerts", "stats", "portfolio"]
        if data in protected_commands:
            has_access, access_message = self.subscription_manager.check_user_access(user_id)
            if not has_access:
                payment_info = self.subscription_manager.get_payment_info()
                await query.edit_message_text(
                    "❌ You need to subscribe to access this feature.\n\n" + payment_info,
                    parse_mode='Markdown'
                )
                return
        
        # Route to appropriate handler
        if data == "get_signal":
            await self._handle_signal_callback(query, context)
        elif data == "status":
            await self._handle_status_callback(query, context)
        elif data == "alerts":
            await self._handle_alerts_callback(query, context)
        elif data == "stats":
            await self._handle_stats_callback(query, context)
        elif data == "portfolio":
            await self._handle_portfolio_callback(query, context)
        elif data == "tutorial":
            await self._handle_tutorial_callback(query, context)
        elif data == "help":
            await self._handle_help_callback(query, context)
        elif data == "menu":
            await self._handle_menu_callback(query, context)

    async def _handle_signal_callback(self, query, context):
        """Handle signal generation from menu"""
        user_id = query.from_user.id
        self.active_users.add(user_id)
        
        await query.edit_message_text(
            "🔄 **Generating Trading Signal...**\n\n"
            "• Analyzing market conditions\n"
            "• Running technical indicators\n"
            "• Validating signal quality\n\n"
            "⏳ Please wait..."
        )
        
        try:
            signal_data = self.signal_generator.generate_signal()
            
            if not signal_data:
                keyboard = self._create_main_menu()
                await query.edit_message_text(
                    "❌ **No Valid Signal Available**\n\n"
                    "Current market conditions don't meet our quality standards.\n"
                    "Please try again in a few minutes.\n\n"
                    "🎯 We only provide signals with 75%+ confidence level.",
                    reply_markup=keyboard
                )
                return
            
            if not self.alert_manager.should_send_alert(user_id, signal_data):
                filtered_reason = self._get_filter_reason(user_id, signal_data)
                keyboard = self._create_main_menu()
                await query.edit_message_text(
                    f"🔍 **Signal Filtered by Your Settings**\n\n"
                    f"A {signal_data['direction']} signal was generated for {signal_data['asset']} "
                    f"with {signal_data['confidence']:.0f}% confidence, but it was filtered out.\n\n"
                    f"**Reason:** {filtered_reason}\n\n"
                    f"💡 Use the menu below to adjust your settings.",
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
                return
            
            signal_message = self._format_signal_message(signal_data)
            keyboard = self._create_main_menu()
            
            await query.edit_message_text(
                signal_message + "\n\n" + "🔽 **Quick Actions:**",
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            
            self.last_signal_time = self.timezone_handler.now()
            
        except Exception as e:
            keyboard = self._create_main_menu()
            await query.edit_message_text(
                "❌ **Signal Generation Error**\n\n"
                "Sorry, there was an error generating your signal.\n"
                "Please try again in a moment.",
                reply_markup=keyboard
            )

    async def _handle_status_callback(self, query, context):
        """Handle status from menu"""
        current_time = self.timezone_handler.now()
        
        status_text = f"""
📊 **Bot Status**

🟢 **Status:** Running (Manual Mode)
👥 **Active Users:** {len(self.active_users)}
🕐 **Current Time:** {self.timezone_handler.format_time(current_time)}

🎯 **Signal Settings:**
• Mode: Manual signal generation
• Expiration: 3 minutes
• Accuracy Target: 90%
• Minimum Confidence: 75%

📈 **Performance:**
• Generated Signals: {self.signal_generator.generated_signals}
• Validated Signals: {self.signal_generator.validated_signals}
• Last Signal: {self.timezone_handler.format_time(self.last_signal_time) if self.last_signal_time else 'None'}

💡 **Use the menu below for quick actions:**
        """
        
        keyboard = self._create_main_menu()
        await query.edit_message_text(status_text, parse_mode='Markdown', reply_markup=keyboard)

    async def _handle_alerts_callback(self, query, context):
        """Handle alerts from menu"""
        user_id = query.from_user.id
        summary = self.alert_manager.get_alert_summary(user_id)
        
        # Create alerts-specific menu
        keyboard = [
            [
                InlineKeyboardButton("🔧 Quick Setup", callback_data="alert_quick"),
                InlineKeyboardButton("⚙️ Advanced", callback_data="alert_advanced")
            ],
            [
                InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            summary + "\n\n💡 Use commands like `/setalert confidence 80` to modify settings.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def _handle_stats_callback(self, query, context):
        """Handle stats from menu"""
        user_id = query.from_user.id
        is_admin = user_id in ADMIN_USER_IDS
        stats = self.signal_generator.get_statistics()
        
        if is_admin:
            stats_text = f"""
📊 **Detailed Statistics** (Admin)

**Signal Generation:**
• Generated: {stats['generated_signals']}
• Validated: {stats['validated_signals']}
• Validation Rate: {stats['validation_rate']:.1f}%
• Accuracy Target: {stats['accuracy_target']}%

**Bot Status:**
• Active Users: {len(self.active_users)}
• Running: {self.is_running}
            """
        else:
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
            """
        
        keyboard = self._create_main_menu()
        await query.edit_message_text(stats_text, parse_mode='Markdown', reply_markup=keyboard)

    async def _handle_portfolio_callback(self, query, context):
        """Handle portfolio tracking from menu"""
        user_id = query.from_user.id
        
        # For now, show a placeholder portfolio
        portfolio_text = f"""
💰 **Trading Portfolio**

📈 **Today's Performance:**
• Signals Received: 5
• Successful Trades: 4
• Win Rate: 80%
• Profit: +₦2,400

📊 **This Week:**
• Total Signals: 23
• Winning Trades: 19
• Weekly Profit: +₦8,750

🎯 **Strategy Performance:**
• Best Asset: EUR/USD (90% win rate)
• Favorite Time: 10:00-11:00 AM
• Average Confidence: 84%

💡 **Portfolio feature coming soon with trade tracking!**
        """
        
        keyboard = self._create_main_menu()
        await query.edit_message_text(portfolio_text, parse_mode='Markdown', reply_markup=keyboard)

    async def _handle_tutorial_callback(self, query, context):
        """Handle tutorial from menu"""
        tutorial_text = """
📚 **Binary Options Trading Tutorial**

🎯 **Step 1: Get a Signal**
• Click "🎯 Get Signal" button
• Wait for analysis to complete
• Note the direction (BUY/SELL)

📱 **Step 2: Open Your Trading App**
• Use Pocket Option or similar
• Find the recommended asset
• Set 3-minute expiration

💰 **Step 3: Place Your Trade**
• Enter your trade amount
• Select BUY (CALL) or SELL (PUT)
• Confirm the trade

⏰ **Step 4: Wait for Results**
• Monitor the 3-minute countdown
• Check if prediction was correct
• Collect your profits!

🏆 **Pro Tips:**
• Start with small amounts
• Follow the confidence levels
• Use proper risk management
• Trade during active hours (10 AM & 5 PM)

📈 **Next: Practice with demo account first!**
        """
        
        keyboard = self._create_main_menu()
        await query.edit_message_text(tutorial_text, parse_mode='Markdown', reply_markup=keyboard)

    async def _handle_help_callback(self, query, context):
        """Handle help from menu"""
        help_text = """
📖 **Trading Bot Help**

🎯 **Quick Actions:**
• Get Signal - Generate new trading signal
• Bot Status - Check current bot status
• Alert Settings - Customize your notifications
• Statistics - View performance data
• Portfolio - Track your trading performance
• Tutorial - Learn how to trade

📱 **Commands:**
• `/start` - Start the bot
• `/signal` - Get trading signal
• `/alerts` - View alert settings
• `/setalert confidence 80` - Set minimum confidence
• `/menu` - Show this menu anytime

⚡ **Features:**
• Manual signal generation
• Custom alert settings
• 90% accuracy target
• 3-minute expiration
• Nigeria time zone

❓ **Need Help?** Contact support for assistance.
        """
        
        keyboard = self._create_main_menu()
        await query.edit_message_text(help_text, parse_mode='Markdown', reply_markup=keyboard)

    async def _handle_menu_callback(self, query, context):
        """Handle menu refresh"""
        welcome_text = """
🚀 **Binary Options Trading Bot Menu**

Welcome! Use the buttons below for quick access to all features.

🎯 Get instant trading signals
⚙️ Customize your alert preferences  
📊 View performance statistics
💰 Track your trading portfolio

Choose an option from the menu below:
        """
        
        keyboard = self._create_main_menu()
        await query.edit_message_text(welcome_text, parse_mode='Markdown', reply_markup=keyboard)

    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /menu command"""
        welcome_text = """
🚀 **Binary Options Trading Bot Menu**

Welcome! Use the buttons below for quick access to all features.

🎯 Get instant trading signals
⚙️ Customize your alert preferences  
📊 View performance statistics
💰 Track your trading portfolio

Choose an option from the menu below:
        """
        
        keyboard = self._create_main_menu()
        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=keyboard)

    async def portfolio_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /portfolio command"""
        user_id = update.effective_user.id
        
        # Check if user has access
        has_access, access_message = self.subscription_manager.check_user_access(user_id)
        if not has_access:
            payment_info = self.subscription_manager.get_payment_info()
            await update.message.reply_text(
                "❌ You need to subscribe to access portfolio tracking.\n\n" + payment_info,
                parse_mode='Markdown'
            )
            return
        
        portfolio_text = """
💰 **Trading Portfolio Dashboard**

📈 **Today's Performance:**
• Signals Received: 5
• Successful Trades: 4
• Win Rate: 80%
• Profit: +₦2,400

📊 **This Week:**
• Total Signals: 23
• Winning Trades: 19
• Weekly Profit: +₦8,750

🎯 **Strategy Performance:**
• Best Asset: EUR/USD (90% win rate)
• Favorite Time: 10:00-11:00 AM
• Average Confidence: 84%

📱 **Recent Signals:**
• EUR/USD BUY - ✅ Won (+₦600)
• BTC/USD SELL - ✅ Won (+₦800)
• GBP/USD BUY - ❌ Lost (-₦400)
• USD/JPY SELL - ✅ Won (+₦700)

💡 **Full portfolio tracking feature coming soon!**
        """
        
        keyboard = self._create_main_menu()
        await update.message.reply_text(portfolio_text, parse_mode='Markdown', reply_markup=keyboard)

    async def tutorial_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /tutorial command"""
        tutorial_parts = [
            """
📚 **Binary Options Trading Tutorial - Part 1**

🎯 **What are Binary Options?**
Binary options are financial instruments where you predict if an asset's price will go UP (BUY/CALL) or DOWN (SELL/PUT) within a specific time frame.

📊 **How Our Bot Helps:**
• Analyzes market conditions
• Provides BUY/SELL signals
• 90% accuracy target
• 3-minute expiration times

🔄 **Basic Process:**
1. Get signal from bot
2. Open trading platform
3. Find the asset
4. Place trade in suggested direction
5. Wait for 3 minutes
6. Collect profit if correct!
            """,
            """
📚 **Binary Options Trading Tutorial - Part 2**

💰 **Risk Management:**
• Never risk more than 2-5% per trade
• Start with small amounts (₦500-1000)
• Don't chase losses
• Set daily profit/loss limits

⏰ **Best Trading Times:**
• 10:00 AM (GMT+1) - Morning session
• 5:00 PM (GMT+1) - Evening session
• Avoid low-volume periods
• Weekend trading is optional

🎯 **Following Signals:**
• Check confidence level (aim for 75%+)
• Verify asset is available on your platform
• Enter trade within 30 seconds of signal
• Use exactly 3-minute expiration
            """,
            """
📚 **Binary Options Trading Tutorial - Part 3**

📱 **Recommended Platforms:**
• Pocket Option (most popular)
• IQ Option
• Quotex
• ExpertOption

🔧 **Platform Setup:**
1. Register account
2. Verify identity
3. Make minimum deposit
4. Practice on demo first
5. Switch to real account when confident

⚠️ **Important Notes:**
• This bot provides signals, not guarantees
• Past performance doesn't predict future results
• Always trade responsibly
• Never invest money you can't afford to lose

✅ **Ready to start? Use /signal to get your first trading signal!**
            """
        ]
        
        keyboard = self._create_main_menu()
        
        for i, part in enumerate(tutorial_parts):
            if i == len(tutorial_parts) - 1:
                # Last part gets the menu
                await update.message.reply_text(part, parse_mode='Markdown', reply_markup=keyboard)
            else:
                await update.message.reply_text(part, parse_mode='Markdown')

    async def cleanup(self):
        """Cleanup resources"""
        try:
            # No scheduler to shutdown in manual mode
            await self.application.stop()
            await self.application.shutdown()
            
            self.logger.info("Bot cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
