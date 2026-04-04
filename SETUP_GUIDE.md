# Mac Mini M4 Setup Guide

## Quick Start Commands

```bash
# 1. Clone your repository
git clone https://github.com/AndErem314/autoresearch-mini-M4.git
cd autoresearch-mini-M4
git checkout trading-adaptation

# 2. Run one-click setup
chmod +x setup_trading.sh
./setup_trading.sh

# 3. Prepare BTC data (after setup completes)
source venv/bin/activate

# Test with small dataset first
python prepare_trading.py --test

# Then prepare full dataset (Nov 2021 - Mar 2024)
python prepare_trading.py

# 4. Start autonomous research
# Point your AI agent at program_trading.md
```

## What Gets Installed

### Python Dependencies:
- `python-binance` - Binance API for BTC/USDT data
- `pandas/numpy` - Data manipulation
- `ta` - Technical indicator calculation (Ichimoku, RSI, MACD, etc.)
- `scikit-learn` - Optional machine learning features
- `matplotlib` - Visualization (optional)

### Directory Structure Created:
```
~/.cache/autoresearch-trading/
├── data/                    # Cached BTC data
└── indicators/              # Pre-calculated indicators
```

### Virtual Environment:
- Created at `venv/` in project directory
- Automatically activated by setup script
- All dependencies installed

## Testing the Setup

After running the setup script, test with:

```bash
# Test data pipeline
python -c "
import sys
sys.path.insert(0, '.')
from prepare_trading import download_btc_data
data = download_btc_data(start_date='2024-01-01', end_date='2024-01-05', interval='4h')
print(f'Downloaded {len(data)} BTC candles')
"

# Test strategy
python -c "
import sys
sys.path.insert(0, '.')
from strategy import test_strategy
test_strategy()
"
```

## Starting Autonomous Research

1. **Read the program**: `cat program_trading.md | head -50`
2. **Point your AI agent** at `program_trading.md`
3. **Let it run overnight** - It will:
   - Edit `strategy.py` parameters
   - Run 5-minute backtests
   - Keep improvements, revert failures
   - Log results to `results_trading.tsv`

## Troubleshooting

### If Binance API fails:
```bash
# Check internet connection
ping api.binance.com

# Try with proxy (if needed)
export https_proxy=http://your-proxy:port
```

### If Python dependencies fail:
```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_trading.txt
```

### If memory issues on Mac Mini:
- Use `--test` flag for development
- Reduce dataset size in `prepare_trading.py`
- Close other applications during backtesting

## Next Steps After Setup

1. **Verify data download** works
2. **Test a manual backtest** with default strategy
3. **Review the AI program** in `program_trading.md`
4. **Start autonomous optimization** overnight
5. **Check results** in `results_trading.tsv` next morning

## Ready to Go!

Your complete BTC/Ichimoku trading optimization infrastructure is now set up. The AI agent will autonomously:

1. Test different Ichimoku parameters (periods, rules)
2. Combine with other indicators (RSI, MACD, etc.)
3. Optimize risk management (stop loss, position sizing)
4. Find strategies with best Sharpe ratio
5. Log all experiments for review

**Run `./setup_trading.sh` on your Mac Mini M4 and you're ready!** 🚀