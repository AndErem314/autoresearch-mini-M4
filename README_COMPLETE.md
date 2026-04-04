# Complete Trading Autoresearch Infrastructure

## 🚀 What's Included

This repository now contains a **complete trading strategy optimization system** for BTC/USDT using Ichimoku Cloud indicators, ready for autonomous AI research on your Mac Mini M4.

## 📁 Project Structure

```
autoresearch-mini-M4/
├── 📊 DATA PIPELINE
│   ├── prepare_trading.py          # BTC data download & indicator calculation
│   ├── requirements_trading.txt    # Python dependencies
│   └── test_data_pipeline.py       # Pipeline testing
│
├── ⚙️ BACKTESTING ENGINE
│   ├── backtest.py                 # Fixed-time backtesting with metrics
│   ├── strategy.py                 # Trading strategy template (AGENT EDITS)
│   └── results_trading.tsv         # Experiment results log
│
├── 🤖 AUTONOMOUS RESEARCH
│   └── program_trading.md          # AI agent instructions
│
├── 🛠️ SETUP & UTILITIES
│   ├── setup_trading.sh            # One-click setup script
│   ├── README_COMPLETE.md          # This file
│   ├── README_TRADING.md           # Detailed trading documentation
│   └── .gitignore                  # Git exclusions
│
└── 📚 ORIGINAL MLX CODE (preserved)
    ├── prepare.py                  # Original text data prep
    ├── train.py                    # Original ML training
    ├── program.md                  # Original AI program
    └── README.md                   # Original documentation
```

## 🎯 Core Features

### 1. **Complete Ichimoku Cloud Implementation**
- All 5 Ichimoku components calculated
- 19 Ichimoku-derived indicators
- Customizable periods (Tenkan, Kijun, Senkou B)
- Cloud position, crosses, and distance metrics

### 2. **Comprehensive Indicator Suite** (50+ indicators)
- Trend: SMA, EMA, MACD
- Momentum: RSI (7, 14, 21)
- Volatility: Bollinger Bands
- Volume: VWAP
- Price: Returns, support/resistance

### 3. **Fixed-Time Backtesting Engine**
- 5-minute evaluation budget per experiment
- 15+ performance metrics (Sharpe, Sortino, drawdown, etc.)
- Realistic trading fees (0.1%) and position sizing
- Keep/revert logic based on performance

### 4. **Autonomous Research Ready**
- AI agent instructions in `program_trading.md`
- Parameter optimization framework
- Git-based experiment tracking
- Results logging in TSV format

## 🚀 Quick Start

### Step 1: Clone & Setup
```bash
# Clone your repository
git clone https://github.com/AndErem314/autoresearch-mini-M4.git
cd autoresearch-mini-M4
git checkout trading-adaptation

# Run setup script
chmod +x setup_trading.sh
./setup_trading.sh
```

### Step 2: Prepare Data
```bash
# Activate virtual environment
source venv/bin/activate

# Test with small dataset
python prepare_trading.py --test

# Prepare full dataset (Nov 2021 - Mar 2024)
python prepare_trading.py
```

### Step 3: Test Strategy
```bash
# Test the default Ichimoku strategy
python -c "
import sys
sys.path.insert(0, '.')
from strategy import test_strategy
test_strategy()
"
```

### Step 4: Start Autonomous Research
Point your AI agent (Claude Code, etc.) at `program_trading.md` and let it run experiments overnight.

## 📈 Trading Strategy Optimization

### What the AI Agent Can Modify:

#### **Parameters** (in `strategy.py`):
```python
PARAMETERS = {
    'tenkan_period': 9,      # Try: 7-14
    'kijun_period': 26,      # Try: 20-30
    'senkou_b_period': 52,   # Try: 40-60
    'require_price_above_cloud': True,
    'stop_loss_pct': 5.0,    # Try: 2-10%
    'take_profit_pct': 10.0, # Try: 5-15%
    # ... 15+ more parameters
}
```

#### **Trading Logic** (in `generate_signals()`):
- Add/remove entry conditions
- Combine multiple indicators
- Implement advanced risk management
- Create custom filters

#### **Evaluation Metrics**:
- **Primary**: Maximize Sharpe Ratio
- **Constraints**: Max drawdown < 20%, Win rate > 45%, Min 10 trades

## 🏗️ Architecture

### Data Flow:
```
BTC 4h Data (Yahoo Finance)
        ↓
[prepare_trading.py] → Download & calculate 50+ indicators
        ↓
Train/Val/Test Splits (Nov 2021 - Mar 2024)
        ↓
[strategy.py] → Generate trading signals
        ↓
[backtest.py] → 5-minute fixed-time evaluation
        ↓
Performance Metrics → Keep/Revert Decision
```

### Experiment Loop:
1. AI agent edits `strategy.py`
2. Run 5-minute backtest on validation data
3. Calculate Sharpe ratio and constraints
4. If improved: `git commit`
5. If not: `git checkout strategy.py` (revert)
6. Repeat

## 🍎 Mac Mini M4 Advantages

1. **Unified Memory** - Handle large datasets without GPU limits
2. **Energy Efficient** - Run 24/7 optimization loops
3. **Local & Private** - Your strategies stay on your machine
4. **MLX Ready** - Can integrate Apple's ML framework later

## 📊 Data Specifications

### Time Periods:
- **Training**: Nov 2021 - Nov 2023 (2 years)
- **Validation**: Nov 2023 - Mar 2024 (4 months) ← **Optimization target**
- **Testing**: Mar 2024 - Apr 2024 (1 month) ← **Final evaluation**

### Data Source:
- **Symbol**: BTC-USD
- **Interval**: 4-hour charts
- **Cache**: `~/.cache/autoresearch-trading/`
- **Updates**: Run `python prepare_trading.py --update`

## 🔧 Technical Details

### Dependencies:
- `yfinance` - BTC data download
- `ta` - Technical indicator calculation
- `pandas/numpy` - Data manipulation
- `scikit-learn` - Optional ML features

### File Descriptions:

| File | Purpose | Editable by AI? |
|------|---------|-----------------|
| `prepare_trading.py` | Data pipeline | No |
| `backtest.py` | Backtesting engine | No |
| `strategy.py` | Trading logic | **YES** |
| `program_trading.md` | Agent instructions | No |
| `results_trading.tsv` | Experiment log | No |

## 🎮 Usage Examples

### Manual Backtest:
```python
import pickle
from backtest import BacktestEngine
import strategy

# Load data
with open('~/.cache/autoresearch-trading/indicators/data_splits.pkl', 'rb') as f:
    splits = pickle.load(f)

# Run backtest
engine = BacktestEngine(time_budget=300)
result = engine.evaluate_strategy(strategy, splits['val'], 'val')

print(f"Sharpe: {result.sharpe_ratio:.3f}")
print(f"Return: {result.total_return:.2%}")
print(f"Drawdown: {result.max_drawdown:.2%}")
```

### Parameter Optimization Template:
```python
# In strategy.py - AI agent can implement this
def optimize_parameters(data):
    best_params = {}
    best_score = -float('inf')
    
    for tenkan in [7, 9, 12, 14]:
        for kijun in [20, 26, 30]:
            params = PARAMETERS.copy()
            params['tenkan_period'] = tenkan
            params['kijun_period'] = kijun
            
            # Evaluate this parameter set
            score = evaluate_params(data, params)
            
            if score > best_score:
                best_score = score
                best_params = params
    
    return best_params
```

## 🚨 Important Notes

1. **Time Budget**: Each experiment limited to 5 minutes wall clock
2. **Validation Only**: Optimize on validation data, not test data
3. **Realistic Assumptions**: 0.1% trading fees, 4-hour execution
4. **Overfitting Risk**: Watch for win rates > 70% (may be overfitting)
5. **Git Workflow**: All changes tracked via git commits

## 📈 Expected Outcomes

Running overnight autonomous research should:
1. Discover optimal Ichimoku parameters for BTC
2. Find effective entry/exit rule combinations
3. Develop robust risk management settings
4. Potentially achieve Sharpe ratio > 1.0
5. Provide insights into BTC market behavior

## 🆘 Troubleshooting

### Common Issues:

1. **Data download fails**:
   ```bash
   python prepare_trading.py --test --update
   ```

2. **Indicator calculation errors**:
   ```bash
   pip install --upgrade ta pandas
   ```

3. **Memory issues on Mac Mini**:
   - Reduce dataset size in `prepare_trading.py`
   - Use `--test` flag for development

4. **Backtest too slow**:
   - Reduce `time_budget` in `BacktestEngine`
   - Use smaller validation dataset

## 📚 Next Steps

After initial optimization:

1. **Add more indicators** (ATR, Stochastic, etc.)
2. **Implement MLX integration** for Apple Silicon speed
3. **Add walk-forward optimization**
4. **Create ensemble strategies**
5. **Deploy to paper trading**

## 📞 Support

- **GitHub Issues**: https://github.com/AndErem314/autoresearch-mini-M4/issues
- **Documentation**: See `README_TRADING.md` for detailed trading docs
- **Original Code**: Preserved in original files for reference

---

**Your trading autoresearch infrastructure is now complete and ready for autonomous optimization on your Mac Mini M4!** 🚀