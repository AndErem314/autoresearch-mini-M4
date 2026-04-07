"""
Trading strategy template with Ichimoku Cloud indicators.
This file is edited by the AI agent during optimization.

The agent can modify:
1. PARAMETERS dictionary - Ichimoku and other indicator parameters
2. generate_signals() function - Trading logic and rules
3. STRATEGY_NAME - Descriptive name for the strategy

Keep the same function signatures but modify the logic.

Version: v2.0 - Voting System (Option 1)
"""

import numpy as np
import pandas as pd
from typing import List, Optional
from backtest import TradeAction, TradingSignal, Position

# ---------------------------------------------------------------------------
# Strategy Configuration (AGENT MODIFIES THESE)
# ---------------------------------------------------------------------------

STRATEGY_NAME = "Ichimoku Voting System v2.0"

# --- Ichimoku core periods ---
PARAMETERS = {
    # Ichimoku periods
    'tenkan_period': 9,
    'kijun_period': 26,
    'senkou_b_period': 52,
    'displacement': 26,

    # Trading mode
    'enable_short': False,
    'adapt_to_regime': False,

    # --- VOTING SYSTEM: each enabled filter that passes adds +1 to the score. ---
    # When total score >= vote_threshold, a BUY signal is generated.
    #
    # vote_threshold: minimum votes required to enter a long trade.
    #   Range: 1 (enter if ANY single filter passes) to N (all enabled filters must pass).
    #   Recommended starting point: 3 (out of 6-7 enabled filters).
    'vote_threshold': 3,

    # Each filter is controlled by a single boolean:
    #   True  → this filter is counted as one vote (if it passes).
    #   False → filter is ignored (no vote either way).
    'vote_price_above_cloud': True,
    'vote_tenkan_above_kijun': True,
    'vote_chikou_above_price': True,
    'vote_cloud_width': True,
    'vote_rsi': True,
    'vote_macd_bullish': False,
    'vote_volume_above_avg': True,

    # Filter sub-parameters
    'min_cloud_width_pct': 1.0,
    'min_rsi': 30,
    'max_rsi': 70,

    # Short-entry votes (if enable_short=True)
    'vote_price_below_cloud': False,
    'vote_tenkan_below_kijun': False,
    'vote_chikou_below_price': False,
    'vote_macd_bearish': False,
    'max_cloud_width_pct': 5.0,

    # Exit rules (unchanged from v1 — any-one triggers exit)
    'exit_on_death_cross': True,
    'exit_on_golden_cross': False,
    'exit_price_below_kijun': False,
    'exit_price_above_kijun': False,
    'exit_price_below_cloud': True,
    'exit_price_above_cloud': False,

    # Risk management
    'stop_loss_pct': 5.0,
    'take_profit_pct': 10.0,
    'trailing_stop_pct': 3.0,

    # Position sizing
    'position_size_pct': 10.0,
    'max_positions': 1,
}

# ---------------------------------------------------------------------------
# Voting helpers
# ---------------------------------------------------------------------------

def _vote(params: dict, flag_key: str, condition: bool) -> tuple[bool, str]:
    """Evaluate one vote.

    Returns (scored, reason) — if the filter is disabled (flag is False/missing),
    the function returns (False, "") so it contributes nothing.
    If enabled and condition is True → (+1, reason).
    If enabled and condition is False → (0, reason with ✗ marker).
    """
    if not params.get(flag_key, False):
        return False, ""
    if condition:
        return True, f"{flag_key}✓"
    return False, f"{flag_key}✗"


# ---------------------------------------------------------------------------
# Strategy Logic (AGENT MODIFIES THIS FUNCTION)
# ---------------------------------------------------------------------------

def generate_signals(
    current_row: 'pd.Series',
    positions: List[Position],
    available_capital: float
) -> TradingSignal:
    """
    Generate trading signals based on a voting system.

    Each enabled indicator casts a vote (+1 if condition met, 0 if not).
    When the total vote count >= vote_threshold → BUY signal.

    Exit logic remains "any one trigger" — unchanged from v1.
    """
    params = PARAMETERS

    # Not enough data yet
    if pd.isna(current_row.get('ichimoku_tenkan')) or pd.isna(current_row.get('ichimoku_kijun')):
        return TradingSignal(action=TradeAction.HOLD, reason="Insufficient data")

    # -------------------------------------------------------------------
    # ENTRY — VOTING SYSTEM
    # -------------------------------------------------------------------
    score = 0
    reasons = []

    # 1. Price above cloud
    scored, reason = _vote(params, 'vote_price_above_cloud',
                           current_row.get('ichimoku_price_above_cloud', False))
    if reason:
        reasons.append(reason)
    if scored:
        score += 1

    # 2. Tenkan above Kijun
    scored, reason = _vote(params, 'vote_tenkan_above_kijun',
                           current_row.get('ichimoku_tk_cross', False))
    if reason:
        reasons.append(reason)
    if scored:
        score += 1

    # 3. Chikou span above price
    chikou = current_row.get('ichimoku_chikou')
    scored, reason = _vote(params, 'vote_chikou_above_price',
                           chikou is not None and chikou > current_row['close'])
    if reason:
        reasons.append(reason)
    if scored:
        score += 1

    # 4. Cloud width sufficient
    cloud_width = current_row.get('ichimoku_cloud_width', 0)
    min_width = current_row['close'] * (params['min_cloud_width_pct'] / 100)
    scored, reason = _vote(params, 'vote_cloud_width', cloud_width > min_width)
    if reason:
        reasons.append(reason)
    if scored:
        score += 1

    # 5. RSI in acceptable range
    rsi = current_row.get('rsi_14')
    rsi_ok = rsi is not None and params['min_rsi'] <= rsi <= params['max_rsi']
    scored, reason = _vote(params, 'vote_rsi', rsi_ok)
    if reason:
        reasons.append(reason)
    if scored:
        score += 1

    # 6. MACD bullish
    macd = current_row.get('macd', 0)
    macd_signal = current_row.get('macd_signal', 0)
    scored, reason = _vote(params, 'vote_macd_bullish', macd > macd_signal)
    if reason:
        reasons.append(reason)
    if scored:
        score += 1

    # 7. Volume above average (or at least present)
    vol = current_row.get('volume', 0)
    scored, reason = _vote(params, 'vote_volume_above_avg', vol > 0)
    if reason:
        reasons.append(reason)
    if scored:
        score += 1

    # Extra: golden-cross bonus vote (not threshold-gated, just adds flavour)
    if current_row.get('ichimoku_golden_cross', False):
        reasons.append("golden_cross🔥")

    # -------------------------------------------------------------------
    # EXIT (unchanged from v1 — any-one triggers)
    # -------------------------------------------------------------------
    sell_reasons = []
    if positions:
        position = positions[0]

        if params['exit_on_death_cross'] and current_row.get('ichimoku_death_cross', False):
            sell_reasons.append("Death cross exit")

        if params['exit_price_below_kijun']:
            if current_row['close'] < current_row.get('ichimoku_kijun', float('inf')):
                sell_reasons.append("Price below Kijun")

        if params['exit_price_below_cloud']:
            if current_row.get('ichimoku_price_below_cloud', False):
                sell_reasons.append("Price below cloud")

        stop_loss_price = position.entry_price * (1 - params['stop_loss_pct'] / 100)
        if current_row['close'] <= stop_loss_price:
            sell_reasons.append(f"Stop loss hit ({params['stop_loss_pct']}%)")

        take_profit_price = position.entry_price * (1 + params['take_profit_pct'] / 100)
        if current_row['close'] >= take_profit_price:
            sell_reasons.append(f"Take profit hit ({params['take_profit_pct']}%)")

        # Trailing stop placeholder
        if params['trailing_stop_pct'] > 0:
            pass

    # -------------------------------------------------------------------
    # DECISION
    # -------------------------------------------------------------------
    threshold = max(params.get('vote_threshold', 3), 1)

    if positions:
        if sell_reasons:
            return TradingSignal(action=TradeAction.SELL, reason=" | ".join(sell_reasons))
    elif score >= threshold:
        vote_summary = f"Vote score {score}/{len(reasons)} " + "| ".join([r for r in reasons if r])
        return TradingSignal(action=TradeAction.BUY, reason=vote_summary)

    return TradingSignal(action=TradeAction.HOLD, reason=f"Vote score {score}/{threshold}")


# ---------------------------------------------------------------------------
# Helper Functions (AGENT CAN ADD MORE)
# ---------------------------------------------------------------------------

def calculate_ichimoku_parameters(data: 'pd.DataFrame', params: dict) -> 'pd.DataFrame':
    """Calculate Ichimoku indicators with custom parameters."""
    df = data.copy()

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
    """Example function for parameter optimization."""
    best_params = PARAMETERS.copy()
    best_score = 0

    for tenkan in [7, 9, 12, 14]:
        params = PARAMETERS.copy()
        params['tenkan_period'] = tenkan

        df_with_custom = calculate_ichimoku_parameters(data, params)
        score = _evaluate_parameter_set(df_with_custom, params)

        if score > best_score:
            best_score = score
            best_params = params

    return best_params


def _evaluate_parameter_set(df: 'pd.DataFrame', params: dict) -> float:
    """Simplified evaluation of parameter set."""
    score = 0
    score += df['ichimoku_golden_cross'].sum() * 10
    score -= df['ichimoku_death_cross'].sum() * 10
    score += df['ichimoku_price_above_cloud'].sum() * 5
    return score


# ---------------------------------------------------------------------------
# Test function
# ---------------------------------------------------------------------------

def test_strategy():
    """Test the strategy logic with sample data."""
    print(f"Testing strategy: {STRATEGY_NAME}")
    print(f"Parameters: {PARAMETERS}")

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

    signal = generate_signals(sample_data, [], 10000.0)
    print(f"Signal: {signal.action.value} - {signal.reason}")

    return signal

if __name__ == "__main__":
    test_strategy()
