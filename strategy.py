"""
Trading strategy template with Ichimoku Cloud indicators.
This file is edited by the AI agent during optimization.

The agent can modify:
1. PARAMETERS dictionary - Ichimoku and other indicator parameters
2. generate_signals() function - Trading logic and rules
3. STRATEGY_NAME - Descriptive name for the strategy

Keep the same function signatures but modify the logic.

Version: v3.0 - Trend + Pullback Entry (Option 2)
"""

import numpy as np
import pandas as pd
from typing import List, Optional
from backtest import TradeAction, TradingSignal, Position

# ---------------------------------------------------------------------------
# Strategy Configuration (AGENT MODIFIES THESE)
# ---------------------------------------------------------------------------

STRATEGY_NAME = "Trend Pullback Entry v3.0"

PARAMETERS = {
    # Ichimoku periods
    'tenkan_period': 9,
    'kijun_period': 26,
    'senkou_b_period': 52,
    'displacement': 26,

    # Trading mode
    'enable_short': False,
    'adapt_to_regime': False,

    # --- TREND CONFIRMATION (must be True before considering entries) ---
    'require_uptrend': True,         # Tenkan > Kijun
    'require_price_above_cloud': True,  # Price above Ichimoku cloud
    'require_cloud_bullish': True,   # Senkou A > Senkou B (cloud is green/bullish)

    # --- PULLBACK ENTRY (wait for dip then bounce) ---
    # The strategy tracks RSI. Entry is triggered when:
    #   1. RSI dips below rsi_pullback_threshold (RSI is oversold relative to the trend)
    #   2. THEN RSI bounces back above rsi_bounce_level (momentum recovering)
    #   3. Trend is still confirmed (requirements above still met)
    'rsi_pullback_threshold': 40,    # RSI must dip below this to register a pullback
    'rsi_bounce_level': 50,          # RSI must cross back above this to trigger entry
    'enable_pullback_entry': True,   # Set False to just enter on trend (no pullback)

    # Fallback: simple trend-following entry (no pullback required)
    # Used only when pullback_entry is disabled OR when pullback never materializes
    'enable_trend_entry': False,     # Enter immediately when uptrend is confirmed

    # --- EXIT RULES ---
    'exit_on_death_cross': True,     # Tenkan crosses below Kijun
    'exit_price_below_kijun': False, # Price closes below Kijun
    'exit_price_below_cloud': True,  # Price closes below cloud
    'exit_rsi_overbought': False,    # Exit when RSI exceeds level
    'exit_rsi_level': 75,            # RSI overbought exit threshold

    # --- RISK MANAGEMENT ---
    'stop_loss_pct': 5.0,
    'take_profit_pct': 10.0,
    'trailing_stop_pct': 3.0,

    # --- POSITION SIZING ---
    'position_size_pct': 10.0,
    'max_positions': 1,

    # --- FILTERS (optional additional confirmation) ---
    'require_volume_above_avg': False,
    'min_cloud_width_pct': 1.0,
}

# ---------------------------------------------------------------------------
# Internal state tracker (module-level, persists across rows in one backtest)
# ---------------------------------------------------------------------------
# Tracks whether RSI has recently dipped below the pullback threshold.
# Reset between backtest runs by optimizer.
_strategy_state = {}

def reset_state():
    """Reset internal state. Called before each backtest run."""
    global _strategy_state
    _strategy_state = {
        'rsi_dipped_below_threshold': False,  # True once RSI dips below threshold
    }

# ---------------------------------------------------------------------------
# Strategy Logic
# ---------------------------------------------------------------------------

def generate_signals(
    current_row: 'pd.Series',
    positions: List[Position],
    available_capital: float
) -> TradingSignal:
    """
    Trend + Pullback Entry strategy.

    Phase 1: Confirm uptrend (price > cloud, Tenkan > Kijun, bullish cloud)
    Phase 2: Wait for RSI pullback — dip below threshold, then bounce above recovery
    Phase 3: Enter on the bounce, not the cross
    Exit: death cross, price below cloud/kijun, or stop-loss/take-profit
    """
    global _strategy_state
    params = PARAMETERS
    rsi = current_row.get('rsi_14')

    # Not enough data
    if pd.isna(current_row.get('ichimoku_tenkan')) or pd.isna(current_row.get('ichimoku_kijun')):
        return TradingSignal(action=TradeAction.HOLD, reason="Insufficient data")

    # -------------------------------------------------------------------
    # TREND CONFIRMATION
    # -------------------------------------------------------------------
    tenkan = current_row.get('ichimoku_tenkan', 0)
    kijun = current_row.get('ichimoku_kijun', 0)
    price_above_cloud = current_row.get('ichimoku_price_above_cloud', False)
    close = current_row['close']

    # Trend checks
    tenkan_above_kijun = tenkan > kijun

    senkou_a = current_row.get('ichimoku_senkou_a', 0)
    senkou_b = current_row.get('ichimoku_senkou_b', 0)
    cloud_bullish = senkou_a > senkou_b if pd.notna(senkou_a) and pd.notna(senkou_b) else True

    # Cloud width filter
    cloud_width = current_row.get('ichimoku_cloud_width', 0)
    min_width = close * (params['min_cloud_width_pct'] / 100)
    cloud_width_ok = cloud_width > min_width

    # All trend conditions met?
    trend_confirmed = True
    trend_reasons = []

    if params['require_uptrend']:
        if not tenkan_above_kijun:
            trend_confirmed = False
        else:
            trend_reasons.append("Tenkan>Kijun")

    if params['require_price_above_cloud']:
        if not price_above_cloud:
            trend_confirmed = False
        else:
            trend_reasons.append("Price>Cloud")

    if params['require_cloud_bullish']:
        if not cloud_bullish:
            trend_confirmed = False
        else:
            trend_reasons.append("Cloud bullish")

    if not cloud_width_ok:
        # Non-fatal for trend but noted
        pass

    # -------------------------------------------------------------------
    # PULLBACK LOGIC
    # -------------------------------------------------------------------
    pullback_ready = False

    if params['enable_pullback_entry'] and rsi is not None and not pd.isna(rsi):
        dip_threshold = params['rsi_pullback_threshold']
        bounce_level = params['rsi_bounce_level']

        # If RSI is currently below threshold — we've seen the dip
        if rsi < dip_threshold:
            _strategy_state['rsi_dipped_below_threshold'] = True

        # If we recorded a dip AND RSI has now bounced back above recovery
        if _strategy_state['rsi_dipped_below_threshold'] and rsi > bounce_level:
            pullback_ready = True
            # Reset so we don't re-enter on the same pullback
            _strategy_state['rsi_dipped_below_threshold'] = False

        # Reset state if trend is broken (pullback context is gone)
        if not trend_confirmed:
            _strategy_state['rsi_dipped_below_threshold'] = False

    # -------------------------------------------------------------------
    # ENTRY DECISIONS
    # -------------------------------------------------------------------
    entry_signal = False
    entry_reason = ""

    if trend_confirmed:
        if pullback_ready:
            entry_signal = True
            entry_reason = f"Pullback entry | RSI {rsi:.1f} bounced {params['rsi_pullback_threshold']}→{params['rsi_bounce_level']} | " + " ".join(trend_reasons)

        elif params['enable_trend_entry']:
            entry_signal = True
            entry_reason = "Trend entry (no pullback) | " + " ".join(trend_reasons)

    # -------------------------------------------------------------------
    # EXIT LOGIC (any-one triggers)
    # -------------------------------------------------------------------
    sell_reasons = []
    if positions:
        position = positions[0]

        # Death cross
        if params['exit_on_death_cross'] and current_row.get('ichimoku_death_cross', False):
            sell_reasons.append("Death cross")

        # Price below Kijun
        if params['exit_price_below_kijun'] and close < kijun:
            sell_reasons.append("Price below Kijun")

        # Price below cloud
        if params['exit_price_below_cloud'] and current_row.get('ichimoku_price_below_cloud', False):
            sell_reasons.append("Price below cloud")

        # RSI overbought exit
        if params['exit_rsi_overbought'] and rsi is not None and rsi > params['exit_rsi_level']:
            sell_reasons.append(f"RSI overbought ({rsi:.1f})")

        # Stop loss
        stop_loss_price = position.entry_price * (1 - params['stop_loss_pct'] / 100)
        if close <= stop_loss_price:
            sell_reasons.append(f"Stop loss ({params['stop_loss_pct']}%)")

        # Take profit
        take_profit_price = position.entry_price * (1 + params['take_profit_pct'] / 100)
        if close >= take_profit_price:
            sell_reasons.append(f"Take profit ({params['take_profit_pct']}%)")

    # -------------------------------------------------------------------
    # FINAL DECISION
    # -------------------------------------------------------------------
    if positions:
        if sell_reasons:
            return TradingSignal(action=TradeAction.SELL, reason=" | ".join(sell_reasons))
    elif entry_signal:
        return TradingSignal(action=TradeAction.BUY, reason=entry_reason)

    return TradingSignal(action=TradeAction.HOLD, reason="No signal")


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

    high_t = df['high'].rolling(window=tenkan_period).max()
    low_t = df['low'].rolling(window=tenkan_period).min()
    df['ichimoku_tenkan_custom'] = (high_t + low_t) / 2

    high_k = df['high'].rolling(window=kijun_period).max()
    low_k = df['low'].rolling(window=kijun_period).min()
    df['ichimoku_kijun_custom'] = (high_k + low_k) / 2

    df['ichimoku_senkou_a_custom'] = (
        (df['ichimoku_tenkan_custom'] + df['ichimoku_kijun_custom']) / 2
    ).shift(displacement)

    high_s = df['high'].rolling(window=senkou_b_period).max()
    low_s = df['low'].rolling(window=senkou_b_period).min()
    df['ichimoku_senkou_b_custom'] = ((high_s + low_s) / 2).shift(displacement)

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

    # Simulate a pullback scenario over multiple calls
    print("\n--- Simulating pullback scenario ---")

    test_cases = [
        # (tenkan, kijun, price_above_cloud, senkou_a, senkou_b, rsi, death_cross, price_below_cloud)
        {"i_tenkan": 44800, "i_kijun": 44600, "i_pac": True,  "i_senkou_a": 44700, "i_senkou_b": 44500, "rsi": 55.0, "i_dc": False, "i_pbc": False},  # Trend, RSI normal
        {"i_tenkan": 44800, "i_kijun": 44600, "i_pac": True,  "i_senkou_a": 44700, "i_senkou_b": 44500, "rsi": 35.0, "i_dc": False, "i_pbc": False},  # RSI dips
        {"i_tenkan": 44800, "i_kijun": 44600, "i_pac": True,  "i_senkou_a": 44700, "i_senkou_b": 44500, "rsi": 48.0, "i_dc": False, "i_pbc": False},  # RSI bouncing but not yet above 50
        {"i_tenkan": 44800, "i_kijun": 44600, "i_pac": True,  "i_senkou_a": 44700, "i_senkou_b": 44500, "rsi": 52.0, "i_dc": False, "i_pbc": False},  # RSI bounced above 50 → entry
    ]

    reset_state()  # Ensure clean state

    for i, tc in enumerate(test_cases):
        row = pd.Series({
            'close': 45000.0,
            'high': 45500.0,
            'low': 44500.0,
            'volume': 1000,
            'ichimoku_tenkan': tc["i_tenkan"],
            'ichimoku_kijun': tc["i_kijun"],
            'ichimoku_senkou_a': tc["i_senkou_a"],
            'ichimoku_senkou_b': tc["i_senkou_b"],
            'ichimoku_price_above_cloud': tc["i_pac"],
            'ichimoku_price_below_cloud': tc["i_pbc"],
            'ichimoku_death_cross': tc["i_dc"],
            'ichimoku_tk_cross': tc["i_tenkan"] > tc["i_kijun"],
            'ichimoku_cloud_width': 200.0,
            'rsi_14': tc["rsi"],
            'macd': 100.0,
            'macd_signal': 90.0,
        })
        signal = generate_signals(row, [], 10000.0)
        state_str = f"dipped={_strategy_state['rsi_dipped_below_threshold']}"
        print(f"Bar {i}: RSI={tc['rsi']:.1f} → {signal.action.value} ({signal.reason}) | State: {state_str}")

    reset_state()  # Clean up after test

if __name__ == "__main__":
    test_strategy()
