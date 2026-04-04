# BTC Trading Strategy Optimizer

**Complete infrastructure for autonomous BTC/USDT trading strategy optimization using Ichimoku Cloud indicators.**

## 🎯 Purpose

This repository provides a complete, ready-to-run system for autonomously optimizing BTC trading strategies. It's specifically designed for:

- **Mac Mini M4 optimization** with one-click setup
- **Autonomous AI research** with fixed 5-minute experiments
- **Ichimoku Cloud strategy optimization** for BTC/USDT
- **Professional backtesting** with 15+ performance metrics
- **Binance API integration** for reliable crypto data

## 🚀 Quick Start

```bash
# 1. Clone repository
git clone https://github.com/AndErem314/autoresearch-mini-M4.git
cd autoresearch-mini-M4

# 2. Run one-click setup (Mac Mini M4 optimized)
chmod +x setup_trading.sh
./setup_trading.sh

# 3. Prepare BTC data
source venv/bin/activate
python prepare_trading.py --test  # Test with small dataset
python prepare_trading.py         # Full dataset (Nov 2021 - Mar 2024)

# 4. Start autonomous optimization
# Point your AI agent at program_trading.md
```

## 📁 Project Structure

```
autoresearch-mini-M4/
├── 📊 DATA PIPELINE
│   ├── prepare_trading.py          # Binance BTC data & indicators
│   ├── requirements_trading.txt    # Python dependencies
│   └── test_data_pipeline.py       # Pipeline testing
│
├── ⚙️ BACKTESTING ENGINE
│   ├── backtest.py                 # Fixed-time backtesting with metrics
│   ├── strategy.py                 # Trading strategy template (AI EDITABLE)
│   └── results_trading.tsv         # Experiment results log
│
├── 🤖 AUTONOMOUS RESEARCH
│   └── program_trading.md          # AI agent instructions
│
├── 🛠️ SETUP & UTILITIES
│   ├── setup_trading.sh            # One-click setup script
│   ├── SETUP_GUIDE.md              # Detailed setup instructions
│   ├── README_COMPLETE.md          # Complete infrastructure docs
│   ├── README_TRADING.md           # Trading-specific documentation
│   └── .gitignore                  # Git exclusions
│
└── 📚 LICENSE                      # MIT License
```

## 🎯 Core Features

### 1. **Complete Ichimoku Cloud Implementation**
- All 5 Ichimoku components calculated
- 19 Ichimoku-derived indicators
- Customizable periods (Tenkan, Kijun, Senkou B)
- Cloud position, crosses, and distance metrics

### 2. **Binance API Integration**
- Real BTC/USDT data from Binance exchange
- No API key needed for historical data
- 4-hour chart data (Nov 2021 - Mar 2024)
- Automatic caching at `~/.cache/autoresearch-trading/`

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

## 📊 Trading Data

### Time Periods:
- **Training**: Nov 2021 - Nov 2023 (2 years)
- **Validation**: Nov 2023 - Mar 2024 (4 months) ← **Optimization target**
- **Testing**: Mar 2024 - Apr 2024 (1 month) ← **Final evaluation**

### Data Source:
- **Symbol**: BTCUSDT (Bitcoin/Tether on Binance)
- **Interval**: 4-hour charts
- **API**: Binance (no API key needed for historical data)
- **Cache**: `~/.cache/autoresearch-trading/`

## 🎯 Optimization Goal

**Primary objective**: Maximize Sharpe Ratio (risk-adjusted returns)

**Secondary constraints** (must all be satisfied):
- Maximum drawdown < 20%
- Win rate > 45%
- Minimum 10 trades
- Positive expectancy (> 0)

## 🔧 Technical Details

### Dependencies:
- `python-binance` - Binance API for crypto data
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

## 🍎 Mac Mini M4 Advantages

1. **Unified Memory** - Handle large datasets without GPU limits
2. **Energy Efficient** - Run 24/7 optimization loops
3. **Local & Private** - Your strategies stay on your machine
4. **Ready for MLX** - Can integrate Apple's ML framework later

## 📈 Expected Workflow

1. AI agent edits `strategy.py` parameters/rules
2. 5-minute backtest on validation data
3. Calculate Sharpe ratio and constraints
4. If improved: `git commit`
5. If not: `git checkout strategy.py` (revert)
6. Repeat overnight for autonomous optimization

## 🚨 Important Notes

1. **Time Budget**: Each experiment limited to 5 minutes wall clock
2. **Validation Only**: Optimize on validation data, not test data
3. **Realistic Assumptions**: 0.1% trading fees, 4-hour execution
4. **Overfitting Risk**: Watch for win rates > 70% (may be overfitting)
5. **Git Workflow**: All changes tracked via git commits

## 📚 Documentation

- `README_COMPLETE.md` - Complete infrastructure overview
- `README_TRADING.md` - Detailed trading documentation
- `SETUP_GUIDE.md` - Step-by-step setup instructions
- `program_trading.md` - AI agent instructions

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

## 📞 Support

- **GitHub Issues**: https://github.com/AndErem314/autoresearch-mini-M4/issues
- **Documentation**: See `README_TRADING.md` for detailed trading docs

---

**Your complete BTC/Ichimoku trading strategy optimization infrastructure is ready!** 🚀