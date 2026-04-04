import pandas as pd

class IchimokuStrategy:
    def __init__(self, params=None):
        self.params = params or {
            'tenkan_period': 9,
            'kijun_period': 26,
            'enable_short': False,
            'stop_loss_pct': 5.0,
            'take_profit_pct': 10.0
        }
    
    def generate_signal(self, data):
        if len(data) < 52:
            return 0
        
        current = data.iloc[-1]
        
        long_signal = (
            current['price_above_cloud'] and
            current['ichimoku_tenkan'] > current['ichimoku_kijun']
        )
        
        short_signal = (
            self.params['enable_short'] and
            current['price_below_cloud'] and
            current['ichimoku_tenkan'] < current['ichimoku_kijun']
        )
        
        if long_signal:
            return 1
        elif short_signal:
            return -1
        
        return 0
