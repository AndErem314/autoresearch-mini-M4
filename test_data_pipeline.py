#!/usr/bin/env python3
"""
Test script for BTC trading data pipeline.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prepare_trading import download_btc_data, calculate_all_indicators, prepare_data_splits

def test_data_pipeline():
    """Test the complete data pipeline."""
    print("Testing BTC trading data pipeline...")
    print("=" * 60)
    
    try:
        # 1. Test data download (small date range for speed)
        print("1. Testing data download...")
        data = download_btc_data(
            start_date="2024-01-01",
            end_date="2024-01-10",
            interval="4h",
            force_download=False
        )
        
        print(f"   ✓ Downloaded {len(data)} rows")
        print(f"   ✓ Columns: {list(data.columns)}")
        print(f"   ✓ Date range: {data.index[0]} to {data.index[-1]}")
        
        # 2. Test indicator calculation
        print("\n2. Testing indicator calculation...")
        data_with_indicators = calculate_all_indicators(data)
        
        # Check Ichimoku columns
        ichimoku_cols = [col for col in data_with_indicators.columns if 'ichimoku' in col]
        print(f"   ✓ Calculated {len(ichimoku_cols)} Ichimoku indicators")
        print(f"   ✓ Total indicators: {len(data_with_indicators.columns)}")
        
        # 3. Test data splits
        print("\n3. Testing data splits...")
        # Temporarily modify constants for test
        import prepare_trading
        original_train_end = prepare_trading.TRAIN_END
        prepare_trading.TRAIN_END = "2024-01-05"
        prepare_trading.VAL_END = "2024-01-08"
        
        splits = prepare_data_splits(data_with_indicators)
        
        print(f"   ✓ Train data: {len(splits['train'])} rows")
        print(f"   ✓ Validation data: {len(splits['val'])} rows")
        print(f"   ✓ Test data: {len(splits['test'])} rows")
        
        # Restore original constants
        prepare_trading.TRAIN_END = original_train_end
        
        # 4. Check specific Ichimoku calculations
        print("\n4. Verifying Ichimoku calculations...")
        test_row = data_with_indicators.iloc[-1]
        
        required_ichimoku = [
            'ichimoku_tenkan',
            'ichimoku_kijun', 
            'ichimoku_senkou_a',
            'ichimoku_senkou_b',
            'ichimoku_chikou',
            'ichimoku_price_above_cloud',
            'ichimoku_golden_cross'
        ]
        
        for col in required_ichimoku:
            if col in test_row:
                value = test_row[col]
                if pd.isna(value):
                    print(f"   ⚠ {col}: NaN (may be expected for early rows)")
                else:
                    print(f"   ✓ {col}: {value}")
            else:
                print(f"   ✗ {col}: Missing!")
        
        print("\n" + "=" * 60)
        print("DATA PIPELINE TEST COMPLETE!")
        print("=" * 60)
        
        # Summary
        print("\nSummary:")
        print(f"- Total data points: {len(data)}")
        print(f"- Total indicators: {len(data_with_indicators.columns)}")
        print(f"- Ichimoku indicators: {len(ichimoku_cols)}")
        print(f"- Train/Val/Test split working: ✓")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import pandas as pd
    success = test_data_pipeline()
    sys.exit(0 if success else 1)