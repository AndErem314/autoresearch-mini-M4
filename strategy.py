"""
Trading strategy template with Ichimoku Cloud indicators.
This file is edited by the AI agent during optimization.

The agent should modify:
1. PARAMETERS dictionary - Ichimoku and other indicator parameters
2. generate_signals() function - Trading logic and rules
3. STRATEGY_NAME - Descriptive name for the strategy

Keep the same function signatures but modify the logic.
"""

import numpy as np
from typing import List, Optional
from backtest import TradeAction, TradingSignal, Position

# ---------------------------------------------------------------------------
# Strategy Configuration (AGENT MODIFIES THESE)
# ---------------------------------------------------------------------------

STRATEGY_NAME = "Ichimoku Cloud Optimizer v1.0"

# Ichimoku parameters (agent can modify these)
PARAMETERS = {
    # Ichimoku periods
    'tenkan_period': 9,      # Conversion Line period
    'kijun_period': 26,      # Base Line period
    'senkou_b_period': 52,   # Leading Span B period
    'displacement': 26,      # Shift period
    
    # Entry rules
    'require_price_above_cloud': True,
    'require_tenkan_above_kijun': True,
    'require_chikou_above_price': False,
    'min_cloud_width_pct': 1.0,  # Minimum cloud width as % of price
    
    # Exit rules
    'exit_on_death_cross': True,
    'exit_price_below_kijun': False,
    'exit_price_below_cloud': True,
    
    # Risk management
    'stop_loss_pct': 5.0,    # 5% stop loss
    'take_profit_pct': 10.0, # 10% take profit
    'trailing_stop_pct': 3.0, # 3% trailing stop
    
    # Position sizing
    'position_size_pct': 10.0,  # 10% of capital per trade
    'max_positions': 1,
    
    # Filter conditions
    'min_rsi': 30,           # Minimum RSI for buy
    'max_rsi': 70,           # Maximum RSI for buy
    'require_macd_bullish': False,
    'require_volume_above_avg': True,
}

# ---------------------------------------------------------------------------
# Strategy Logic (AGENT MODIFIES THIS FUNCTION)
# ---------------------------------------------------------------------------

def generate_signals(
    current_row: 'pd.Series',
    positions: List[Position],
    available_capital: float
) -> TradingSignal:
    """
    Generate trading signals based on current market conditions.
    
    Args:
        current_row: Current row of data with all indicators
        positions: List of currently open positions
        available_capital: Available capital for new trades
        
    Returns:
        TradingSignal with action and reason
    """
    # Extract parameters
    params = PARAMETERS
    
    # Check if we have enough data (some indicators need time to calculate)
    if pd.isna(current_row.get('ichimoku_tenkan')) or pd.isna(current_row.get('ichimoku_kijun')):
        return TradingSignal(action=TradeAction.HOLD, reason="Insufficient data")
    
    # -------------------------------------------------------------------
    # ENTRY CONDITIONS (Buy Signal)
    # -------------------------------------------------------------------
    buy_conditions = []
    buy_reasons = []
    
    # 1. Ichimoku Cloud position
    if params['require_price_above_cloud']:
        if current_row.get('ichimoku_price_above_cloud', False):
            buy_conditions.append(True)
            buy_reasons.append("Price above cloud")
        else:
            buy_conditions.append(False)
    
    # 2. Tenkan/Kijun cross
    if params['require_tenkan_above_kijun']:
        if current_row.get('ichimoku_tk_cross', False):
            buy_conditions.append(True)
            buy_reasons.append("Tenkan above Kijun")
        else:
            buy_conditions.append(False)
    
    # 3. Chikou span position
    if params['require_chikou_above_price']:
        chikou = current_row.get('ichimoku_chikou')
        if chikou is not None and chikou > current_row['close']:
            buy_conditions.append(True)
            buy_reasons.append("Chikou above price")
        else:
            buy_conditions.append(False)
    
    # 4. Cloud width filter
    cloud_width = current_row.get('ichimoku_cloud_width', 0)
    min_width = current_row['close'] * (params['min_cloud_width_pct'] / 100)
    if cloud_width > min_width:
        buy_conditions.append(True)
        buy_reasons.append(f"Cloud width OK ({cloud_width:.2f})")
    else:
        buy_conditions.append(False)
    
    # 5. RSI filter
    rsi = current_row.get('rsi_14')
    if rsi is not None:
        if params['min_rsi'] <= rsi <= params['max_rsi']:
            buy_conditions.append(True)
            buy_reasons.append(f"RSI in range ({rsi:.1f})")
        else:
            buy_conditions.append(False)
    
    # 6. MACD filter
    if params['require_macd_bullish']:
        macd = current_row.get('macd', 0)
        macd_signal = current_row.get('macd_signal', 0)
        if macd > macd_signal:
            buy_conditions.append(True)
            buy_reasons.append("MACD bullish")
        else:
            buy_conditions.append(False)
    
    # 7. Volume filter
    if params['require_volume_above_avg']:
        volume_ratio = current_row.get('volume', 0) / current_row.get('volume', 1).rolling(20).mean().iloc[-1]
        if volume_ratio > 1.0:
            buy_conditions.append(True)
            buy_reasons.append("Volume above average")
        else:
            buy_conditions.append(False)
    
    # 8. Golden cross signal
    if current_row.get('ichimoku_golden_cross', False):
        buy_conditions.append(True)
        buy_reasons.append("Golden cross detected")
    
    # -------------------------------------------------------------------
    # EXIT CONDITIONS (Sell Signal)
    # -------------------------------------------------------------------
    sell_conditions = []
    sell_reasons = []
    
    # Check if we have open positions
    if positions:
        position = positions[0]  # Assuming single position
        
        # 1. Death cross exit
        if params['exit_on_death_cross'] and current_row.get('ichimoku_death_cross', False):
            sell_conditions.append(True)
            sell_reasons.append("Death cross exit")
        
        # 2. Price below Kijun exit
        if params['exit_price_below_kijun']:
            if current_row['close'] < current_row.get('ichimoku_kijun', float('inf')):
                sell_conditions.append(True)
                sell_reasons.append("Price below Kijun")
        
        # 3. Price below cloud exit
        if params['exit_price_below_cloud']:
            if current_row.get('ichimoku_price_below_cloud', False):
                sell_conditions.append(True)
                sell_reasons.append("Price below cloud")
        
        # 4. Stop loss check
        stop_loss_price = position.entry_price * (1 - params['stop_loss_pct'] / 100)
        if current_row['close'] <= stop_loss_price:
            sell_conditions.append(True)
            sell_reasons.append(f"Stop loss hit ({params['stop_loss_pct']}%)")
        
        # 5. Take profit check
        take_profit_price = position.entry_price * (1 + params['take_profit_pct'] / 100)
        if current_row['close'] >= take_profit_price:
            sell_conditions.append(True)
            sell_reasons.append(f"Take profit hit ({params['take_profit_pct']}%)")
        
        # 6. Trailing stop (simplified)
        if params['trailing_stop_pct'] > 0:
            # This would need more sophisticated tracking
            pass
    
    # -------------------------------------------------------------------
    # DECISION LOGIC
    # -------------------------------------------------------------------
    
    # If we have open positions, check exit conditions first
    if positions:
        if any(sell_conditions):
            reason = " | ".join(sell_reasons)
            return TradingSignal(action=TradeAction.SELL, reason=reason)
    
    # If no positions and all buy conditions met, enter
    elif not positions and all(buy_conditions):
        reason = " | ".join(buy_reasons)
        return TradingSignal(action=TradeAction.BUY, reason=reason)
    
    # Default: hold
    return TradingSignal(action=TradeAction.HOLD, reason="No clear signal")

# ---------------------------------------------------------------------------
# Helper Functions (AGENT CAN ADD MORE)
# ---------------------------------------------------------------------------

def calculate_ichimoku_parameters(data: 'pd.DataFrame', params: dict) -> 'pd.DataFrame':
    """
    Calculate Ichimoku indicators with custom parameters.
    This allows the agent to test different parameter sets.
    """
    df = data.copy()
    
    # Calculate with custom periods
    tenkan_period = params.get('tenkan_period', 9)
    kijun_period = params.get('kijun_period', 26)
    senkou_b_period = params.get('senkou_b_period', 52)
    displacement = params.get('displacement', 26)
    
    # Tenkan-sen (Conversion Line)
    high_9 = df['high'].rolling(window=tenkan_period).max()
    low_9 = df['low'].rolling(window=tenkan_period).min()
    df['ichimoku_tenkan_custom'] = (high_9 + low_9) / 2
    
    # Kijun-sen (Base Line)
    high_26 = df['high'].rolling(window=kijun_period).max()
    low_26 = df['low'].rolling(window=kijun_period).min()
    df['ichimoku_kijun_custom'] = (high_26 + low_26) / 2
    
    # Senkou Span A (Leading Span A)
    df['ichimoku_senkou_a_custom'] = (
        (df['ichimoku_tenkan_custom'] + df['ichimoku_kijun_custom']) / 2
    ).shift(displacement)
    
    # Senkou Span B (Leading Span B)
    high_52 = df['high'].rolling(window=senkou_b_period).max()
    low_52 = df['low'].rolling(window=senkou_b_period).min()
    df['ichimoku_senkou_b_custom'] = ((high_52 + low_52) / 2).shift(displacement)
    
    # Chikou Span (Lagging Span)
    df['ichimoku_chikou_custom'] = df['close'].shift(-displacement)
    
    return df

def optimize_parameters(data: 'pd.DataFrame') -> dict:
    """
    Example function for parameter optimization.
    The agent can implement grid search or other optimization here.
    """
    # This is a template - agent should implement actual optimization
    best_params = PARAMETERS.copy()
    best_score = 0
    
    # Example: Try different Tenkan periods
    for tenkan in [7, 9, 12, 14]:
        params = PARAMETERS.copy()
        params['tenkan_period'] = tenkan
        
        # Calculate custom indicators
        df_with_custom = calculate_ichimoku_parameters(data, params)
        
        # Evaluate strategy (simplified)
        # In reality, this would run a full backtest
        score = _evaluate_parameter_set(df_with_custom, params)
        
        if score > best_score:
            best_score = score
            best_params = params
    
    return best_params

def _evaluate_parameter_set(df: 'pd.DataFrame', params: dict) -> float:
    """
    Simplified evaluation of parameter set.
    Agent should replace with proper backtest evaluation.
    """
    # Simplified scoring based on Ichimoku signals
    score = 0
    
    # Reward golden crosses
    golden_crosses = df['ichimoku_golden_cross'].sum()
    score += golden_crosses * 10
    
    # Penalize death crosses
    death_crosses = df['ichimoku_death_cross'].sum()
    score -= death_crosses * 10
    
    # Reward time price is above cloud
    above_cloud = df['ichimoku_price_above_cloud'].sum()
    score += above_cloud * 5
    
    return score

# ---------------------------------------------------------------------------
# Required imports (don't remove)
# ---------------------------------------------------------------------------

import pandas as pd

# ---------------------------------------------------------------------------
# Test function
# ---------------------------------------------------------------------------

def test_strategy():
    """Test the strategy logic with sample data."""
    print(f"Testing strategy: {STRATEGY_NAME}")
    print(f"Parameters: {PARAMETERS}")
    
    # Create sample data row
    sample_data = pd.Series({
        'close': 45000.0,
        'high': 45500.0,
        'low': 44500.0,
        'volume': 1000,
        'ichimoku_tenkan': 44800.0,
        'ichimoku_kijun': 44600.0,
        'ichimoku_senkou_a': 44700.0,
        'ichimoku_senkou_b': 44500.0,
        'ichimoku_chikou': 44900.0,
        'ichimoku_price_above_cloud': True,
        'ichimoku_tk_cross': True,
        'ichimoku_golden_cross': True,
        'ichimoku_death_cross': False,
        'rsi_14': 55.0,
        'macd': 100.0,
        'macd_signal': 90.0,
        'volume_20_avg': 800.0
    })
    
    # Test signal generation
    signal = generate_signals(sample_data, [], 10000.0)
    print(f"Signal: {signal.action.value} - {signal.reason}")
    
    return signal

if __name__ == "__main__":
    test_strategy()