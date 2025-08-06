"""
Market analysis and technical indicators for signal generation
"""

import random
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from config.settings import TECHNICAL_INDICATORS, PATTERNS
from bot.market_data_fetcher import MarketDataFetcher

class MarketAnalyzer:
    """Analyzes market conditions and generates technical analysis data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.indicators = TECHNICAL_INDICATORS
        self.patterns = PATTERNS
        self.market_data_fetcher = MarketDataFetcher()
        
    def analyze_asset(self, asset: str, category: str) -> Dict:
        """Perform comprehensive technical analysis on an asset"""
        self.logger.info(f"Analyzing asset: {asset} in category: {category}")
        
        # Get real market data
        market_data = self.market_data_fetcher.get_real_time_data(asset)
        
        if market_data is None or market_data.empty:
            self.logger.warning(f"No real market data available for {asset}, using fallback")
            # Use fallback simulated data as backup
            return self._analyze_asset_fallback(asset, category)
        
        # Generate technical indicators from real data
        indicators = self.market_data_fetcher.calculate_technical_indicators(market_data)
        
        # Detect patterns from real data
        pattern_analysis = self.market_data_fetcher.detect_chart_patterns(market_data)
        
        # Calculate trend strength from real data
        trend_analysis = self._analyze_trend(indicators)
        
        # Generate market sentiment from real data
        sentiment = self.market_data_fetcher.analyze_market_sentiment(market_data, indicators)
        
        # Check market hours
        market_status = self.market_data_fetcher.get_market_hours_status(asset)
        
        analysis = {
            "asset": asset,
            "category": category,
            "timestamp": datetime.now(),
            "indicators": indicators,
            "patterns": pattern_analysis,
            "trend": trend_analysis,
            "sentiment": sentiment,
            "market_status": market_status,
            "data_source": "real_market_data",
            "confidence_factors": self._calculate_confidence_factors(indicators, pattern_analysis, trend_analysis)
        }
        
        return analysis
    
    def _analyze_asset_fallback(self, asset: str, category: str) -> Dict:
        """Fallback method using simulated data when real data is unavailable"""
        self.logger.info(f"Using fallback analysis for {asset}")
        
        # Generate technical indicators (simulated)
        indicators = self._generate_technical_indicators(asset)
        
        # Detect patterns (simulated)
        pattern_analysis = self._detect_patterns(asset, indicators)
        
        # Calculate trend strength
        trend_analysis = self._analyze_trend(indicators)
        
        # Generate market sentiment
        sentiment = self._calculate_market_sentiment(indicators, pattern_analysis)
        
        analysis = {
            "asset": asset,
            "category": category,
            "timestamp": datetime.now(),
            "indicators": indicators,
            "patterns": pattern_analysis,
            "trend": trend_analysis,
            "sentiment": sentiment,
            "market_status": {"is_open": True, "market_state": "SIMULATED", "asset_type": "simulated"},
            "data_source": "simulated_data",
            "confidence_factors": self._calculate_confidence_factors(indicators, pattern_analysis, trend_analysis)
        }
        
        return analysis
    
    def _generate_technical_indicators(self, asset: str) -> Dict:
        """Generate technical indicator values"""
        # Simulate realistic technical indicator values
        # In a real implementation, these would come from market data APIs
        
        indicators = {}
        
        # RSI (Relative Strength Index)
        rsi_config = self.indicators["RSI"]
        rsi_value = random.uniform(25, 75)
        indicators["RSI"] = {
            "value": rsi_value,
            "signal": "BUY" if rsi_value < rsi_config["oversold"] else "SELL" if rsi_value > rsi_config["overbought"] else "NEUTRAL",
            "strength": abs(rsi_value - 50) / 50
        }
        
        # MACD (Moving Average Convergence Divergence)
        macd_line = random.uniform(-0.5, 0.5)
        signal_line = random.uniform(-0.5, 0.5)
        indicators["MACD"] = {
            "macd_line": macd_line,
            "signal_line": signal_line,
            "histogram": macd_line - signal_line,
            "signal": "BUY" if macd_line > signal_line else "SELL",
            "strength": abs(macd_line - signal_line)
        }
        
        # Bollinger Bands
        middle_band = random.uniform(100, 200)
        band_width = random.uniform(5, 15)
        current_price = random.uniform(middle_band - band_width, middle_band + band_width)
        indicators["BOLLINGER"] = {
            "upper_band": middle_band + band_width,
            "middle_band": middle_band,
            "lower_band": middle_band - band_width,
            "current_price": current_price,
            "signal": "BUY" if current_price < middle_band - band_width * 0.8 else "SELL" if current_price > middle_band + band_width * 0.8 else "NEUTRAL",
            "strength": abs(current_price - middle_band) / band_width
        }
        
        # Stochastic Oscillator
        stoch_config = self.indicators["STOCHASTIC"]
        k_value = random.uniform(10, 90)
        d_value = random.uniform(10, 90)
        indicators["STOCHASTIC"] = {
            "k_value": k_value,
            "d_value": d_value,
            "signal": "BUY" if k_value < stoch_config["oversold"] else "SELL" if k_value > stoch_config["overbought"] else "NEUTRAL",
            "strength": abs(k_value - 50) / 50
        }
        
        # Williams %R
        williams_r = random.uniform(-100, 0)
        williams_config = self.indicators["WILLIAMS_R"]
        indicators["WILLIAMS_R"] = {
            "value": williams_r,
            "signal": "BUY" if williams_r < williams_config["oversold"] else "SELL" if williams_r > williams_config["overbought"] else "NEUTRAL",
            "strength": abs(williams_r + 50) / 50
        }
        
        # CCI (Commodity Channel Index)
        cci_value = random.uniform(-200, 200)
        cci_config = self.indicators["CCI"]
        indicators["CCI"] = {
            "value": cci_value,
            "signal": "BUY" if cci_value < cci_config["oversold"] else "SELL" if cci_value > cci_config["overbought"] else "NEUTRAL",
            "strength": abs(cci_value) / 200
        }
        
        return indicators
    
    def _detect_patterns(self, asset: str, indicators: Dict) -> Dict:
        """Detect candlestick and chart patterns"""
        patterns = {}
        
        # Simulate pattern detection
        bullish_patterns = self.patterns["BULLISH"]
        bearish_patterns = self.patterns["BEARISH"]
        
        # Random pattern detection with weighted probabilities
        if random.random() < 0.7:  # 70% chance of detecting a pattern
            pattern_type = random.choice(["BULLISH", "BEARISH"])
            if pattern_type == "BULLISH":
                detected_pattern = random.choice(bullish_patterns)
                patterns = {
                    "pattern": detected_pattern,
                    "type": "BULLISH",
                    "confidence": random.uniform(0.75, 0.95),
                    "signal": "BUY"
                }
            else:
                detected_pattern = random.choice(bearish_patterns)
                patterns = {
                    "pattern": detected_pattern,
                    "type": "BEARISH",
                    "confidence": random.uniform(0.75, 0.95),
                    "signal": "SELL"
                }
        else:
            patterns = {
                "pattern": None,
                "type": "NEUTRAL",
                "confidence": 0.5,
                "signal": "NEUTRAL"
            }
        
        return patterns
    
    def _analyze_trend(self, indicators: Dict) -> Dict:
        """Analyze overall trend direction and strength"""
        # Collect signals from all indicators
        signals = []
        strengths = []
        
        for indicator_name, indicator_data in indicators.items():
            signal = indicator_data.get("signal", "NEUTRAL")
            strength = indicator_data.get("strength", 0)
            
            if signal == "BUY":
                signals.append(1)
            elif signal == "SELL":
                signals.append(-1)
            else:
                signals.append(0)
            
            strengths.append(strength)
        
        # Calculate overall trend
        signal_sum = sum(signals)
        avg_strength = np.mean(strengths)
        
        if signal_sum > 1:
            trend_direction = "BULLISH"
            trend_signal = "BUY"
        elif signal_sum < -1:
            trend_direction = "BEARISH"
            trend_signal = "SELL"
        else:
            trend_direction = "SIDEWAYS"
            trend_signal = "NEUTRAL"
        
        return {
            "direction": trend_direction,
            "signal": trend_signal,
            "strength": avg_strength,
            "consensus": abs(signal_sum) / len(signals),
            "agreement_count": sum(1 for s in signals if s != 0)
        }
    
    def _calculate_market_sentiment(self, indicators: Dict, patterns: Dict) -> Dict:
        """Calculate overall market sentiment"""
        # Combine indicator sentiment with pattern sentiment
        indicator_sentiment = 0
        pattern_sentiment = 0
        
        # Calculate indicator sentiment
        for indicator_data in indicators.values():
            signal = indicator_data.get("signal", "NEUTRAL")
            strength = indicator_data.get("strength", 0)
            
            if signal == "BUY":
                indicator_sentiment += strength
            elif signal == "SELL":
                indicator_sentiment -= strength
        
        # Calculate pattern sentiment
        if patterns["type"] == "BULLISH":
            pattern_sentiment = patterns["confidence"]
        elif patterns["type"] == "BEARISH":
            pattern_sentiment = -patterns["confidence"]
        
        # Combine sentiments
        total_sentiment = (indicator_sentiment + pattern_sentiment * 2) / 3  # Weight patterns more heavily
        
        # Determine sentiment category
        if total_sentiment > 0.3:
            sentiment_category = "BULLISH"
        elif total_sentiment < -0.3:
            sentiment_category = "BEARISH"
        else:
            sentiment_category = "NEUTRAL"
        
        return {
            "value": total_sentiment,
            "category": sentiment_category,
            "indicator_sentiment": indicator_sentiment,
            "pattern_sentiment": pattern_sentiment,
            "confidence": min(abs(total_sentiment), 1.0)
        }
    
    def _calculate_confidence_factors(self, indicators: Dict, patterns: Dict, trend: Dict) -> Dict:
        """Calculate factors that contribute to signal confidence"""
        factors = {}
        
        # Indicator agreement
        buy_signals = sum(1 for ind in indicators.values() if ind.get("signal") == "BUY")
        sell_signals = sum(1 for ind in indicators.values() if ind.get("signal") == "SELL")
        total_indicators = len(indicators)
        
        factors["indicator_agreement"] = max(buy_signals, sell_signals) / total_indicators
        
        # Pattern confirmation
        factors["pattern_confirmation"] = patterns["confidence"] if patterns["pattern"] else 0
        
        # Trend strength
        factors["trend_strength"] = trend["strength"]
        
        # Signal consensus
        factors["signal_consensus"] = trend["consensus"]
        
        # Overall confidence calculation (adjusted for real market data)
        weights = {
            "indicator_agreement": 0.2,
            "pattern_confirmation": 0.4,  # Increase pattern weight for real data
            "trend_strength": 0.3,
            "signal_consensus": 0.1
        }
        
        overall_confidence = sum(factors[factor] * weights[factor] for factor in factors)
        factors["overall_confidence"] = min(overall_confidence, 1.0)
        
        return factors
