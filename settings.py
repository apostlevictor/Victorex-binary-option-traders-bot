"""
Configuration settings for the trading bot
"""

import os
from typing import Dict, List

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_USER_IDS = [int(id.strip()) for id in os.getenv("ADMIN_USER_IDS", "7149581100").split(",") if id.strip()]

# Signal Configuration
SIGNAL_INTERVAL_MINUTES = 5
SIGNAL_EXPIRATION_MINUTES = 3
TARGET_ACCURACY = 90.0
MINIMUM_CONFIDENCE = 65.0

# Timezone Configuration
TIMEZONE = "Africa/Lagos"  # GMT+1 Nigeria time

# Asset Categories
CURRENCY_PAIRS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD", "USD/CHF",
    "EUR/GBP", "EUR/JPY", "GBP/JPY", "AUD/JPY", "NZD/USD", "USD/SGD",
    "EUR/CAD", "GBP/CAD", "AUD/CAD", "EUR/AUD", "GBP/AUD", "USD/ZAR"
]

CRYPTOCURRENCIES = [
    "BTC/USD", "ETH/USD", "XRP/USD", "LTC/USD", "ADA/USD", "DOT/USD",
    "LINK/USD", "BCH/USD", "XLM/USD", "DOGE/USD", "MATIC/USD", "SOL/USD",
    "AVAX/USD", "ATOM/USD", "ALGO/USD", "VET/USD", "FIL/USD", "TRX/USD"
]

# OTC Currency Pairs (additional exotic pairs)
OTC_CURRENCY_PAIRS = [
    "USD/TRY", "USD/MXN", "USD/PLN", "USD/CZK", "USD/HUF", "USD/RON",
    "EUR/TRY", "EUR/PLN", "EUR/CZK", "EUR/HUF", "EUR/NOK", "EUR/SEK",
    "GBP/TRY", "GBP/PLN", "GBP/CZK", "GBP/NOK", "GBP/SEK", "GBP/ZAR",
    "USD/DKK", "USD/ILS", "USD/RUB", "USD/INR", "USD/CNY", "USD/KRW",
    "AUD/NZD", "CAD/JPY", "CHF/JPY", "NZD/JPY", "SGD/JPY", "HKD/JPY"
]

# OTC Cryptocurrency Pairs (additional crypto pairs)
OTC_CRYPTOCURRENCIES = [
    "BNB/USD", "XRP/BTC", "ETH/BTC", "LTC/BTC", "ADA/BTC", "DOT/BTC",
    "SHIB/USD", "UNI/USD", "AAVE/USD", "COMP/USD", "MKR/USD", "SNX/USD",
    "CRV/USD", "YFI/USD", "SUSHI/USD", "1INCH/USD", "BAT/USD", "ZRX/USD",
    "BTC/EUR", "ETH/EUR", "XRP/EUR", "LTC/EUR", "ADA/EUR", "DOGE/EUR",
    "BTC/GBP", "ETH/GBP", "XRP/GBP", "BTC/JPY", "ETH/JPY", "XRP/JPY"
]

# Technical Analysis Parameters
TECHNICAL_INDICATORS = {
    "RSI": {"period": 14, "overbought": 70, "oversold": 30},
    "MACD": {"fast": 12, "slow": 26, "signal": 9},
    "BOLLINGER": {"period": 20, "deviation": 2},
    "STOCHASTIC": {"k_period": 14, "d_period": 3, "overbought": 80, "oversold": 20},
    "WILLIAMS_R": {"period": 14, "overbought": -20, "oversold": -80},
    "CCI": {"period": 20, "overbought": 100, "oversold": -100}
}

# Signal Validation Rules
VALIDATION_RULES = {
    "min_confidence": 65.0,
    "max_signals_per_asset": 5,  # per hour
    "cooldown_minutes": 10,  # minimum time between signals for same asset
    "required_indicators": 2,  # minimum number of indicators agreeing
    "trend_confirmation": False,  # More lenient for signal generation
    "volume_confirmation": False  # Not available for binary options
}

# Market Analysis Patterns
PATTERNS = {
    "BULLISH": [
        "hammer", "doji", "engulfing_bull", "morning_star", "piercing_line",
        "three_white_soldiers", "ascending_triangle", "cup_and_handle"
    ],
    "BEARISH": [
        "shooting_star", "hanging_man", "engulfing_bear", "evening_star",
        "dark_cloud_cover", "three_black_crows", "descending_triangle", "head_and_shoulders"
    ]
}

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = "trading_bot.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
