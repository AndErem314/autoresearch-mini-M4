"""
Fixed-time backtesting engine for trading strategy optimization.
Evaluates trading strategies within a 5-minute time budget.

Usage:
    python backtest.py --strategy strategy.py --data splits.pkl
    python backtest.py --test  # Run test with sample strategy
"""

import argparse
import pickle
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import os

# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

class TradeAction(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

@dataclass
class Trade:
    timestamp: pd.Timestamp
    action: TradeAction
    price: float
    quantity: float
    fee: float
    reason: str = ""

@dataclass
class Position:
    entry_price: float
    entry_time: pd.Timestamp
    quantity: float
    current_value: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0

@dataclass
class BacktestResult:
    # Performance metrics
    total_return: float
    sharpe_ratio: float
    sortino_ratio: float
    profit_factor: float
    max_drawdown: float
    win_rate: float
    avg_win: float
    avg_loss: float
    expectancy: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    
    # Risk metrics
    volatility: float
    downside_volatility: float
    calmar_ratio: float
    ulcer_index: float
    
    # Trading stats
    avg_holding_period: float  # in periods
    profit_per_trade: float
    largest_win: float
    largest_loss: float
    
    # Strategy info
    strategy_name: str
    parameters: Dict[str, Any]
    backtest_duration: float  # seconds
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_return': self.total_return,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'profit_factor': self.profit_factor,
            'max_drawdown': self.max_drawdown,
            'win_rate': self.win_rate,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'expectancy': self.expectancy,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'volatility': self.volatility,
            'downside_volatility': self.downside_volatility,
            'calmar_ratio': self.calmar_ratio,
            'ulcer_index': self.ulcer_index,
            'avg_holding_period': self.avg_holding_period,
            'profit_per_trade': self.profit_per_trade,
            'largest_win': self.largest_win,
            'largest_loss': self.largest_loss,
            'strategy_name': self.strategy_name,
            'backtest_duration': self.backtest_duration
        }

# ---------------------------------------------------------------------------
# Backtesting Engine
# ---------------------------------------------------------------------------

class BacktestEngine:
    def __init__(
        self,
        initial_capital: float = 10000.0,
        trading_fee: float = 0.001,  # 0.1%
        position_size: float = 0.1,   # 10% per trade
        max_positions: int = 1,
        time_budget: float = 300.0    # 5 minutes
    ):
        self.initial_capital = initial_capital
        self.trading_fee = trading_fee
        self.position_size = position_size
        self.max_positions = max_positions
        self.time_budget = time_budget
        
        # State
        self.capital = initial_capital
        self.positions: List[Position] = []
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = [initial_capital]
        self.timestamps: List[pd.Timestamp] = []
        
    def evaluate_strategy(
        self,
        strategy_module,
        data: pd.DataFrame,
        data_type: str = 'val'  # 'train', 'val', or 'test'
    ) -> BacktestResult:
        """
        Evaluate a trading strategy on the given data within time budget.
        
        Args:
            strategy_module: Imported strategy module with generate_signals()
            data: DataFrame with price data and indicators
            data_type: Type of data for reporting
            
        Returns:
            BacktestResult with performance metrics
        """
        start_time = time.time()
        
        # Reset state
        self._reset_state()
        
        # Get strategy parameters
        strategy_name = getattr(strategy_module, 'STRATEGY_NAME', 'Unknown')
        parameters = getattr(strategy_module, 'PARAMETERS', {})
        
        # Run backtest
        for i in range(len(data)):
            # Check time budget
            if time.time() - start_time > self.time_budget:
                print(f"Time budget exceeded ({self.time_budget}s), stopping early")
                break
            
            current_row = data.iloc[i]
            current_time = data.index[i]
            
            # Update existing positions
            self._update_positions(current_row['close'])
            
            # Generate trading signal
            signal = strategy_module.generate_signals(
                current_row,
                self.positions,
                self.capital
            )
            
            # Execute trade if signal received
            if signal.action != TradeAction.HOLD:
                self._execute_trade(signal, current_row, current_time)
            
            # Record equity
            total_value = self.capital + sum(
                pos.current_value for pos in self.positions
            )
            self.equity_curve.append(total_value)
            self.timestamps.append(current_time)
        
        # Close all positions at end
        self._close_all_positions(data.iloc[-1]['close'], data.index[-1])
        
        # Calculate metrics
        result = self._calculate_metrics(
            strategy_name,
            parameters,
            time.time() - start_time
        )
        
        return result
    
    def _reset_state(self):
        """Reset backtesting engine to initial state."""
        self.capital = self.initial_capital
        self.positions.clear()
        self.trades.clear()
        self.equity_curve = [self.initial_capital]
        self.timestamps.clear()
    
    def _update_positions(self, current_price: float):
        """Update all open positions with current price."""
        for position in self.positions:
            position.current_value = position.quantity * current_price
            position.pnl = position.current_value - (position.quantity * position.entry_price)
            position.pnl_pct = position.pnl / (position.quantity * position.entry_price)
    
    def _execute_trade(self, signal, row: pd.Series, timestamp: pd.Timestamp):
        """Execute a trade based on signal."""
        current_price = row['close']
        
        if signal.action == TradeAction.BUY:
            # Calculate position size
            trade_amount = self.capital * self.position_size
            if trade_amount < 10:  # Minimum trade size
                return
            
            # Calculate quantity (accounting for fee)
            fee = trade_amount * self.trading_fee
            net_amount = trade_amount - fee
            quantity = net_amount / current_price
            
            # Check if we can open new position
            if len(self.positions) >= self.max_positions:
                return
            
            # Open position
            position = Position(
                entry_price=current_price,
                entry_time=timestamp,
                quantity=quantity
            )
            self.positions.append(position)
            self.capital -= trade_amount
            
            # Record trade
            trade = Trade(
                timestamp=timestamp,
                action=TradeAction.BUY,
                price=current_price,
                quantity=quantity,
                fee=fee,
                reason=signal.reason
            )
            self.trades.append(trade)
            
        elif signal.action == TradeAction.SELL:
            # Close all positions
            for position in self.positions:
                # Calculate proceeds
                proceeds = position.quantity * current_price
                fee = proceeds * self.trading_fee
                net_proceeds = proceeds - fee
                
                # Update capital
                self.capital += net_proceeds
                
                # Record trade
                trade = Trade(
                    timestamp=timestamp,
                    action=TradeAction.SELL,
                    price=current_price,
                    quantity=position.quantity,
                    fee=fee,
                    reason=signal.reason
                )
                self.trades.append(trade)
            
            # Clear positions
            self.positions.clear()
    
    def _close_all_positions(self, current_price: float, timestamp: pd.Timestamp):
        """Close all open positions at given price."""
        for position in self.positions:
            proceeds = position.quantity * current_price
            fee = proceeds * self.trading_fee
            net_proceeds = proceeds - fee
            
            self.capital += net_proceeds
            
            trade = Trade(
                timestamp=timestamp,
                action=TradeAction.SELL,
                price=current_price,
                quantity=position.quantity,
                fee=fee,
                reason="End of backtest"
            )
            self.trades.append(trade)
        
        self.positions.clear()
    
    def _calculate_metrics(
        self,
        strategy_name: str,
        parameters: Dict[str, Any],
        duration: float
    ) -> BacktestResult:
        """Calculate all performance metrics from trades and equity curve."""
        
        # Extract trade P&L
        trade_pnl = []
        trade_returns = []
        holding_periods = []
        
        # Group trades into round trips (buy-sell pairs)
        i = 0
        while i < len(self.trades):
            if (i + 1 < len(self.trades) and 
                self.trades[i].action == TradeAction.BUY and
                self.trades[i + 1].action == TradeAction.SELL):
                
                buy_trade = self.trades[i]
                sell_trade = self.trades[i + 1]
                
                # Calculate P&L
                buy_cost = buy_trade.price * buy_trade.quantity + buy_trade.fee
                sell_proceeds = sell_trade.price * sell_trade.quantity - sell_trade.fee
                pnl = sell_proceeds - buy_cost
                return_pct = pnl / buy_cost
                
                trade_pnl.append(pnl)
                trade_returns.append(return_pct)
                
                # Calculate holding period (in periods/rows)
                holding_period = (sell_trade.timestamp - buy_trade.timestamp).total_seconds() / (4 * 3600)  # 4-hour periods
                holding_periods.append(holding_period)
                
                i += 2
            else:
                i += 1
        
        # Calculate metrics
        if not trade_pnl:
            # No trades made
            return BacktestResult(
                total_return=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                profit_factor=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                expectancy=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                volatility=0.0,
                downside_volatility=0.0,
                calmar_ratio=0.0,
                ulcer_index=0.0,
                avg_holding_period=0.0,
                profit_per_trade=0.0,
                largest_win=0.0,
                largest_loss=0.0,
                strategy_name=strategy_name,
                parameters=parameters,
                backtest_duration=duration
            )
        
        # Basic metrics
        total_trades = len(trade_pnl)
        winning_trades = sum(1 for pnl in trade_pnl if pnl > 0)
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        # P&L metrics
        winning_pnl = [pnl for pnl in trade_pnl if pnl > 0]
        losing_pnl = [pnl for pnl in trade_pnl if pnl < 0]
        
        avg_win = np.mean(winning_pnl) if winning_pnl else 0.0
        avg_loss = np.mean(losing_pnl) if losing_pnl else 0.0
        largest_win = max(winning_pnl) if winning_pnl else 0.0
        largest_loss = min(losing_pnl) if losing_pnl else 0.0
        
        # Profit factor
        gross_profit = sum(winning_pnl)
        gross_loss = abs(sum(losing_pnl))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Expectancy
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
        
        # Equity curve metrics
        equity_array = np.array(self.equity_curve)
        returns = np.diff(equity_array) / equity_array[:-1]
        
        total_return = (equity_array[-1] - equity_array[0]) / equity_array[0]
        
        # Sharpe ratio (assuming 0% risk-free rate)
        if len(returns) > 1 and np.std(returns) > 0:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(365 * 6)  # Annualized for 4-hour periods
        else:
            sharpe_ratio = 0.0
        
        # Sortino ratio
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 1 and np.std(downside_returns) > 0:
            sortino_ratio = np.mean(returns) / np.std(downside_returns) * np.sqrt(365 * 6)
        else:
            sortino_ratio = 0.0
        
        # Maximum drawdown
        peak = equity_array[0]
        max_drawdown = 0.0
        for value in equity_array:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Calmar ratio
        calmar_ratio = total_return / max_drawdown if max_drawdown > 0 else 0.0
        
        # Ulcer index
        drawdowns = []
        peak = equity_array[0]
        for value in equity_array:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            drawdowns.append(drawdown)
        ulcer_index = np.sqrt(np.mean(np.array(drawdowns) ** 2))
        
        # Volatility
        volatility = np.std(returns) * np.sqrt(365 * 6) if len(returns) > 1 else 0.0
        downside_volatility = np.std(downside_returns) * np.sqrt(365 * 6) if len(downside_returns) > 1 else 0.0
        
        # Other metrics
        avg_holding_period = np.mean(holding_periods) if holding_periods else 0.0
        profit_per_trade = np.mean(trade_pnl) if trade_pnl else 0.0
        
        return BacktestResult(
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            expectancy=expectancy,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            volatility=volatility,
            downside_volatility=downside_volatility,
            calmar_ratio=calmar_ratio,
            ulcer_index=ulcer_index,
            avg_holding_period=avg_holding_period,
            profit_per_trade=profit_per_trade,
            largest_win=largest_win,
            largest_loss=largest_loss,
            strategy_name=strategy_name,
            parameters=parameters,
            backtest_duration=duration
        )

# ---------------------------------------------------------------------------
# Signal Dataclass
# ---------------------------------------------------------------------------

@dataclass
class TradingSignal:
    action: TradeAction
    reason: str = ""
    confidence: float = 1.0

# ---------------------------------------------------------------------------
# Main Function
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Backtest trading strategies')
    parser.add_argument('--strategy', type=str, help='Path to strategy module')
    parser.add_argument('--data', type=str, help='Path to data splits pickle file')
    parser.add_argument('--test', action='store_true', help='Run test with sample strategy')
    parser.add_argument('--time-budget', type=float, default=300.0, help='Time budget in seconds')
    args = parser.parse_args()
    
    if args.test:
        print("Running backtest test...")
        _run_test()
