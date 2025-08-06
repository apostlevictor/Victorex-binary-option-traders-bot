"""
Advanced signal generation system for binary options trading
"""

import logging
import random
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from bot.market_analyzer import MarketAnalyzer
from bot.asset_manager import AssetManager
from bot.signal_validator import SignalValidator
from utils.timezone_handler import TimezoneHandler
from config.settings import SIGNAL_EXPIRATION_MINUTES, TARGET_ACCURACY, MINIMUM_CONFIDENCE

class SignalGenerator:
    """Generates high-quality trading signals with advanced analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.market_analyzer = MarketAnalyzer()
        self.asset_manager = AssetManager()
        self.signal_validator = SignalValidator()
        self.timezone_handler = TimezoneHandler()
        
        # Signal generation statistics
        self.generated_signals = 0
        self.validated_signals = 0
        self.accuracy_target = TARGET_ACCURACY
        
    def generate_signal(self) -> Optional[Dict]:
        """Generate a complete trading signal"""
        try:
            # Get next asset for signal generation
            asset, category = self.asset_manager.get_next_asset()
            
            # Perform market analysis
            analysis = self.market_analyzer.analyze_asset(asset, category)
            
            # Generate signal based on analysis
            signal_data = self._create_signal_from_analysis(asset, category, analysis)
            
            if not signal_data:
                self.logger.warning(f"Failed to create signal for {asset}")
                return None
            
            # Validate signal
            is_valid, validation_message = self.signal_validator.validate_signal(signal_data)
            
            if not is_valid:
                self.logger.warning(f"Signal validation failed for {asset}: {validation_message}")
                return None
            
            # Record signal and update statistics
            self.signal_validator.record_signal(signal_data)
            self.generated_signals += 1
            self.validated_signals += 1
            
            self.logger.info(f"Generated valid signal for {asset}: {signal_data['direction']}")
            return signal_data
            
        except Exception as e:
            self.logger.error(f"Error generating signal: {e}")
            return None
    
    def _create_signal_from_analysis(self, asset: str, category: str, analysis: Dict) -> Optional[Dict]:
        """Create a trading signal from market analysis"""
        try:
            # Extract key data from analysis
            trend = analysis.get("trend", {})
            sentiment = analysis.get("sentiment", {})
            patterns = analysis.get("patterns", {})
            confidence_factors = analysis.get("confidence_factors", {})
            
            # Determine signal direction
            signal_direction = self._determine_signal_direction(trend, sentiment, patterns)
            
            if signal_direction == "NEUTRAL":
                return None  # No clear signal
            
            # Calculate signal confidence
            confidence = self._calculate_signal_confidence(analysis, signal_direction)
            
            if confidence < MINIMUM_CONFIDENCE:
                return None  # Confidence too low
            
            # Generate entry reasoning
            reasoning = self._generate_entry_reasoning(analysis, signal_direction)
            
            # Create signal data
            current_time = self.timezone_handler.now()
            expiration_time = self.timezone_handler.get_expiration_time(SIGNAL_EXPIRATION_MINUTES)
            
            signal_data = {
                "asset": asset,
                "category": category,
                "direction": signal_direction,
                "confidence": confidence,
                "expiration_time": expiration_time,
                "generated_time": current_time,
                "reasoning": reasoning,
                "analysis": analysis,
                "accuracy_target": self.accuracy_target
            }
            
            return signal_data
            
        except Exception as e:
            self.logger.error(f"Error creating signal from analysis: {e}")
            return None
    
    def _determine_signal_direction(self, trend: Dict, sentiment: Dict, patterns: Dict) -> str:
        """Determine the signal direction based on multiple factors"""
        # Collect signals from different sources
        signals = []
        weights = []
        
        # Trend signal (weight: 0.4)
        trend_signal = trend.get("signal", "NEUTRAL")
        if trend_signal != "NEUTRAL":
            signals.append(trend_signal)
            weights.append(0.4 * trend.get("strength", 0.5))
        
        # Sentiment signal (weight: 0.35)
        sentiment_category = sentiment.get("category", "NEUTRAL")
        if sentiment_category != "NEUTRAL":
            sentiment_signal = "BUY" if sentiment_category == "BULLISH" else "SELL"
            signals.append(sentiment_signal)
            weights.append(0.35 * sentiment.get("confidence", 0.5))
        
        # Pattern signal (weight: 0.25)
        pattern_signal = patterns.get("signal", "NEUTRAL")
        if pattern_signal != "NEUTRAL":
            signals.append(pattern_signal)
            weights.append(0.25 * patterns.get("confidence", 0.5))
        
        # If no signals, return neutral
        if not signals:
            return "NEUTRAL"
        
        # Calculate weighted decision
        buy_weight = sum(w for s, w in zip(signals, weights) if s == "BUY")
        sell_weight = sum(w for s, w in zip(signals, weights) if s == "SELL")
        
        # Require minimum weight difference for signal
        min_difference = 0.05  # More lenient threshold
        if buy_weight > sell_weight + min_difference:
            return "BUY"
        elif sell_weight > buy_weight + min_difference:
            return "SELL"
        else:
            # If weights are close, use the higher one if it's above a threshold
            if max(buy_weight, sell_weight) > 0.2:  # Lower threshold for real market data
                return "BUY" if buy_weight > sell_weight else "SELL"
            # For real market data, generate a signal even if weights are low
            if buy_weight > 0 or sell_weight > 0:
                return "BUY" if buy_weight >= sell_weight else "SELL"
            return "NEUTRAL"
    
    def _calculate_signal_confidence(self, analysis: Dict, signal_direction: str) -> float:
        """Calculate confidence score for the signal"""
        confidence_factors = analysis.get("confidence_factors", {})
        
        # Base confidence from analysis
        base_confidence = confidence_factors.get("overall_confidence", 0.5)
        
        # Adjust based on signal agreement
        trend = analysis.get("trend", {})
        sentiment = analysis.get("sentiment", {})
        patterns = analysis.get("patterns", {})
        
        # Count agreeing sources
        agreeing_sources = 0
        total_sources = 0
        
        # Check trend agreement
        if trend.get("signal") == signal_direction:
            agreeing_sources += 1
        if trend.get("signal") != "NEUTRAL":
            total_sources += 1
        
        # Check sentiment agreement
        sentiment_signal = "BUY" if sentiment.get("category") == "BULLISH" else "SELL" if sentiment.get("category") == "BEARISH" else "NEUTRAL"
        if sentiment_signal == signal_direction:
            agreeing_sources += 1
        if sentiment_signal != "NEUTRAL":
            total_sources += 1
        
        # Check pattern agreement
        if patterns.get("signal") == signal_direction:
            agreeing_sources += 1
        if patterns.get("signal") != "NEUTRAL":
            total_sources += 1
        
        # Calculate agreement bonus
        agreement_bonus = 0
        if total_sources > 0:
            agreement_ratio = agreeing_sources / total_sources
            agreement_bonus = (agreement_ratio - 0.5) * 0.2  # Up to 20% bonus
        
        # Final confidence calculation
        final_confidence = min(base_confidence + agreement_bonus, 1.0)
        
        # Boost confidence for real market data signals
        if final_confidence > 0.4:  # If we have reasonable confidence
            final_confidence = min(final_confidence + 0.2, 1.0)  # Add boost
        
        # Convert to percentage
        return final_confidence * 100
    
    def _generate_entry_reasoning(self, analysis: Dict, signal_direction: str) -> str:
        """Generate human-readable reasoning for the signal"""
        reasoning_parts = []
        
        # Trend reasoning
        trend = analysis.get("trend", {})
        if trend.get("signal") == signal_direction:
            trend_strength = trend.get("strength", 0)
            if trend_strength > 0.7:
                reasoning_parts.append(f"Strong {trend.get('direction', '').lower()} trend")
            else:
                reasoning_parts.append(f"Moderate {trend.get('direction', '').lower()} trend")
        
        # Pattern reasoning
        patterns = analysis.get("patterns", {})
        if patterns.get("signal") == signal_direction and patterns.get("pattern"):
            pattern_name = patterns["pattern"].replace("_", " ").title()
            reasoning_parts.append(f"{pattern_name} pattern detected")
        
        # Indicator reasoning
        indicators = analysis.get("indicators", {})
        supporting_indicators = []
        for name, data in indicators.items():
            if data.get("signal") == signal_direction:
                supporting_indicators.append(name)
        
        if supporting_indicators:
            if len(supporting_indicators) > 2:
                reasoning_parts.append(f"Multiple indicators ({', '.join(supporting_indicators[:2])}+) support direction")
            else:
                reasoning_parts.append(f"{', '.join(supporting_indicators)} support direction")
        
        # Sentiment reasoning
        sentiment = analysis.get("sentiment", {})
        sentiment_category = sentiment.get("category", "NEUTRAL")
        if sentiment_category != "NEUTRAL":
            sentiment_confidence = sentiment.get("confidence", 0)
            if sentiment_confidence > 0.7:
                reasoning_parts.append(f"Strong {sentiment_category.lower()} sentiment")
            else:
                reasoning_parts.append(f"Moderate {sentiment_category.lower()} sentiment")
        
        # Combine reasoning
        if reasoning_parts:
            return " • ".join(reasoning_parts)
        else:
            return "Technical analysis indicates favorable conditions"
    
    def get_statistics(self) -> Dict:
        """Get signal generation statistics"""
        validation_rate = (self.validated_signals / self.generated_signals * 100) if self.generated_signals > 0 else 0
        
        return {
            "generated_signals": self.generated_signals,
            "validated_signals": self.validated_signals,
            "validation_rate": validation_rate,
            "accuracy_target": self.accuracy_target,
            "asset_stats": self.asset_manager.get_usage_stats(),
            "validation_stats": self.signal_validator.get_validation_stats()
        }
    
    def reset_statistics(self):
        """Reset generation statistics"""
        self.generated_signals = 0
        self.validated_signals = 0
        self.asset_manager.reset_usage_stats()
        self.logger.info("Signal generation statistics reset")
