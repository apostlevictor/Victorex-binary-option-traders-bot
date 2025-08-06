"""
Real market data fetcher for live trading signals
"""

import yfinance as yf
import pandas as pd
import numpy as np
import requests
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import ta
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators

class MarketDataFetcher:
    """Fetches real market data from various sources"""
    
    def __init__(self, alpha_vantage_key: str = None):
        self.logger = logging.getLogger(__name__)
        self.alpha_vantage_key = alpha_vantage_key
        
        # Initialize Alpha Vantage if key is provided
        if alpha_vantage_key:
            self.ts = TimeSeries(key=alpha_vantage_key, output_format='pandas')
            self.ti = TechIndicators(key=alpha_vantage_key, output_format='pandas')
        
        # Asset symbol mapping for different categories
        self.asset_symbols = {
            # Currency pairs (using forex symbols)
            "EUR/USD": "EURUSD=X",
            "GBP/USD": "GBPUSD=X", 
            "USD/JPY": "USDJPY=X",
            "AUD/USD": "AUDUSD=X",
            "USD/CAD": "USDCAD=X",
            "USD/CHF": "USDCHF=X",
            "EUR/GBP": "EURGBP=X",
            "EUR/JPY": "EURJPY=X",
            "GBP/JPY": "GBPJPY=X",
            "AUD/JPY": "AUDJPY=X",
            "NZD/USD": "NZDUSD=X",
            "USD/SGD": "USDSGD=X",
            "EUR/CAD": "EURCAD=X",
            "GBP/CAD": "GBPCAD=X",
            "AUD/CAD": "AUDCAD=X",
            "EUR/AUD": "EURAUD=X",
            "GBP/AUD": "GBPAUD=X",
            "USD/ZAR": "USDZAR=X",
            
            # Cryptocurrencies
            "BTC/USD": "BTC-USD",
            "ETH/USD": "ETH-USD",
            "XRP/USD": "XRP-USD",
            "LTC/USD": "LTC-USD",
            "ADA/USD": "ADA-USD",
            "DOT/USD": "DOT-USD",
            "LINK/USD": "LINK-USD",
            "BCH/USD": "BCH-USD",
            "XLM/USD": "XLM-USD",
            "DOGE/USD": "DOGE-USD",
            "MATIC/USD": "MATIC-USD",
            "SOL/USD": "SOL-USD",
            "AVAX/USD": "AVAX-USD",
            "ATOM/USD": "ATOM-USD",
            "ALGO/USD": "ALGO-USD",
            "VET/USD": "VET-USD",
            "FIL/USD": "FIL-USD",
            "TRX/USD": "TRX-USD",
            
            # OTC Currency Pairs (Exotic pairs)
            "USD/TRY": "USDTRY=X",
            "USD/MXN": "USDMXN=X",
            "USD/PLN": "USDPLN=X",
            "USD/CZK": "USDCZK=X",
            "USD/HUF": "USDHUF=X",
            "USD/RON": "USDRON=X",
            "EUR/TRY": "EURTRY=X",
            "EUR/PLN": "EURPLN=X",
            "EUR/CZK": "EURCZK=X",
            "EUR/HUF": "EURHUF=X",
            "EUR/NOK": "EURNOK=X",
            "EUR/SEK": "EURSEK=X",
            "GBP/TRY": "GBPTRY=X",
            "GBP/PLN": "GBPPLN=X",
            "GBP/CZK": "GBPCZK=X",
            "GBP/NOK": "GBPNOK=X",
            "GBP/SEK": "GBPSEK=X",
            "GBP/ZAR": "GBPZAR=X",
            "USD/DKK": "USDDKK=X",
            "USD/ILS": "USDILS=X",
            "USD/RUB": "USDRUB=X",
            "USD/INR": "USDINR=X",
            "USD/CNY": "USDCNY=X",
            "USD/KRW": "USDKRW=X",
            "AUD/NZD": "AUDNZD=X",
            "CAD/JPY": "CADJPY=X",
            "CHF/JPY": "CHFJPY=X",
            "NZD/JPY": "NZDJPY=X",
            "SGD/JPY": "SGDJPY=X",
            "HKD/JPY": "HKDJPY=X",
            
            # OTC Cryptocurrencies
            "BNB/USD": "BNB-USD",
            "XRP/BTC": "XRP-BTC",
            "ETH/BTC": "ETH-BTC",
            "LTC/BTC": "LTC-BTC",
            "ADA/BTC": "ADA-BTC",
            "DOT/BTC": "DOT-BTC",
            "SHIB/USD": "SHIB-USD",
            "UNI/USD": "UNI-USD",
            "AAVE/USD": "AAVE-USD",
            "COMP/USD": "COMP-USD",
            "MKR/USD": "MKR-USD",
            "SNX/USD": "SNX-USD",
            "CRV/USD": "CRV-USD",
            "YFI/USD": "YFI-USD",
            "SUSHI/USD": "SUSHI-USD",
            "1INCH/USD": "1INCH-USD",
            "BAT/USD": "BAT-USD",
            "ZRX/USD": "ZRX-USD",
            "BTC/EUR": "BTC-EUR",
            "ETH/EUR": "ETH-EUR",
            "XRP/EUR": "XRP-EUR",
            "LTC/EUR": "LTC-EUR",
            "ADA/EUR": "ADA-EUR",
            "DOGE/EUR": "DOGE-EUR",
            "BTC/GBP": "BTC-GBP",
            "ETH/GBP": "ETH-GBP",
            "XRP/GBP": "XRP-GBP",
            "BTC/JPY": "BTC-JPY",
            "ETH/JPY": "ETH-JPY",
            "XRP/JPY": "XRP-JPY"
        }
    
    def get_real_time_data(self, asset: str, period: str = "1d", interval: str = "1m") -> Optional[pd.DataFrame]:
        """Get real-time market data for an asset"""
        try:
            symbol = self.asset_symbols.get(asset, asset)
            self.logger.info(f"Fetching real-time data for {asset} ({symbol})")
            
            # Use yfinance for real-time data
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                self.logger.warning(f"No data available for {asset}")
                return None
            
            # Ensure we have recent data
            if len(data) < 10:
                self.logger.warning(f"Insufficient data for {asset}")
                return None
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching data for {asset}: {e}")
            return None
    
    def calculate_technical_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate technical indicators from real market data"""
        try:
            if data.empty or len(data) < 20:
                return {}
            
            indicators = {}
            
            # RSI
            rsi = ta.momentum.RSIIndicator(data['Close'], window=14)
            rsi_value = rsi.rsi().iloc[-1]
            indicators["RSI"] = {
                "value": rsi_value,
                "signal": "BUY" if rsi_value < 30 else "SELL" if rsi_value > 70 else "NEUTRAL",
                "strength": abs(rsi_value - 50) / 50
            }
            
            # MACD
            macd = ta.trend.MACD(data['Close'])
            macd_line = macd.macd().iloc[-1]
            signal_line = macd.macd_signal().iloc[-1]
            indicators["MACD"] = {
                "macd_line": macd_line,
                "signal_line": signal_line,
                "histogram": macd_line - signal_line,
                "signal": "BUY" if macd_line > signal_line else "SELL",
                "strength": abs(macd_line - signal_line)
            }
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(data['Close'], window=20, window_dev=2)
            upper_band = bb.bollinger_hband().iloc[-1]
            middle_band = bb.bollinger_mavg().iloc[-1]
            lower_band = bb.bollinger_lband().iloc[-1]
            current_price = data['Close'].iloc[-1]
            
            indicators["BOLLINGER"] = {
                "upper_band": upper_band,
                "middle_band": middle_band,
                "lower_band": lower_band,
                "current_price": current_price,
                "signal": "BUY" if current_price < lower_band else "SELL" if current_price > upper_band else "NEUTRAL",
                "strength": abs(current_price - middle_band) / (upper_band - lower_band)
            }
            
            # Stochastic Oscillator
            stoch = ta.momentum.StochasticOscillator(data['High'], data['Low'], data['Close'])
            k_value = stoch.stoch().iloc[-1]
            d_value = stoch.stoch_signal().iloc[-1]
            indicators["STOCHASTIC"] = {
                "k_value": k_value,
                "d_value": d_value,
                "signal": "BUY" if k_value < 20 else "SELL" if k_value > 80 else "NEUTRAL",
                "strength": abs(k_value - 50) / 50
            }
            
            # Williams %R
            williams_r = ta.momentum.WilliamsRIndicator(data['High'], data['Low'], data['Close'])
            wr_value = williams_r.williams_r().iloc[-1]
            indicators["WILLIAMS_R"] = {
                "value": wr_value,
                "signal": "BUY" if wr_value < -80 else "SELL" if wr_value > -20 else "NEUTRAL",
                "strength": abs(wr_value + 50) / 50
            }
            
            # CCI
            cci = ta.trend.CCIIndicator(data['High'], data['Low'], data['Close'])
            cci_value = cci.cci().iloc[-1]
            indicators["CCI"] = {
                "value": cci_value,
                "signal": "BUY" if cci_value < -100 else "SELL" if cci_value > 100 else "NEUTRAL",
                "strength": min(abs(cci_value) / 200, 1.0)
            }
            
            # Moving Averages
            sma_20 = ta.trend.SMAIndicator(data['Close'], window=20).sma_indicator().iloc[-1]
            sma_50 = ta.trend.SMAIndicator(data['Close'], window=50).sma_indicator().iloc[-1]
            
            indicators["SMA"] = {
                "sma_20": sma_20,
                "sma_50": sma_50,
                "signal": "BUY" if sma_20 > sma_50 else "SELL",
                "strength": abs(sma_20 - sma_50) / sma_50
            }
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}")
            return {}
    
    def detect_chart_patterns(self, data: pd.DataFrame) -> Dict:
        """Detect chart patterns from real market data"""
        try:
            if data.empty or len(data) < 20:
                return {"pattern": None, "type": "NEUTRAL", "confidence": 0.5, "signal": "NEUTRAL"}
            
            # Get recent price action
            recent_highs = data['High'].tail(10)
            recent_lows = data['Low'].tail(10)
            recent_closes = data['Close'].tail(10)
            
            patterns = []
            
            # Simple trend detection
            if len(recent_closes) >= 5:
                trend_slope = (recent_closes.iloc[-1] - recent_closes.iloc[0]) / len(recent_closes)
                
                if trend_slope > 0:
                    patterns.append({"pattern": "uptrend", "type": "BULLISH", "confidence": 0.8, "signal": "BUY"})
                elif trend_slope < 0:
                    patterns.append({"pattern": "downtrend", "type": "BEARISH", "confidence": 0.8, "signal": "SELL"})
            
            # Support and resistance levels
            current_price = data['Close'].iloc[-1]
            recent_high = recent_highs.max()
            recent_low = recent_lows.min()
            
            # Check if price is near support/resistance
            if current_price <= recent_low * 1.01:  # Near support
                patterns.append({"pattern": "support_bounce", "type": "BULLISH", "confidence": 0.75, "signal": "BUY"})
            elif current_price >= recent_high * 0.99:  # Near resistance
                patterns.append({"pattern": "resistance_rejection", "type": "BEARISH", "confidence": 0.75, "signal": "SELL"})
            
            # Volume analysis (if available)
            if 'Volume' in data.columns:
                avg_volume = data['Volume'].tail(20).mean()
                recent_volume = data['Volume'].iloc[-1]
                
                if recent_volume > avg_volume * 1.5:  # High volume
                    volume_trend = "high_volume_confirmation"
                    for pattern in patterns:
                        pattern["confidence"] = min(pattern["confidence"] + 0.1, 0.95)
            
            # Return the strongest pattern
            if patterns:
                strongest_pattern = max(patterns, key=lambda x: x["confidence"])
                return strongest_pattern
            
            return {"pattern": None, "type": "NEUTRAL", "confidence": 0.5, "signal": "NEUTRAL"}
            
        except Exception as e:
            self.logger.error(f"Error detecting patterns: {e}")
            return {"pattern": None, "type": "NEUTRAL", "confidence": 0.5, "signal": "NEUTRAL"}
    
    def analyze_market_sentiment(self, data: pd.DataFrame, indicators: Dict) -> Dict:
        """Analyze market sentiment from real data"""
        try:
            if data.empty:
                return {"value": 0, "category": "NEUTRAL", "confidence": 0.5}
            
            sentiment_scores = []
            
            # Price momentum
            if len(data) >= 5:
                price_change = (data['Close'].iloc[-1] - data['Close'].iloc[-5]) / data['Close'].iloc[-5]
                sentiment_scores.append(price_change)
            
            # Volume trend (if available)
            if 'Volume' in data.columns and len(data) >= 10:
                recent_volume = data['Volume'].tail(5).mean()
                older_volume = data['Volume'].tail(10).head(5).mean()
                if older_volume > 0:  # Avoid division by zero
                    volume_trend = (recent_volume - older_volume) / older_volume
                    sentiment_scores.append(volume_trend * 0.5)  # Weight volume less than price
            
            # Indicator sentiment
            for indicator_name, indicator_data in indicators.items():
                signal = indicator_data.get("signal", "NEUTRAL")
                strength = indicator_data.get("strength", 0)
                
                if signal == "BUY":
                    sentiment_scores.append(strength * 0.3)
                elif signal == "SELL":
                    sentiment_scores.append(-strength * 0.3)
            
            # Calculate overall sentiment
            if sentiment_scores:
                avg_sentiment = np.mean(sentiment_scores)
                sentiment_value = np.clip(avg_sentiment, -1, 1)
                
                if sentiment_value > 0.2:
                    category = "BULLISH"
                elif sentiment_value < -0.2:
                    category = "BEARISH"
                else:
                    category = "NEUTRAL"
                
                confidence = min(abs(sentiment_value) + 0.5, 1.0)
                
                return {
                    "value": sentiment_value,
                    "category": category,
                    "confidence": confidence
                }
            
            return {"value": 0, "category": "NEUTRAL", "confidence": 0.5}
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {e}")
            return {"value": 0, "category": "NEUTRAL", "confidence": 0.5}
    
    def get_market_hours_status(self, asset: str) -> Dict:
        """Check if market is open for the given asset"""
        try:
            symbol = self.asset_symbols.get(asset, asset)
            ticker = yf.Ticker(symbol)
            
            # Get basic info
            info = ticker.info
            market_state = info.get('marketState', 'UNKNOWN')
            
            # Forex markets are generally open 24/5
            if any(pair in asset for pair in ['EUR/', 'GBP/', 'USD/', 'AUD/', 'NZD/', 'CAD/', 'CHF/', 'JPY']):
                return {
                    "is_open": True,
                    "market_state": "OPEN",
                    "asset_type": "forex"
                }
            
            return {
                "is_open": market_state in ['REGULAR', 'PREPRE', 'PRE', 'POSTPOST'],
                "market_state": market_state,
                "asset_type": "stock" if asset in ["AAPL", "GOOGL", "MSFT"] else "commodity"
            }
            
        except Exception as e:
            self.logger.error(f"Error checking market hours for {asset}: {e}")
            return {
                "is_open": True,  # Default to open to allow trading
                "market_state": "UNKNOWN",
                "asset_type": "unknown"
            }