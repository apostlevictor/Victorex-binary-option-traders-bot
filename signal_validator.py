"""
Signal validation and quality assurance for trading signals
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from config.settings import VALIDATION_RULES, MINIMUM_CONFIDENCE, TARGET_ACCURACY

class SignalValidator:
    """Validates trading signals for quality and accuracy"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rules = VALIDATION_RULES
        self.signal_history = []  # Store recent signals for validation
        self.accuracy_tracker = {}  # Track accuracy per asset
        
    def validate_signal(self, signal_data: Dict) -> Tuple[bool, str]:
        """Validate a trading signal against all rules"""
        self.logger.info(f"Validating signal for {signal_data['asset']}")
        
        # Check minimum confidence
        if not self._check_minimum_confidence(signal_data):
            return False, "Signal confidence below minimum threshold"
        
        # Check asset cooldown
        if not self._check_asset_cooldown(signal_data):
            return False, "Asset still in cooldown period"
        
        # Check signal frequency
        if not self._check_signal_frequency(signal_data):
            return False, "Too many signals for this asset recently"
        
        # Check indicator agreement
        if not self._check_indicator_agreement(signal_data):
            return False, "Insufficient indicator agreement"
        
        # Check trend confirmation
        if not self._check_trend_confirmation(signal_data):
            return False, "Trend confirmation failed"
        
        # Check signal quality
        if not self._check_signal_quality(signal_data):
            return False, "Signal quality below standards"
        
        # Check historical accuracy
        if not self._check_historical_accuracy(signal_data):
            return False, "Asset historical accuracy below threshold"
        
        # All validations passed
        self.logger.info(f"Signal validation passed for {signal_data['asset']}")
        return True, "Signal validated successfully"
    
    def _check_minimum_confidence(self, signal_data: Dict) -> bool:
        """Check if signal meets minimum confidence requirement"""
        confidence = signal_data.get("confidence", 0)
        return confidence >= self.rules["min_confidence"]
    
    def _check_asset_cooldown(self, signal_data: Dict) -> bool:
        """Check if asset is still in cooldown period"""
        asset = signal_data["asset"]
        cooldown_minutes = self.rules["cooldown_minutes"]
        current_time = datetime.now()
        
        # Find last signal for this asset
        for signal in reversed(self.signal_history):
            if signal["asset"] == asset:
                time_diff = (current_time - signal["timestamp"]).total_seconds() / 60
                if time_diff < cooldown_minutes:
                    return False
                break
        
        return True
    
    def _check_signal_frequency(self, signal_data: Dict) -> bool:
        """Check if we're not sending too many signals for this asset"""
        asset = signal_data["asset"]
        max_signals = self.rules["max_signals_per_asset"]
        current_time = datetime.now()
        one_hour_ago = current_time - timedelta(hours=1)
        
        # Count signals for this asset in the last hour
        recent_signals = [
            signal for signal in self.signal_history
            if signal["asset"] == asset and signal["timestamp"] > one_hour_ago
        ]
        
        return len(recent_signals) < max_signals
    
    def _check_indicator_agreement(self, signal_data: Dict) -> bool:
        """Check if enough indicators agree on the signal direction"""
        required_indicators = self.rules["required_indicators"]
        analysis = signal_data.get("analysis", {})
        indicators = analysis.get("indicators", {})
        
        signal_direction = signal_data["direction"]
        agreeing_indicators = 0
        
        for indicator_data in indicators.values():
            if indicator_data.get("signal") == signal_direction:
                agreeing_indicators += 1
        
        return agreeing_indicators >= required_indicators
    
    def _check_trend_confirmation(self, signal_data: Dict) -> bool:
        """Check if trend analysis confirms the signal"""
        if not self.rules["trend_confirmation"]:
            return True
        
        analysis = signal_data.get("analysis", {})
        trend = analysis.get("trend", {})
        signal_direction = signal_data["direction"]
        
        # Check if trend direction aligns with signal
        trend_signal = trend.get("signal", "NEUTRAL")
        trend_strength = trend.get("strength", 0)
        
        # Trend should align with signal and have sufficient strength
        return trend_signal == signal_direction and trend_strength > 0.5
    
    def _check_signal_quality(self, signal_data: Dict) -> bool:
        """Check overall signal quality based on multiple factors"""
        analysis = signal_data.get("analysis", {})
        
        # Check sentiment alignment
        sentiment = analysis.get("sentiment", {})
        sentiment_confidence = sentiment.get("confidence", 0)
        
        # Check pattern confirmation
        patterns = analysis.get("patterns", {})
        pattern_confidence = patterns.get("confidence", 0)
        
        # Check confidence factors
        confidence_factors = analysis.get("confidence_factors", {})
        overall_confidence = confidence_factors.get("overall_confidence", 0)
        
        # Quality thresholds (more lenient for real market data)
        min_sentiment_confidence = 0.3
        min_pattern_confidence = 0.4 if patterns.get("pattern") else 0  # Only if pattern detected
        min_overall_confidence = 0.3
        
        return (sentiment_confidence >= min_sentiment_confidence and
                pattern_confidence >= min_pattern_confidence and
                overall_confidence >= min_overall_confidence)
    
    def _check_historical_accuracy(self, signal_data: Dict) -> bool:
        """Check if asset has maintained acceptable accuracy"""
        asset = signal_data["asset"]
        
        if asset not in self.accuracy_tracker:
            return True  # No history yet, allow signal
        
        accuracy_data = self.accuracy_tracker[asset]
        total_signals = accuracy_data.get("total", 0)
        correct_signals = accuracy_data.get("correct", 0)
        
        if total_signals < 10:  # Not enough data
            return True
        
        accuracy = (correct_signals / total_signals) * 100
        return accuracy >= 70  # Minimum 70% accuracy required
    
    def record_signal(self, signal_data: Dict):
        """Record a signal for tracking and validation"""
        signal_record = {
            "asset": signal_data["asset"],
            "direction": signal_data["direction"],
            "confidence": signal_data["confidence"],
            "timestamp": datetime.now(),
            "expiration_time": signal_data["expiration_time"]
        }
        
        self.signal_history.append(signal_record)
        
        # Keep only last 100 signals to manage memory
        if len(self.signal_history) > 100:
            self.signal_history = self.signal_history[-100:]
        
        self.logger.info(f"Signal recorded for {signal_data['asset']}")
    
    def update_accuracy(self, asset: str, was_correct: bool):
        """Update accuracy tracking for an asset"""
        if asset not in self.accuracy_tracker:
            self.accuracy_tracker[asset] = {"total": 0, "correct": 0}
        
        self.accuracy_tracker[asset]["total"] += 1
        if was_correct:
            self.accuracy_tracker[asset]["correct"] += 1
        
        # Calculate current accuracy
        total = self.accuracy_tracker[asset]["total"]
        correct = self.accuracy_tracker[asset]["correct"]
        accuracy = (correct / total) * 100
        
        self.logger.info(f"Updated accuracy for {asset}: {accuracy:.1f}% ({correct}/{total})")
    
    def get_validation_stats(self) -> Dict:
        """Get validation statistics"""
        return {
            "total_signals": len(self.signal_history),
            "accuracy_tracker": self.accuracy_tracker.copy(),
            "validation_rules": self.rules
        }
    
    def cleanup_old_signals(self, hours: int = 24):
        """Remove signals older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        self.signal_history = [
            signal for signal in self.signal_history
            if signal["timestamp"] > cutoff_time
        ]
        
        self.logger.info(f"Cleaned up signals older than {hours} hours")
