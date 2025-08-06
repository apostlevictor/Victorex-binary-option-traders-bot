"""
Timezone handling utilities for Nigeria time (GMT+1)
"""

import pytz
from datetime import datetime, timedelta
from typing import Optional

class TimezoneHandler:
    """Handles timezone conversions and time operations"""
    
    def __init__(self, timezone_name: str = "Africa/Lagos"):
        self.timezone = pytz.timezone(timezone_name)
        self.utc = pytz.UTC
    
    def now(self) -> datetime:
        """Get current time in the configured timezone"""
        return datetime.now(self.timezone)
    
    def utc_now(self) -> datetime:
        """Get current UTC time"""
        return datetime.now(self.utc)
    
    def to_local(self, utc_time: datetime) -> datetime:
        """Convert UTC time to local timezone"""
        if utc_time.tzinfo is None:
            utc_time = self.utc.localize(utc_time)
        return utc_time.astimezone(self.timezone)
    
    def to_utc(self, local_time: datetime) -> datetime:
        """Convert local time to UTC"""
        if local_time.tzinfo is None:
            local_time = self.timezone.localize(local_time)
        return local_time.astimezone(self.utc)
    
    def format_time(self, dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
        """Format datetime with timezone info"""
        return dt.strftime(format_str)
    
    def get_expiration_time(self, minutes: int = 3) -> datetime:
        """Get expiration time from now + specified minutes"""
        return self.now() + timedelta(minutes=minutes)
    
    def is_expired(self, expiration_time: datetime) -> bool:
        """Check if a time has expired"""
        return self.now() > expiration_time
    
    def get_next_signal_time(self, interval_minutes: int = 5) -> datetime:
        """Calculate next signal time based on interval"""
        current_time = self.now()
        # Round to next interval
        minutes_since_hour = current_time.minute
        next_interval = ((minutes_since_hour // interval_minutes) + 1) * interval_minutes
        
        if next_interval >= 60:
            next_time = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        else:
            next_time = current_time.replace(minute=next_interval, second=0, microsecond=0)
        
        return next_time
    
    def time_until_expiration(self, expiration_time: datetime) -> str:
        """Get human-readable time until expiration"""
        time_diff = expiration_time - self.now()
        
        if time_diff.total_seconds() <= 0:
            return "EXPIRED"
        
        minutes = int(time_diff.total_seconds() // 60)
        seconds = int(time_diff.total_seconds() % 60)
        
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
