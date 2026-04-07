"""
Parameter sweep optimizer for BTC/USDT trading strategies.
Uses random sampling to explore the parameter space efficiently,
evaluates on validation set, then tests top performers on held-out test set.

Features:
- Random sampling: explores large parameter spaces without full grid explosion
- Resumable: saves results after every 100 samples
- Prevents overfitting: validates on unseen test data
- Reports top configurations ranked by Sharpe ratio
- CSV output for easy analysis

Usage:
    python optimizer.py --samples 5000                  # Run 5K random combos on val set
    python optimizer.py --samples 10000 --top-n 20     # 10K samples, test top 20
    python optimizer.py --samples 5000 --tier 2        # Tier 2 (indicator periods)
    python optimizer.py --test                         # Run existing val results on test set
    python optimizer.py --max-combos 500               # Limit for quick testing
"""

import pickle
import sys
import os
import time
import json
import copy
import random
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from backtest import BacktestEngine, TradeAction, TradingSignal, Position

# ---------------------------------------------------------------------------
# Data paths
# ---------------------------------------------------------------------------
DATA_DIR = Path.home() / ".cache" / "autoresearch-trading" / "indicators"
SPLITS_FILE = DATA_DIR / "data_splits.pkl"
PROJECT_DIR = Path.home() / "GitHub_projects" / "autoresearch-mini-M4"
RESULTS_DIR = PROJECT_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Import strategy module
# ---------------------------------------------------------------------------
import importlib.util
spec = importlib.util.spec_from_file_location("strategy", PROJECT_DIR / "strategy.py")
strategy_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(strategy_mod)

# ---------------------------------------------------------------------------
# Ichimoku recalculation (needed when indicator periods change)
# ---------------------------------------------------------------------------
def recalculate_ichimoku(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
Recalculate all Ichimoku indicators with custom periods."""
    df = df.copy(deep=True)
    
    tenkan = params.get('tenkan_period', 9)
    kijun = params.get('kijun_period', 26)
    senkou_b = params.get('senkou_b_period', 52)
    displacement = params.get('displacement', 26)
    
    # Tenkan-sen (Conversion Line)
    high_t = df['high'].rolling(window=tenkan).max()
    low_t = df['low'].rolling(window=tenkan).min()
    df['ichimoku_tenkan'] = (high_t + low_t) / 2
    
    # Kijun-sen (Base Line)
    high_k = df['high'].rolling(window=kijun).max()
    low_k = df['low'].rolling(window=kijun).min()
    df['ichimoku_kijun'] = (high_k + low_k) / 2
    
    # Senkou Span A (Leading Span A)
    df['ichimoku_senkou_a'] = (
        (df['ichimoku_tenkan'] + df['ichimoku_kijun']) / 2
    ).shift(displacement)
    
    # Senkou Span B (Leading Span B)
    high_s = df['high'].rolling(window=senkou_b).max()
    low_s = df['low'].rolling(window=senkou_b).min()
    df['ichimoku_senkou_b'] = ((high_s + low_s) / 2).shift(displacement)
    
    # Chikou Span (Lagging Span)
    df['ichimoku_chikou'] = df['close'].shift(-displacement)
    
    # Cloud top/bottom
    df['ichimoku_cloud_top'] = df[['ichimoku_senkou_a', 'ichimoku_senkou_b']].max(axis=1)
    df['ichimoku_cloud_bottom'] = df[['ichimoku_senkou_a', 'ichimoku_senkou_b']].min(axis=1)
    
    # Position relative to cloud
    df['ichimoku_price_above_cloud'] = df['close'] > df['ichimoku_cloud_top']
    df['ichimoku_price_below_cloud'] = df['close'] < df['ichimoku_cloud_bottom']
    df['ichimoku_price_in_cloud'] = ~df['ichimoku_price_above_cloud'] & ~df['ichimoku_price_below_cloud']
    
    # TK Cross (Tenkan crosses above Kijun)
    tenkan_above = df['ichimoku_tenkan'] > df['ichimoku_kijun']
    df['ichimoku_tk_cross'] = tenkan_above & ~tenkan_above.shift(1).fillna(False)
    
    # Golden cross: tenkan was <= kijun, now > kijun
    prev_crossover = df['ichimoku_tenkan'].shift(1) <= df['ichimoku_kijun'].shift(1)
    curr_above = df['ichimoku_tenkan'] > df['ichimoku_kijun']
    df['ichimoku_golden_cross'] = curr_above & prev_crossover
    
    # Death cross: tenkan was >= kijun, now < kijun
    prev_crossover_down = df['ichimoku_tenkan'].shift(1) >= df['ichimoku_kijun'].shift(1)
    curr_below = df['ichimoku_tenkan'] < df['ichimoku_kijun']
    df['ichimoku_death_cross'] = curr_below & prev_crossover_down
    
    # Cloud width
    df['ichimoku_cloud_width'] = (df['ichimoku_cloud_top'] - df['ichimoku_cloud_bottom']).abs()
    
    return df


def is_tier2_param_set(params: dict) -> bool:
    """Check if params include indicator period overrides."""
    defaults = {'tenkan_period': 9, 'kijun_period': 26, 'senkou_b_period': 52, 'displacement': 26}
    return any(params.get(k) != v for k, v in defaults.items())


# ---------------------------------------------------------------------------
# Parameter ranges — v3.0 Trend + Pullback Entry
# ---------------------------------------------------------------------------

# Signal-level parameters (no indicator recalculation needed)
TIER1_PARAM_RANGES = {
    'rsi_pullback_threshold': {'type': 'discrete', 'values': [25, 28, 30, 33, 35, 37, 40, 42, 45]},
    'rsi_bounce_level': {'type': 'discrete', 'values': [45, 48, 50, 52, 55, 58, 60]},
    
    'stop_loss_pct': {'type': 'discrete', 'values': [2.0, 3.0, 4.0, 5.0, 7.0, 10.0, 12.0, 15.0]},
    'take_profit_pct': {'type': 'discrete', 'values': [5.0, 8.0, 10.0, 12.0, 15.0, 20.0, 25.0, 30.0]},
    'position_size_pct': {'type': 'discrete', 'values': [10.0, 15.0, 20.0, 25.0, 30.0, 50.0, 75.0, 100.0]},
    
    # Trend confirmation toggles
    'require_uptrend': {'type': 'bool'},
    'require_price_above_cloud': {'type': 'bool'},
    'require_cloud_bullish': {'type': 'bool'},
    
    # Entry mode toggles
    'enable_pullback_entry': {'type': 'bool'},
    'enable_trend_entry': {'type': 'bool'},
    
    # Exit toggles
    'exit_on_death_cross': {'type': 'bool'},
    'exit_price_below_kijun': {'type': 'bool'},
    'exit_price_below_cloud': {'type': 'bool'},
    'exit_rsi_overbought': {'type': 'bool'},
    
    # Filters
    'require_volume_above_avg': {'type': 'bool'},
    'min_cloud_width_pct': {'type': 'discrete', 'values': [0.1, 0.5, 1.0, 2.0, 3.0, 5.0]},
}

# Indicator period parameters (requires recalculation per sample)
TIER2_PARAM_RANGES = {
    'tenkan_period': {'type': 'discrete', 'values': [5, 7, 9, 11, 13, 15, 17, 19, 21]},
    'kijun_period': {'type': 'discrete', 'values': [16, 18, 20, 22, 24, 26, 28, 30, 32, 34]},
    'senkou_b_period': {'type': 'discrete', 'values': [30, 36, 40, 44, 48, 52, 56, 60, 64, 68]},
    'displacement': {'type': 'discrete', 'values': [16, 20, 22, 24, 26, 28, 30]},
}

# Fixed params (always these values)
FIXED_PARAMS = {
    'enable_short': False,
    'adapt_to_regime': False,
    'exit_on_golden_cross': False,
    'exit_price_above_kijun': False,
    'exit_price_above_cloud': False,
    'max_positions': 1,
    'trailing_stop_pct': 3.0,
}


# ---------------------------------------------------------------------------
# Random sampling
# ---------------------------------------------------------------------------
def sample_params(param_ranges: dict, base_params: dict = None) -> dict:
    """Generate a random parameter combination from ranges."""
    params = base_params.copy() if base_params else {}
    
    for key, config in param_ranges.items():
        if config['type'] == 'discrete':
            params[key] = random.choice(config['values'])
        elif config['type'] == 'bool':
            params[key] = random.choice([True, False])
        elif config['type'] == 'range':
            params[key] = random.uniform(config['min'], config['max'])
    
    return params


# ---------------------------------------------------------------------------
# Backtest runner (single-threaded, fast)
# ---------------------------------------------------------------------------
def run_backtest(params: dict, df: pd.DataFrame) -> dict:
    """
    Run a single backtest with the given parameters on a DataFrame.
    Returns a result dict with metrics.
    """
    try:
        # Check if we need to recalculate indicators
        if is_tier2_param_set(params):
            df = recalculate_ichimoku(df, params)
        
        # Reset strategy internal state
        if hasattr(strategy_mod, 'reset_state'):
            strategy_mod.reset_state()
        
        # Set the strategy's parameters
        original_params = strategy_mod.PARAMETERS
        strategy_mod.PARAMETERS = copy.deepcopy(params)
        
        try:
            # Create engine
            engine = BacktestEngine(
                initial_capital=10000.0,
                trading_fee=0.001,
                position_size=0.1,
                max_positions=1,
            )
            
            # Run the backtest
            result = engine.evaluate_strategy(strategy_mod, df, 'test')
        finally:
            strategy_mod.PARAMETERS = original_params
        
        # Build result dict
        return {
            'params': params,
            'sharpe_ratio': result.sharpe_ratio,
            'sortino_ratio': result.sortino_ratio,
            'total_return': result.total_return,
            'max_drawdown': result.max_drawdown,
            'win_rate': result.win_rate,
            'total_trades': result.total_trades,
            'profit_factor': result.profit_factor,
            'expectancy': result.expectancy,
            'calmar_ratio': result.calmar_ratio,
            'backtest_duration': result.backtest_duration,
            'error': None,
        }
        
    except Exception as e:
        return {
            'params': params,
            'sharpe_ratio': float('-inf'),
            'sortino_ratio': float('-inf'),
            'total_return': 0,
            'max_drawdown': 100,
            'win_rate': 0,
            'total_trades': 0,
            'profit_factor': 0,
            'expectancy': 0,
            'calmar_ratio': float('-inf'),
            'backtest_duration': 0,
            'error': str(e),
        }


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
def score_config(result: dict) -> float:
    """
    Composite score for ranking configurations.
    """
    sharpe = result.get('sharpe_ratio', -999)
    total_return = result.get('total_return', 0)
    win_rate = result.get('win_rate', 0) / 100.0
    max_dd = result.get('max_drawdown', 100) / 100.0
    total_trades = result.get('total_trades', 0)
    profit_factor = result.get('profit_factor', 0)
    
    # Disqualify configs with too few trades
    if total_trades < 5:
        return -10000
    
    # HEAVILY penalize configs that lose money
    if total_return <= 0:
        return -1000 + total_return * 100
    
    # Penalize configs with very high trade count but mediocre win rate
    if total_trades > 300 and win_rate < 0.6:
        return -500
    
    # Reward configs with good profit factor (> 1.5 is decent)
    pf_bonus = min(profit_factor, 3.0) * 0.1 if profit_factor > 1.0 else 0
    
    # Composite score for profitable configs only
    trade_penalty = max(0, 1.0 - total_trades / 30.0) * 1.0
    
    score = (
        sharpe * 0.4 +
        win_rate * 0.25 +
        total_return * 2.0 +
        (1 - max_dd) * 0.2 -
        trade_penalty +
        pf_bonus
    )
    
    return score


# ---------------------------------------------------------------------------
# Optimizer
# ---------------------------------------------------------------------------
class StrategyOptimizer:
    def __init__(self):
        with open(SPLITS_FILE, 'rb') as f:
            self.splits = pickle.load(f)
        
        self.val_results: List[dict] = []
        self.results_file = RESULTS_DIR / "val_results.pkl"
    
    def run_sweep(self, n_samples: int = 5000, tier: str = "1",
                  resume: bool = True, base_params: dict = None):
        """Run random parameter sweep and score on validation data."""
        tier_name = "Signal Logic" if tier == "1" else "Indicator Periods"
        print(f"\n{'='*60}")
        print(f"SWEEP: {tier_name} Parameters ({n_samples} random samples)")
        print(f"{'='*60}")
        print(f"Validation data: {self.splits['val'].shape[0]} rows")
        print(f"Test data: {self.splits['test'].shape[0]} rows\n")
        
        # Load existing results for resume
        start_idx = 0
        if resume and self.results_file.exists():
            with open(self.results_file, 'rb') as f:
                self.val_results = pickle.load(f)
            
            existing_count = len(self.val_results)
            start_idx = existing_count
            print(f"Resuming from sample {start_idx + 1}/{n_samples} ({existing_count} already done)\n")
        
        # Determine which param ranges to use
        param_ranges = TIER1_PARAM_RANGES if tier == "1" else {**TIER1_PARAM_RANGES, **TIER2_PARAM_RANGES}
        if base_params and tier == "2":
            for k, v in base_params.items():
                if k not in TIER2_PARAM_RANGES:
                    param_ranges.pop(k, None)
        
        # Run sweep
        valid = no_trades = errors = 0
        best_sharpe = float('-inf')
        start_time = time.time()
        
        for i in range(start_idx, n_samples):
            params = sample_params(param_ranges, {**FIXED_PARAMS})
            if base_params:
                params.update(base_params)
            
            # Run backtest on validation data
            val_df = self.splits['val']
            result = run_backtest(params, val_df)
            
            result['score'] = score_config(result)
            result['data_type'] = 'val'
            
            # Track stats
            if result['error']:
                errors += 1
            elif result['total_trades'] == 0:
                no_trades += 1
            else:
                valid += 1
                if result['sharpe_ratio'] > best_sharpe:
                    best_sharpe = result['sharpe_ratio']
            
            self.val_results.append(result)
            
            # Checkpoint every 100 samples
            if (i + 1) % 100 == 0:
                with open(self.results_file, 'wb') as f:
                    pickle.dump(self.val_results, f)
            
            # Progress
            elapsed = time.time() - start_time
            rate = (i - start_idx + 1) / elapsed if elapsed > 0 else 0
            eta = (n_samples - i - 1) / rate if rate > 0 else 0
            print(f"\r [{i+1}/{n_samples}] Valid: {valid} | No trades: {no_trades} | "
                  f"Errors: {errors} | Best Sharpe: {best_sharpe:.3f} | Rate: {rate:.0f}/s | "
                  f"ETA: {eta:.0f}s", end='', flush=True)
        
        print()  # New line after progress
        
        # Save final results
        with open(self.results_file, 'wb') as f:
            pickle.dump(self.val_results, f)
        
        elapsed = time.time() - start_time
        print(f"\nSweep complete in {elapsed:.1f}s ({n_samples} total, ~{n_samples/elapsed:.1f}/s)")
        
        # Report
        valid_results = [r for r in self.val_results if r['error'] is None and r['total_trades'] > 0]
        if valid_results:
            sharpe_vals = [r['sharpe_ratio'] for r in valid_results]
            returns = [r['total_return'] for r in valid_results]
            win_rates = [r['win_rate'] for r in valid_results]
            
            print(f"\n{'='*60}")
            print(f"Summary: Validation")
            print(f"{'='*60}")
            print(f"Valid configs: {len(valid_results)}")
            print(f"Best  Sharpe: {max(sharpe_vals):.3f}")
            print(f"Avg   Sharpe: {np.mean(sharpe_vals):.3f}")
            print(f"Median Sharpe: {np.median(sharpe_vals):.3f}")
            print(f"Worst Sharpe: {min(sharpe_vals):.3f}")
            print(f"Best Return:  {max(returns)*100:.1f}%")
            print(f"Avg   Return: {np.mean(returns)*100:.1f}%")
            print(f"Best Win Rate: {max(win_rates):.1f}%")
            print(f"Avg   Win Rate: {np.mean(win_rates):.1f}%")
        
        return self.val_results


    def test_top_configs(self, top_n: int = 10, tier: str = "1"):
        """Test top validation configs on held-out test data."""
        if not self.val_results:
            print("No validation results to test.")
            return []
        
        # Score and sort
        scored = [(r, score_config(r)) for r in self.val_results if r.get('error') is None and r.get('total_trades', 0) > 0]
        if not scored:
            print("No valid configs found.")
            return []
        
        scored.sort(key=lambda x: x[1], reverse=True)
        
        print(f"\n{'='*70}")
        print(f"TOP 20 CONFIGURATIONS (Validation)")
        print(f"{'='*70}")
        print(f"{'Rank':>4} | {'Score':>7} | {'Sharpe':>6} | {'Return':>7} | {'MaxDD':>6} | {'Win%':>5} | {'Trades':>6}")
        print(f"{'-'*4}+{'-'*8}+{'-'*8}+{'-'*8}+{'-'*7}+{'-'*6}+{'-'*7}")
        
        for rank, (result, score) in enumerate(scored[:20], 1):
            print(f"{rank:>4} | {score:>7.3f} | {result['sharpe_ratio']:>6.3f} | "
                  f"{result['total_return']*100:>6.1f}% | {result['max_drawdown']:>5.1f}% | "
                  f"{result['win_rate']:>4.1f}% | {result['total_trades']:>6}")
        
        # CSV full results
        csv_file = RESULTS_DIR / "validation_full_results.csv"
        rows = []
        for result, score in scored:
            row = {
                'score': score,
                'sharpe_ratio': result['sharpe_ratio'],
                'total_return': result['total_return'],
                'max_drawdown': result['max_drawdown'],
                'win_rate': result['win_rate'],
                'total_trades': result['total_trades'],
                'profit_factor': result['profit_factor'],
                'calmar_ratio': result['calmar_ratio'],
                'backtest_duration': result['backtest_duration'],
                'error': result['error'],
            }
            # Flatten params
            params = result.get('params', {}) or {}
            for k, v in params.items():
                row[f'param_{k}'] = v
            rows.append(row)
        
        if rows:
            df = pd.DataFrame(rows)
            df.to_csv(csv_file, index=False)
        
        print(f"\nCSV saved: {csv_file}\n")
        
        # Test on test set
        top_results = [r for r, _ in scored[:top_n]]
        test_results = []
        test_data = self.splits['test']
        
        print(f"{'='*70}")
        print(f"TEST SET: Top {len(top_results)} from validation")
        print(f"{'='*70}")
        print(f"Test data size: {test_data.shape[0]} rows\n")
        
        for i, result in enumerate(top_results):
            start = time.time()
            test_result = run_backtest(result['params'], test_data)
            elapsed = time.time() - start
            
            test_results.append(test_result)
            
            sharpe_val = result.get('sharpe_ratio', 0)
            print(f" [{i+1}/{len(top_results)}] Sharpe(val)={sharpe_val:.3f} → Sharpe(test)={test_result['sharpe_ratio']:.3f} | "
                  f"Return: {test_result['total_return']:.1f}% | Trades: {test_result['total_trades']} | "
                  f"Elapsed: {elapsed:.1f}s")
        
        print(f"\nTest evaluation complete in {sum(time.time()-start for _ in test_results):.1f}s (approx)")
        
        # Final ranking
        print(f"\n{'='*70}")
        print(f"FINAL RANKED RESULTS (Test Set)")
        print(f"{'='*70}\n")
        
        for i, (val_res, (val_result, score)) in enumerate(zip(test_results, scored[:top_n])):
            if val_res['params'] is None:
                continue
            
            print(f"#{i+1} | Val Sharpe: {val_result['sharpe_ratio']} | Test Sharpe: {val_res['sharpe_ratio']:.3f}")
            print(f"   Return: {val_res['total_return']:.1f}% | MaxDD: {val_res['max_drawdown']:.1f}% | "
                  f"Win%: {val_res['win_rate']:.1f}% | Trades: {val_res['total_trades']} | "
                  f"Profit Factor: {val_res['profit_factor']:.2f}")
            
            # Key params
            params = val_result.get('params', {}) or {}
            key_params = ['rsi_pullback_threshold', 'rsi_bounce_level',
                         'stop_loss_pct', 'take_profit_pct', 'position_size_pct',
                         'require_uptrend', 'require_price_above_cloud', 'enable_pullback_entry',
                         'exit_on_death_cross', 'min_cloud_width_pct']
            param_str = " | ".join(f"{k}={params[k]}" for k in key_params if k in params)
            print(f"   Params: {param_str}")
            print()
        
        # Save CSV
        csv_file = RESULTS_DIR / "final_results.csv"
        rows = []
        for val_res, (val_result, _) in zip(test_results, scored[:top_n]):
            if val_res['params'] is None:
                continue
            row = {
                'rank': len(rows) + 1,
                'val_sharpe': val_result['sharpe_ratio'],
                'test_sharpe': val_res['sharpe_ratio'],
                'test_return': val_res['total_return'],
                'test_max_dd': val_res['max_drawdown'],
                'test_win_rate': val_res['win_rate'],
                'test_trades': val_res['total_trades'],
                'test_profit_factor': val_res['profit_factor'],
            }
            params = val_res.get('params', {}) or {}
            for k, v in params.items():
                row[f'param_{k}'] = v
            rows.append(row)
        
        if rows:
            df = pd.DataFrame(rows)
            df.to_csv(csv_file, index=False)
        
        print(f"CSV saved: {csv_file}")
        return test_results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description='Optimize trading strategy parameters')
    parser.add_argument('--samples', type=int, default=5000, help='Number of random samples')
    parser.add_argument('--max-combos', type=int, help='Alias for --samples')
    parser.add_argument('--tier', type=str, default="1", choices=["1", "2"], help='Parameter tier')
    parser.add_argument('--resume', action='store_true', help='Resume from last checkpoint')
    parser.add_argument('--no-resume', action='store_true', help='Do not resume')
    parser.add_argument('--top-n', type=int, default=10, help='Number of top configs to test')
    parser.add_argument('--test', action='store_true', help='Run test only (skip sweep)')
    args = parser.parse_args()
    
    n = args.max_combos if args.max_combos else args.samples
    
    optimizer = StrategyOptimizer()
    
    if not args.test:
        resume = not args.no_resume
        optimizer.run_sweep(n_samples=n, tier=args.tier, resume=resume)
    
    # Test top configs on test set
    top_n = min(args.top_n, len(optimizer.val_results)) if optimizer.val_results else 10
    optimizer.test_top_configs(top_n=top_n, tier=args.tier)


if __name__ == "__main__":
    main()
