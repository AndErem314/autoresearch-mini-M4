# Autoresearch Trading Adaptation

Adaptation of autoresearch-mlx for BTC/USDT trading strategy optimization using Ichimoku Cloud and other technical indicators.

## Project Goal

Use autonomous AI research loops to find optimal trading strategy configurations for BTC/USDT 4-hour chart data (Nov 2021 - Mar 2024).

## Key Features

1. **Ichimoku Cloud Integration** - Complete Ichimoku indicator calculation with all components:
   - Tenkan-sen (Conversion Line)
   - Kijun-sen (Base Line) 
   - Senkou Span A & B (Leading Spans)
   - Chikou Span (Lagging Span)
   - Cloud status and cross signals

2. **Comprehensive Indicator Suite** - 40+ technical indicators including:
   - Moving Averages (SMA, EMA)
   - Momentum (RSI, MACD)
   - Volatility (Bollinger Bands)
   - Volume (VWAP)
   - Price-based features

3. **Fixed-Time Backtesting** - 5-minute backtest budget per experiment
4. **Autonomous Optimization** - AI agents explore parameter spaces
5. **Keep/Revert Logic** - Only profitable strategies are kept
6. **Mac Mini M4 Optimized** - Apple Silicon native implementation

## Data Pipeline

### Time Periods
- **Training**: Nov 2021 - Nov 2023 (2 years)
- **Validation**: Nov 2023 - Mar 2024 (4 months)
- **Testing**: Mar 2024 - Apr 2024 (1 month)

### Data Source
- **Symbol**: BTCUSDT (Bitcoin/Tether)
- **Interval**: 4-hour charts
- **Source**: Binance API via `python-binance`
- **Cache**: Local cache at `~/.cache/autoresearch-trading/`
- **Advantages**: Real crypto data, no rate limits for historical data, more reliable than Yahoo Finance for crypto

### Indicators Calculated

#### Ichimoku Cloud (Primary Focus)
- `ichimoku_tenkan` - Conversion Line (9-period)
- `ichimoku_kijun` - Base Line (26-period)
- `ichimoku_senkou_a` - Leading Span A
- `ichimoku_senkou_b` - Leading Span B
- `ichimoku_chikou` - Lagging Span
- `ichimoku_cloud_top/bottom` - Cloud boundaries
- `ichimoku_price_above/below/in_cloud` - Cloud position
- `ichimoku_golden/death_cross` - Tenkan/Kijun crosses

#### Supporting Indicators
- **Trend**: SMA(20,50,200), EMA(12,26)
- **Momentum**: RSI(7,14,21), MACD
- **Volatility**: Bollinger Bands(20,2)
- **Volume**: VWAP(20)
- **Price**: Returns, volatility, support/resistance levels

## Setup

### 1. Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements_trading.txt

# Or using uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv pip install -r requirements_trading.txt
```

### 2. Prepare Data
```bash
# Full data preparation (Nov 2021 - Mar 2024)
python prepare_trading.py

# Test mode (small dataset)
python prepare_trading.py --test

# Update with latest data
python prepare_trading.py --update
```

### 3. Test Pipeline
```bash
python test_data_pipeline.py
```

## Project Structure

```
autoresearch-mini-M4/
├── prepare_trading.py          # Main data preparation
├── requirements_trading.txt    # Trading dependencies
├── test_data_pipeline.py       # Pipeline testing
├── README_TRADING.md           # This file
├── strategy.py                 # Trading strategy (TO BE CREATED)
├── backtest.py                 # Backtesting engine (TO BE CREATED)
├── program_trading.md          # Trading agent instructions (TO BE CREATED)
└── results_trading.tsv         # Trading experiment results (TO BE CREATED)
```

## Next Steps

1. **Create Backtesting Engine** (`backtest.py`)
   - Fixed-time backtest loop
   - Trading metrics calculation (Sharpe, profit factor, etc.)
   - Position management and fee calculation

2. **Create Strategy Template** (`strategy.py`)
   - Parameterized trading rules
   - Indicator combination logic
   - Signal generation

3. **Create Trading Program** (`program_trading.md`)
   - AI agent instructions for trading optimization
   - Parameter search space definition
   - Evaluation criteria

4. **Integrate with Autoresearch Loop**
   - Adapt keep/revert logic for trading
   - Results logging and analysis
   - Overnight optimization runs

## Trading Parameters to Optimize

### Ichimoku Parameters
- Tenkan period (default: 9)
- Kijun period (default: 26)
- Senkou B period (default: 52)
- Shift periods (default: 26)

### Entry/Exit Rules
- Cloud position requirements
- Tenkan/Kijun cross conditions
- Chikou span position
- Support/resistance levels

### Risk Management
- Position sizing (default: 10%)
- Stop loss levels
- Take profit targets
- Maximum drawdown limits

## Evaluation Metrics

### Primary Objectives (choose one)
1. **Sharpe Ratio** - Risk-adjusted returns
2. **Profit Factor** - Gross profit / gross loss  
3. **Sortino Ratio** - Downside risk-adjusted returns
4. **Calmar Ratio** - Returns vs max drawdown

### Constraints
- Maximum drawdown < 20%
- Win rate > 45%
- Number of trades > 10 (avoid overfitting)
- Positive expectancy

## Mac Mini M4 Advantages

1. **Unified Memory** - Handle large datasets without GPU limits
2. **Energy Efficiency** - 24/7 optimization loops
3. **Local Privacy** - Trading strategies stay on your machine
4. **MLX Optimization** - Native Apple Silicon performance

## License

MIT - See [LICENSE](LICENSE) file.