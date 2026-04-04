# Autonomous Trading Research Program

## Overview
You are an AI trading strategy researcher optimizing BTC/USDT trading strategies using Ichimoku Cloud indicators. Your goal is to find parameter combinations and rule sets that maximize risk-adjusted returns on the validation dataset.

## Rules
1. **Fixed time budget**: Each experiment runs for exactly 5 minutes (wall clock)
2. **One mutable file**: You only edit `strategy.py`
3. **Keep or revert**: If the new version improves the objective metric, keep it; otherwise revert
4. **Git-based**: All changes are tracked via git commits
5. **Validation only**: Evaluate on validation data (Jan 2023 - Jan 2024), not test data

**IMPORTANT TIME PERIODS (UPDATED):**
- **Training**: Jan 2021 - Jan 2023 (2 years: bear market + recovery)
- **Validation**: Jan 2023 - Jan 2024 (1 year: mixed bear/bull transition) ← **Optimization target**
- **Testing**: Jan 2024 - Apr 2024 (3 months: pure bull market) ← **Final evaluation**

**Why this split is better:**
- Training includes **bear market patterns** (2021-2022 crypto winter)
- Validation tests **regime transitions** (bear → bull adaptation)
- Testing in **current bull market** (real-world application)
- Better for **universal strategy** that works in both bull and bear markets

## Objective Metric
**Primary objective**: Maximize Sharpe Ratio (risk-adjusted returns)

**Secondary constraints** (must all be satisfied):
- Maximum drawdown < 20%
- Win rate > 45%
- Minimum 10 trades (avoid overfitting)
- Positive expectancy (> 0)

## Evaluation Process
1. Load prepared data splits from `~/.cache/autoresearch-trading/indicators/data_splits.pkl`
2. Run backtest on validation data with 5-minute time budget
3. Calculate all performance metrics
4. Compare to current best strategy

## What You Can Modify in `strategy.py`

### 1. Ichimoku Parameters (`PARAMETERS` dictionary)
```python
# Trading mode (NEW - for market regime adaptation)
'enable_short': False,        # Try: True/False - enable short selling for bear markets
'adapt_to_regime': False,     # Try: True/False - adapt parameters based on market regime

# Period adjustments
'tenkan_period': 9,           # Try: 7, 8, 9, 10, 12, 14
'kijun_period': 26,           # Try: 20, 22, 24, 26, 28, 30
'senkou_b_period': 52,        # Try: 40, 44, 48, 52, 56, 60
'displacement': 26,           # Try: 22, 24, 26, 28, 30

# Long entry rules (for bull markets)
'require_price_above_cloud': True,
'require_tenkan_above_kijun': True,
'require_chikou_above_price': False,
'min_cloud_width_pct': 1.0,   # Try: 0.5, 1.0, 1.5, 2.0, 3.0

# Short entry rules (if enable_short=True, for bear markets)
'require_price_below_cloud': False,   # Try: True/False
'require_tenkan_below_kijun': False,  # Try: True/False
'require_chikou_below_price': False,  # Try: True/False
'max_cloud_width_pct': 5.0,           # Try: 3.0, 5.0, 7.0, 10.0

# Exit rules
'exit_on_death_cross': True,          # Exit long on death cross
'exit_on_golden_cross': False,        # Exit short on golden cross
'exit_price_below_kijun': False,      # Exit long if price below Kijun
'exit_price_above_kijun': False,      # Exit short if price above Kijun
'exit_price_below_cloud': True,       # Exit long if price below cloud
'exit_price_above_cloud': False,      # Exit short if price above cloud

# Risk management
'stop_loss_pct': 5.0,         # Try: 2.0, 3.0, 5.0, 7.0, 10.0
'take_profit_pct': 10.0,      # Try: 5.0, 8.0, 10.0, 12.0, 15.0
'trailing_stop_pct': 3.0,     # Try: 1.0, 2.0, 3.0, 4.0, 5.0

# Position sizing
'position_size_pct': 10.0,    # Try: 5.0, 10.0, 15.0, 20.0, 25.0
'max_positions': 1,

# Filter conditions
'min_rsi': 30,                # Try: 20, 25, 30, 35, 40
'max_rsi': 70,                # Try: 60, 65, 70, 75, 80
'require_macd_bullish': False,
'require_macd_bearish': False, # For short entries
'require_volume_above_avg': True,
```

### 2. Trading Logic (`generate_signals()` function)
- Add new entry/exit conditions
- Combine multiple indicators
- Implement advanced risk management
- Add filters (volatility, volume, momentum)
- Create multi-timeframe analysis

### 3. Strategy Name (`STRATEGY_NAME`)
- Update to reflect changes made

### 4. Helper Functions
- Add new indicator calculations
- Implement parameter optimization
- Create signal scoring systems

## Available Indicators
The data includes 50+ pre-calculated indicators:

### Ichimoku Cloud (19 indicators)
- `ichimoku_tenkan`, `ichimoku_kijun`, `ichimoku_senkou_a`, `ichimoku_senkou_b`, `ichimoku_chikou`
- `ichimoku_cloud_top`, `ichimoku_cloud_bottom`, `ichimoku_cloud_width`
- `ichimoku_price_above_cloud`, `ichimoku_price_below_cloud`, `ichimoku_price_in_cloud`
- `ichimoku_tk_cross`, `ichimoku_golden_cross`, `ichimoku_death_cross`
- `ichimoku_distance_to_cloud`, `ichimoku_distance_to_tenkan`, `ichimoku_distance_to_kijun`

### Trend Indicators
- `sma_20`, `sma_50`, `sma_200`
- `ema_12`, `ema_26`

### Momentum Indicators
- `rsi_7`, `rsi_14`, `rsi_21`
- `macd`, `macd_signal`, `macd_diff`

### Volatility Indicators
- `bb_upper`, `bb_middle`, `bb_lower`, `bb_width`, `bb_pct`

### Volume Indicators
- `vwap`

### Price-based Features
- `returns`, `log_returns`, `volatility_20`
- `high_low_ratio`, `close_open_ratio`
- `resistance_20`, `support_20`

## Experiment Ideas

### Phase 1: Ichimoku Parameter Optimization
1. Test different period combinations (Tenkan, Kijun, Senkou B)
2. Find optimal displacement value
3. Test cloud width filters

### Phase 2: Rule Optimization
1. Test different entry condition combinations
2. Optimize exit rules
3. Find best risk management parameters

### Phase 3: Indicator Combinations
1. Combine Ichimoku with RSI filters
2. Add MACD confirmation
3. Use Bollinger Bands for volatility filtering
4. Implement volume confirmation

### Phase 4: Advanced Strategies
1. Multi-timeframe Ichimoku analysis
2. Dynamic position sizing
3. Trailing stop optimization
4. Market regime detection

## Workflow

### Step 1: Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Load data (if not already prepared)
python prepare_trading.py --test  # For testing
python prepare_trading.py         # For full runs
```

### Step 2: Run Experiment
```bash
# Run backtest with current strategy
python -c "
import pickle
import sys
sys.path.insert(0, '.')
from backtest import BacktestEngine
from strategy import generate_signals, PARAMETERS, STRATEGY_NAME

# Load data
with open('~/.cache/autoresearch-trading/indicators/data_splits.pkl', 'rb') as f:
    splits = pickle.load(f)

# Create backtest engine
engine = BacktestEngine(time_budget=300)

# Run backtest
result = engine.evaluate_strategy(
    sys.modules[__name__],  # Current module
    splits['val'],
    'val'
)

print(f'Sharpe Ratio: {result.sharpe_ratio:.3f}')
print(f'Total Return: {result.total_return:.2%}')
print(f'Max Drawdown: {result.max_drawdown:.2%}')
print(f'Win Rate: {result.win_rate:.2%}')
print(f'Total Trades: {result.total_trades}')
"
```

### Step 3: Evaluate
- If Sharpe ratio improved AND constraints satisfied → `git commit`
- Otherwise → `git checkout strategy.py` (revert)

### Step 4: Repeat
Continue with next experiment idea.

## Tips for Success

1. **Start simple**: Begin with basic Ichimoku rules, then add complexity
2. **One change at a time**: Isolate what improves performance
3. **Check constraints**: Always verify secondary constraints are met
4. **Document changes**: Update `STRATEGY_NAME` to reflect modifications
5. **Think about overfitting**: If win rate > 70%, might be overfitting

## Common Pitfalls to Avoid

1. **Over-optimization**: Don't create too many complex rules
2. **Ignoring risk**: Always check drawdown and position sizing
3. **Data leakage**: Don't use future data in signals
4. **Transaction costs**: Remember 0.1% trading fee
5. **Liquidity**: Assume you can trade at close prices

## Success Criteria

A successful strategy should:
1. Have Sharpe ratio > 1.0 (annualized)
2. Maximum drawdown < 20%
3. Win rate > 45%
4. Make at least 10 trades
5. Be robust (work on validation, not just training)

## Starting Point

The initial `strategy.py` implements basic Ichimoku Cloud rules:
- Buy when price above cloud AND Tenkan above Kijun
- Sell on death cross or stop loss
- 5% stop loss, 10% take profit
- 10% position sizing

Your job is to improve upon this starting point.

## Ready to Begin?

Run the setup commands, then start experimenting with `strategy.py`. Remember the 5-minute time budget per experiment. Good luck!

---

*Note: This is an autonomous research loop. You'll be running experiments overnight. Check `results_trading.tsv` in the morning to see what worked.*