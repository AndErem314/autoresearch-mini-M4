# autoresearch-mini-M4

**Apple Silicon (MLX) port of [Karpathy's autoresearch](https://github.com/karpathy/autoresearch) with BTC Trading Adaptation**

## 🎯 Two Modes Available

### 1. **Original MLX Mode** (Text Generation)
- Autonomous AI research loops for text generation
- MLX framework for Apple Silicon native performance
- Fixed 5-minute training experiments
- See original files: `train.py`, `prepare.py`, `program.md`

### 2. **Trading Adaptation Mode** (BTC Strategy Optimization) 🆕
- **BTC/USDT trading strategy optimization using Ichimoku Cloud**
- **Complete infrastructure for autonomous trading research**
- **Fixed 5-minute backtesting experiments**
- **Ready for Mac Mini M4 optimization**

## 🚀 Quick Start - Trading Mode

```bash
# Clone and setup
git clone https://github.com/AndErem314/autoresearch-mini-M4.git
cd autoresearch-mini-M4
git checkout trading-adaptation

# One-click setup
chmod +x setup_trading.sh
./setup_trading.sh

# Prepare BTC data
source venv/bin/activate
python prepare_trading.py --test  # Test with small dataset
python prepare_trading.py         # Full dataset (Nov 2021 - Mar 2024)

# Start autonomous research
# Point your AI agent at program_trading.md
```

## 📁 Trading Infrastructure

### Core Files:
- `prepare_trading.py` - BTC data pipeline with Ichimoku Cloud (50+ indicators)
- `backtest.py` - Fixed-time backtesting engine (15+ metrics)
- `strategy.py` - Trading strategy template **(AI agent edits this)**
- `program_trading.md` - Autonomous research instructions
- `setup_trading.sh` - Mac Mini M4 setup script

### Key Features:
- **Complete Ichimoku Cloud implementation** (19 indicators)
- **40+ technical indicators** pre-calculated
- **5-minute fixed-time backtesting** per experiment
- **Keep/revert logic** based on Sharpe ratio
- **Git-based experiment tracking**
- **Mac Mini M4 optimized**

## 📊 Trading Data
- **Symbol**: BTCUSDT (Bitcoin/Tether on Binance)
- **Interval**: 4-hour charts
- **Period**: Nov 2021 - Mar 2024
- **Splits**: Train (2y), Validation (4m), Test (1m)
- **Cache**: `~/.cache/autoresearch-trading/`
- **API**: Binance (no API key needed for historical data)

## 🎯 Optimization Goal
Maximize **Sharpe Ratio** with constraints:
- Maximum drawdown < 20%
- Win rate > 45%
- Minimum 10 trades
- Positive expectancy

## 📚 Documentation
- `README_COMPLETE.md` - Complete infrastructure overview
- `README_TRADING.md` - Detailed trading documentation
- `program_trading.md` - AI agent instructions

## 🍎 Mac Mini M4 Advantages
1. **Unified Memory** - Handle large datasets without GPU limits
2. **Energy Efficient** - Run 24/7 optimization loops
3. **Local & Private** - Your strategies stay on your machine
4. **MLX Ready** - Can integrate Apple's ML framework

## 🔧 Requirements
- Apple Silicon Mac (M1/M2/M3/M4)
- Python 3.10+
- Virtual environment (auto-created by setup script)

## 📈 Expected Workflow
1. AI agent edits `strategy.py` parameters/rules
2. 5-minute backtest on validation data
3. Calculate Sharpe ratio and constraints
4. If improved: `git commit`
5. If not: `git checkout strategy.py` (revert)
6. Repeat overnight for autonomous optimization

## 🆕 What's New in Trading Adaptation
- **Complete BTC data pipeline** with Yahoo Finance integration
- **Ichimoku Cloud optimization** framework
- **Professional backtesting engine** with realistic assumptions
- **Autonomous research program** for AI agents
- **Mac Mini M4 optimized setup**

## ⚠️ Note
The original MLX text generation code is preserved in:
- `prepare.py` (original)
- `train.py` (original)
- `program.md` (original)
- `README_ORIGINAL.md` (coming soon)

## 📞 Support
- **GitHub Issues**: https://github.com/AndErem314/autoresearch-mini-M4/issues
- **Trading Docs**: See `README_TRADING.md` and `README_COMPLETE.md`

---

**Ready for autonomous BTC trading strategy optimization on your Mac Mini M4!** 🚀