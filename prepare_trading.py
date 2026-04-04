"""
Trading data preparation for BTC/USDT 4-hour chart optimization.
Downloads BTC historical data, calculates indicators including Ichimoku Cloud,
and prepares train/validation/test splits.

Usage:
    python prepare_trading.py                  # full data preparation
    python prepare_trading.py --test           # test mode with smaller dataset
    python prepare_trading.py --update         # update with latest data

Data is stored in ~/.cache/autoresearch-trading/.
"""

import argparse
import os
import pickle
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
import yfinance as yf
from ta import add_all_ta_features
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator, EMAIndicator, IchimokuIndicator
from ta.volatility import BollingerBands
from ta.volume import VolumeWeightedAveragePrice

# ---------------------------------------------------------------------------
# Constants (fixed, do not modify)
# ---------------------------------------------------------------------------

TIME_BUDGET = 300  # 5-minute backtest budget
TRAIN_START = "2021-11-01"
TRAIN_END = "2023-11-01"
VAL_START = "2023-11-01"
VAL_END = "2024-03-01"
TEST_START = "2024-03-01"
TEST_END = "2024-04-01"

# Trading parameters
INITIAL_CAPITAL = 10000.0
TRADING_FEE = 0.001  # 0.1% trading fee
POSITION_SIZE = 0.1   # 10% of capital per trade

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "autoresearch-trading")
DATA_DIR = os.path.join(CACHE_DIR, "data")
INDICATORS_DIR = os.path.join(CACHE_DIR, "indicators")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(INDICATORS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------

def download_btc_data(
    start_date: str = TRAIN_START,
    end_date: str = TEST_END,
    interval: str = "4h",
    force_download: bool = False
) -> pd.DataFrame:
    """
    Download BTC/USDT 4-hour chart data from Yahoo Finance.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        interval: Data interval ('1h', '4h', '1d', etc.)
        force_download: Force re-download even if cached
        
    Returns:
        DataFrame with OHLCV data
    """
    cache_file = os.path.join(DATA_DIR, f"btc_usdt_{interval}_{start_date}_{end_date}.pkl")
    
    # Use cache if available and not forcing download
    if os.path.exists(cache_file) and not force_download:
        print(f"Loading cached data from {cache_file}")
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    
    print(f"Downloading BTC/USDT {interval} data from {start_date} to {end_date}...")
    
    # Download data
    ticker = yf.Ticker("BTC-USD")
    data = ticker.history(start=start_date, end=end_date, interval=interval)
    
    if data.empty:
        raise ValueError(f"No data downloaded for BTC-USD from {start_date} to {end_date}")
    
    # Ensure proper column names
    data.columns = [col.lower() for col in data.columns]
    
    # Add datetime index if not present
    if not isinstance(data.index, pd.DatetimeIndex):
        data.index = pd.to_datetime(data.index)
    
    print(f"Downloaded {len(data)} rows of {interval} data")
    print(f"Date range: {data.index[0]} to {data.index[-1]}")
    
    # Save to cache
    with open(cache_file, 'wb') as f:
        pickle.dump(data, f)
    
    return data

# ---------------------------------------------------------------------------
# Indicator Calculation
# ---------------------------------------------------------------------------

def calculate_ichimoku_cloud(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Ichimoku Cloud indicators.
    
    Ichimoku Cloud consists of:
    - Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
    - Kijun-sen (Base Line): (26-period high + 26-period low)/2
    - Senkou Span A (Leading Span A): (Tenkan-sen + Kijun-sen)/2, shifted 26 periods forward
    - Senkou Span B (Leading Span B): (52-period high + 52-period low)/2, shifted 26 periods forward
    - Chikou Span (Lagging Span): Close price shifted 26 periods backward
    
    Args:
        df: DataFrame with OHLC data
        
    Returns:
        DataFrame with Ichimoku columns added
    """
    df = df.copy()
    
    # Calculate periods
    high_9 = df['high'].rolling(window=9).max()
    low_9 = df['low'].rolling(window=9).min()
    df['ichimoku_tenkan'] = (high_9 + low_9) / 2
    
    high_26 = df['high'].rolling(window=26).max()
    low_26 = df['low'].rolling(window=26).min()
    df['ichimoku_kijun'] = (high_26 + low_26) / 2
    
    df['ichimoku_senkou_a'] = ((df['ichimoku_tenkan'] + df['ichimoku_kijun']) / 2).shift(26)
    
    high_52 = df['high'].rolling(window=52).max()
    low_52 = df['low'].rolling(window=52).min()
    df['ichimoku_senkou_b'] = ((high_52 + low_52) / 2).shift(26)
    
    df['ichimoku_chikou'] = df['close'].shift(-26)
    
    # Cloud status
    df['ichimoku_cloud_top'] = df[['ichimoku_senkou_a', 'ichimoku_senkou_b']].max(axis=1)
    df['ichimoku_cloud_bottom'] = df[['ichimoku_senkou_a', 'ichimoku_senkou_b']].min(axis=1)
    df['ichimoku_price_above_cloud'] = df['close'] > df['ichimoku_cloud_top']
    df['ichimoku_price_below_cloud'] = df['close'] < df['ichimoku_cloud_bottom']
    df['ichimoku_price_in_cloud'] = (df['close'] <= df['ichimoku_cloud_top']) & (df['close'] >= df['ichimoku_cloud_bottom'])
    
    # Tenkan/Kijun cross
    df['ichimoku_tk_cross'] = df['ichimoku_tenkan'] > df['ichimoku_kijun']
    df['ichimoku_tk_cross_prev'] = df['ichimoku_tk_cross'].shift(1)
    df['ichimoku_golden_cross'] = (df['ichimoku_tk_cross'] == True) & (df['ichimoku_tk_cross_prev'] == False)
    df['ichimoku_death_cross'] = (df['ichimoku_tk_cross'] == False) & (df['ichimoku_tk_cross_prev'] == True)
    
    return df

def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all technical indicators for trading.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with all indicators added
    """
    df = df.copy()
    
    # 1. Ichimoku Cloud (our main focus)
    df = calculate_ichimoku_cloud(df)
    
    # 2. Moving Averages
    df['sma_20'] = SMAIndicator(close=df['close'], window=20).sma_indicator()
    df['sma_50'] = SMAIndicator(close=df['close'], window=50).sma_indicator()
    df['sma_200'] = SMAIndicator(close=df['close'], window=200).sma_indicator()
    df['ema_12'] = EMAIndicator(close=df['close'], window=12).ema_indicator()
    df['ema_26'] = EMAIndicator(close=df['close'], window=26).ema_indicator()
    
    # 3. Momentum Indicators
    df['rsi_14'] = RSIIndicator(close=df['close'], window=14).rsi()
    df['rsi_7'] = RSIIndicator(close=df['close'], window=7).rsi()
    df['rsi_21'] = RSIIndicator(close=df['close'], window=21).rsi()
    
    # 4. MACD
    macd = MACD(close=df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_diff'] = macd.macd_diff()
    
    # 5. Bollinger Bands
    bb = BollingerBands(close=df['close'], window=20, window_dev=2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_middle'] = bb.bollinger_mavg()
    df['bb_lower'] = bb.bollinger_lband()
    df['bb_width'] = bb.bollinger_wband()
    df['bb_pct'] = bb.bollinger_pband()
    
    # 6. Volume Indicators
    df['vwap'] = VolumeWeightedAveragePrice(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        volume=df['volume'],
        window=20
    ).volume_weighted_average_price()
    
    # 7. Price-based features
    df['returns'] = df['close'].pct_change()
    df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
    df['volatility_20'] = df['returns'].rolling(window=20).std()
    df['high_low_ratio'] = df['high'] / df['low']
    df['close_open_ratio'] = df['close'] / df['open']
    
    # 8. Support/Resistance levels (simplified)
    df['resistance_20'] = df['high'].rolling(window=20).max()
    df['support_20'] = df['low'].rolling(window=20).min()
    
    # 9. Ichimoku-specific derived features
    df['ichimoku_cloud_width'] = df['ichimoku_cloud_top'] - df['ichimoku_cloud_bottom']
    df['ichimoku_cloud_mid'] = (df['ichimoku_cloud_top'] + df['ichimoku_cloud_bottom']) / 2
    df['ichimoku_distance_to_cloud'] = df['close'] - df['ichimoku_cloud_mid']
    df['ichimoku_distance_to_tenkan'] = df['close'] - df['ichimoku_tenkan']
    df['ichimoku_distance_to_kijun'] = df['close'] - df['ichimoku_kijun']
    
    return df

def prepare_data_splits(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Split data into train, validation, and test sets.
    
    Args:
        df: DataFrame with all indicators
        
    Returns:
        Dictionary with train, val, test DataFrames
    """
    # Convert date strings to datetime
    train_start = pd.to_datetime(TRAIN_START)
    train_end = pd.to_datetime(TRAIN_END)
    val_start = pd.to_datetime(VAL_START)
    val_end = pd.to_datetime(VAL_END)
    test_start = pd.to_datetime(TEST_START)
    test_end = pd.to_datetime(TEST_END)
    
    # Create splits
    train_data = df[(df.index >= train_start) & (df.index < train_end)].copy()
    val_data = df[(df.index >= val_start) & (df.index < val_end)].copy()
    test_data = df[(df.index >= test_start) & (df.index < test_end)].copy()
    
    # Drop NaN values (from indicator calculations)
    train_data = train_data.dropna()
    val_data = val_data.dropna()
    test_data = test_data.dropna()
    
    print(f"Train data: {len(train_data)} rows ({train_data.index[0]} to {train_data.index[-1]})")
    print(f"Validation data: {len(val_data)} rows ({val_data.index[0]} to {val_data.index[-1]})")
    print(f"Test data: {len(test_data)} rows ({test_data.index[0]} to {test_data.index[-1]})")
    
    return {
        'train': train_data,
        'val': val_data,
        'test': test_data
    }

# ---------------------------------------------------------------------------
# Main Preparation Function
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Prepare BTC trading data for autoresearch')
    parser.add_argument('--test', action='store_true', help='Test mode with smaller date range')
    parser.add_argument('--update', action='store_true', help='Force update data download')
    parser.add_argument('--start', type=str, default=TRAIN_START, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, default=TEST_END, help='End date (YYYY-MM-DD)')
    args = parser.parse_args()
    
    # Adjust dates for test mode
    if args.test:
        print("Running in test mode with smaller dataset")
        start_date = "2024-01-01"
        end_date = "2024-02-01"
    else:
        start_date = args.start
        end_date = args.end
    
    try:
        # 1. Download data
        print("=" * 60)
        print("Step 1: Downloading BTC/USDT 4-hour data")
        print("=" * 60)
        data = download_btc_data(
            start_date=start_date,
            end_date=end_date,
            interval="4h",
            force_download=args.update
        )
        
        # 2. Calculate indicators
        print("\n" + "=" * 60)
        print("Step 2: Calculating technical indicators")
        print("=" * 60)
        print("Calculating Ichimoku Cloud indicators...")
        data_with_indicators = calculate_all_indicators(data)
        
        # 3. Prepare splits
        print("\n" + "=" * 60)
        print("Step 3: Preparing train/validation/test splits")
        print("=" * 60)
        splits = prepare_data_splits(data_with_indicators)
        
        # 4. Save prepared data
        print("\n" + "=" * 60)
        print("Step 4: Saving prepared data")
        print("=" * 60)
        
        # Save splits
        splits_file = os.path.join(INDICATORS_DIR, "data_splits.pkl")
        with open(splits_file, 'wb') as f:
            pickle.dump(splits, f)
        
        # Save metadata
        metadata = {
            'train_start': TRAIN_START,
            'train_end': TRAIN_END,
            'val_start': VAL_START,
            'val_end': VAL_END,
            'test_start': TEST_START,
            'test_end': TEST_END,
            'interval': '4h',
            'initial_capital': INITIAL_CAPITAL,
            'trading_fee': TRADING_FEE,
            'position_size': POSITION_SIZE,
            'indicators_calculated': list(data_with_indicators.columns),
            'prepared_at': datetime.now().isoformat()
        }
        
        metadata_file = os.path.join(INDICATORS_DIR, "metadata.pkl")
        with open(metadata_file, 'wb') as f:
            pickle.dump(metadata, f)
        
        print(f"✓ Data splits saved to {splits_file}")
        print(f"✓ Metadata saved to {metadata_file}")
        
        # 5. Print summary
        print("\n" + "=" * 60)
        print("DATA PREPARATION COMPLETE")
        print("=" * 60)
        print(f"Total data points: {len(data)}")
        print(f"Indicators calculated: {len(data_with_indicators.columns)}")
        print(f"Train samples: {len(splits['train'])}")
        print(f"Validation samples: {len(splits['val'])}")
        print(f"Test samples: {len(splits['test'])}")
        print(f"\nIchimoku Cloud indicators available:")
        ichimoku_cols = [col for col in data_with_indicators.columns if 'ichimoku' in col]
        for col in ichimoku_cols:
            print(f"  - {col}")
        
        print(f"\nOther key indicators:")
        other_key = ['rsi_14', 'macd', 'macd_signal', 'sma_20', 'sma_50', 'bb_upper', 'bb_lower', 'vwap']
        for col in other_key:
            if col in data_with_indicators.columns:
                print(f"  - {col}")
        
        print(f"\nCache directory: {CACHE_DIR}")
        print("Ready for trading strategy optimization!")
        
    except Exception as e:
        print(f"Error during data preparation: {e}")
        import trace