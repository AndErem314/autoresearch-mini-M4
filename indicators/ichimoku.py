import pandas as pd
import numpy as np

def calculate_ichimoku(data, tenkan=9, kijun=26, senkou_b=52):
    """Calculate Ichimoku Cloud indicators."""
    # Tenkan-sen
    tenkan_high = data['high'].rolling(tenkan).max()
    tenkan_low = data['low'].rolling(tenkan).min()
    data['ichimoku_tenkan'] = (tenkan_high + tenkan_low) / 2
    
    # Kijun-sen
    kijun_high = data['high'].rolling(kijun).max()
    kijun_low = data['low'].rolling(kijun).min()
    data['ichimoku_kijun'] = (kijun_high + kijun_low) / 2
    
    # Senkou Span A
    data['ichimoku_senkou_a'] = ((data['ichimoku_tenkan'] + data['ichimoku_kijun']) / 2).shift(kijun)
    
    # Senkou Span B
    senkou_b_high = data['high'].rolling(senkou_b).max()
    senkou_b_low = data['low'].rolling(senkou_b).min()
    data['ichimoku_senkou_b'] = ((senkou_b_high + senkou_b_low) / 2).shift(kijun)
    
    # Cloud boundaries
    data['ichimoku_cloud_top'] = data[['ichimoku_senkou_a', 'ichimoku_senkou_b']].max(axis=1)
    data['ichimoku_cloud_bottom'] = data[['ichimoku_senkou_a', 'ichimoku_senkou_b']].min(axis=1)
    
    # Position relative to cloud
    data['price_above_cloud'] = data['close'] > data['ichimoku_cloud_top']
    data['price_below_cloud'] = data['close'] < data['ichimoku_cloud_bottom']
    data['price_in_cloud'] = ~(data['price_above_cloud'] | data['price_below_cloud'])
    
    return data
