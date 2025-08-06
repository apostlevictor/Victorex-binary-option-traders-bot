"""
Asset management and rotation for trading signals
"""

import random
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from config.settings import CURRENCY_PAIRS, CRYPTOCURRENCIES, OTC_CURRENCY_PAIRS, OTC_CRYPTOCURRENCIES

class AssetManager:
    """Manages asset rotation and selection for trading signals"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.assets = {
            "currency_pairs": CURRENCY_PAIRS,
            "cryptocurrencies": CRYPTOCURRENCIES,
            "otc_currency_pairs": OTC_CURRENCY_PAIRS,
            "otc_cryptocurrencies": OTC_CRYPTOCURRENCIES
        }
        self.last_used = {}  # Track last used time for each asset
        self.usage_count = {}  # Track usage count for each asset
        self.current_rotation_index = 0
        self.category_rotation = ["currency_pairs", "cryptocurrencies", "otc_currency_pairs", "otc_cryptocurrencies"]
        
    def get_next_asset(self) -> tuple[str, str]:
        """Get next asset using intelligent rotation"""
        category = self._get_next_category()
        asset = self._select_asset_from_category(category)
        
        # Update tracking
        self.last_used[asset] = datetime.now()
        self.usage_count[asset] = self.usage_count.get(asset, 0) + 1
        
        self.logger.info(f"Selected asset: {asset} from category: {category}")
        return asset, category
    
    def _get_next_category(self) -> str:
        """Get next category using round-robin rotation"""
        category = self.category_rotation[self.current_rotation_index]
        self.current_rotation_index = (self.current_rotation_index + 1) % len(self.category_rotation)
        return category
    
    def _select_asset_from_category(self, category: str) -> str:
        """Select asset from category with smart selection"""
        available_assets = self.assets[category]
        
        # Filter out recently used assets (within last 30 minutes)
        current_time = datetime.now()
        filtered_assets = []
        
        for asset in available_assets:
            last_used = self.last_used.get(asset)
            if not last_used or (current_time - last_used).total_seconds() > 1800:  # 30 minutes
                filtered_assets.append(asset)
        
        # If all assets were used recently, reset and use all
        if not filtered_assets:
            filtered_assets = available_assets
            self.logger.info(f"All assets in {category} used recently, resetting rotation")
        
        # Select asset with lowest usage count, with some randomness
        asset_weights = []
        for asset in filtered_assets:
            usage = self.usage_count.get(asset, 0)
            # Lower usage = higher weight
            weight = max(1, 10 - usage)
            asset_weights.append(weight)
        
        # Weighted random selection
        selected_asset = random.choices(filtered_assets, weights=asset_weights)[0]
        return selected_asset
    
    def get_asset_info(self, asset: str) -> Dict:
        """Get information about a specific asset"""
        category = self._get_asset_category(asset)
        return {
            "asset": asset,
            "category": category,
            "last_used": self.last_used.get(asset),
            "usage_count": self.usage_count.get(asset, 0)
        }
    
    def _get_asset_category(self, asset: str) -> str:
        """Determine which category an asset belongs to"""
        for category, assets in self.assets.items():
            if asset in assets:
                return category
        return "unknown"
    
    def get_category_display_name(self, category: str) -> str:
        """Get display name for category"""
        display_names = {
            "currency_pairs": "Currency Pair",
            "cryptocurrencies": "Cryptocurrency", 
            "otc_currency_pairs": "OTC Currency Pair",
            "otc_cryptocurrencies": "OTC Cryptocurrency"
        }
        return display_names.get(category, category.title())
    
    def reset_usage_stats(self):
        """Reset usage statistics"""
        self.usage_count.clear()
        self.last_used.clear()
        self.logger.info("Asset usage statistics reset")
    
    def get_usage_stats(self) -> Dict:
        """Get current usage statistics"""
        return {
            "usage_count": self.usage_count.copy(),
            "last_used": self.last_used.copy(),
            "total_assets": sum(len(assets) for assets in self.assets.values())
        }
