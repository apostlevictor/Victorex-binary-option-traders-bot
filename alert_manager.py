
"""
Alert management system for custom user notifications
"""

import json
import os
from typing import Dict, List, Optional, Set
from datetime import datetime, time
from utils.timezone_handler import TimezoneHandler

class AlertManager:
    """Manages custom alert settings for users"""
    
    def __init__(self):
        self.timezone_handler = TimezoneHandler()
        self.alerts_file = "user_alerts.json"
        self.user_alerts = self._load_alerts()
        
        # Default alert settings
        self.default_settings = {
            "enabled": True,
            "min_confidence": 75,
            "preferred_assets": ["all"],
            "excluded_assets": [],
            "alert_times": {
                "start": "09:00",
                "end": "22:00"
            },
            "max_signals_per_hour": 5,
            "signal_types": ["BUY", "SELL"],
            "sound_alerts": True,
            "instant_notifications": True,
            "weekend_alerts": False
        }
    
    def _load_alerts(self) -> Dict:
        """Load alert settings from file"""
        if os.path.exists(self.alerts_file):
            try:
                with open(self.alerts_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, ValueError):
                return {}
        return {}
    
    def _save_alerts(self):
        """Save alert settings to file"""
        with open(self.alerts_file, 'w') as f:
            json.dump(self.user_alerts, f, indent=2)
    
    def get_user_settings(self, user_id: int) -> Dict:
        """Get alert settings for a user"""
        user_id_str = str(user_id)
        if user_id_str in self.user_alerts:
            # Merge with defaults to ensure all keys exist
            settings = self.default_settings.copy()
            settings.update(self.user_alerts[user_id_str])
            return settings
        return self.default_settings.copy()
    
    def update_user_settings(self, user_id: int, settings: Dict) -> bool:
        """Update alert settings for a user"""
        user_id_str = str(user_id)
        
        # Validate settings
        if not self._validate_settings(settings):
            return False
        
        # Get current settings or defaults
        current_settings = self.get_user_settings(user_id)
        current_settings.update(settings)
        
        self.user_alerts[user_id_str] = current_settings
        self._save_alerts()
        return True
    
    def _validate_settings(self, settings: Dict) -> bool:
        """Validate alert settings"""
        try:
            # Validate confidence level
            if "min_confidence" in settings:
                conf = settings["min_confidence"]
                if not isinstance(conf, (int, float)) or conf < 50 or conf > 100:
                    return False
            
            # Validate alert times
            if "alert_times" in settings:
                times = settings["alert_times"]
                if "start" in times:
                    datetime.strptime(times["start"], "%H:%M")
                if "end" in times:
                    datetime.strptime(times["end"], "%H:%M")
            
            # Validate max signals per hour
            if "max_signals_per_hour" in settings:
                max_signals = settings["max_signals_per_hour"]
                if not isinstance(max_signals, int) or max_signals < 1 or max_signals > 20:
                    return False
            
            # Validate signal types
            if "signal_types" in settings:
                valid_types = {"BUY", "SELL"}
                signal_types = set(settings["signal_types"])
                if not signal_types.issubset(valid_types):
                    return False
            
            return True
        except (ValueError, TypeError, KeyError):
            return False
    
    def should_send_alert(self, user_id: int, signal_data: Dict) -> bool:
        """Check if alert should be sent to user based on their settings"""
        settings = self.get_user_settings(user_id)
        
        # Check if alerts are enabled
        if not settings.get("enabled", True):
            return False
        
        # Check confidence level
        signal_confidence = signal_data.get("confidence", 0)
        min_confidence = settings.get("min_confidence", 75)
        if signal_confidence < min_confidence:
            return False
        
        # Check signal direction
        signal_direction = signal_data.get("direction", "")
        allowed_types = settings.get("signal_types", ["BUY", "SELL"])
        if signal_direction not in allowed_types:
            return False
        
        # Check asset preferences
        asset = signal_data.get("asset", "")
        preferred_assets = settings.get("preferred_assets", ["all"])
        excluded_assets = settings.get("excluded_assets", [])
        
        # Check if asset is excluded
        if asset in excluded_assets:
            return False
        
        # Check if asset is in preferred list (unless "all" is selected)
        if "all" not in preferred_assets and asset not in preferred_assets:
            return False
        
        # Check time restrictions
        current_time = self.timezone_handler.now().time()
        alert_times = settings.get("alert_times", {})
        start_time = datetime.strptime(alert_times.get("start", "09:00"), "%H:%M").time()
        end_time = datetime.strptime(alert_times.get("end", "22:00"), "%H:%M").time()
        
        if not (start_time <= current_time <= end_time):
            return False
        
        # Check weekend settings
        if not settings.get("weekend_alerts", False):
            current_day = self.timezone_handler.now().weekday()
            if current_day >= 5:  # Saturday = 5, Sunday = 6
                return False
        
        return True
    
    def get_alert_summary(self, user_id: int) -> str:
        """Get formatted summary of user's alert settings"""
        settings = self.get_user_settings(user_id)
        
        status = "🟢 Enabled" if settings.get("enabled") else "🔴 Disabled"
        confidence = settings.get("min_confidence", 75)
        
        preferred = settings.get("preferred_assets", ["all"])
        if "all" in preferred:
            assets_text = "All assets"
        else:
            assets_text = f"{len(preferred)} selected assets"
        
        excluded = settings.get("excluded_assets", [])
        excluded_text = f" ({len(excluded)} excluded)" if excluded else ""
        
        alert_times = settings.get("alert_times", {})
        time_range = f"{alert_times.get('start', '09:00')} - {alert_times.get('end', '22:00')}"
        
        signal_types = settings.get("signal_types", ["BUY", "SELL"])
        types_text = " & ".join(signal_types)
        
        max_per_hour = settings.get("max_signals_per_hour", 5)
        weekend = "Yes" if settings.get("weekend_alerts", False) else "No"
        
        return f"""⚙️ **Your Alert Settings**

📊 **Status:** {status}
🎯 **Min Confidence:** {confidence}%
📈 **Signal Types:** {types_text}
🕐 **Active Hours:** {time_range}
📋 **Assets:** {assets_text}{excluded_text}
⏰ **Max/Hour:** {max_per_hour}
📅 **Weekend Alerts:** {weekend}

Use /alerts to modify these settings."""
```
