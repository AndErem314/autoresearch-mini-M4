import pandas as pd
import numpy as np

class BacktestEngine:
    def __init__(self, initial_capital=10000.0, fee=0.001):
        self.initial_capital = initial_capital
        self.fee = fee
        self.reset()
    
    def reset(self):
        self.capital = self.initial_capital
        self.position = 0.0
        self.trades = []
        self.equity = []
    
    def run(self, data, strategy):
        self.reset()
        
        for i in range(len(data)):
            price = data.iloc[i]['close']
            signal = strategy.generate_signal(data.iloc[:i+1])
            
            if signal == 1 and self.position == 0:
                # Buy
                self.position = self.capital * 0.1 / price
                self.capital -= self.position * price * (1 + self.fee)
                self.trades.append({'action': 'buy', 'price': price})
            elif signal == -1 and self.position > 0:
                # Sell
                self.capital += self.position * price * (1 - self.fee)
                self.trades.append({'action': 'sell', 'price': price})
                self.position = 0.0
            
            # Record equity
            current_equity = self.capital + self.position * price
            self.equity.append(current_equity)
        
        return self.calculate_metrics()
    
    def calculate_metrics(self):
        if not self.equity:
            return {}
        
        equity_series = pd.Series(self.equity)
        returns = equity_series.pct_change().dropna()
        
        metrics = {
            'total_return': (equity_series.iloc[-1] / equity_series.iloc[0] - 1) * 100,
            'sharpe_ratio': returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0,
            'max_drawdown': self.calculate_drawdown(equity_series),
            'num_trades': len(self.trades) // 2,
            'win_rate': self.calculate_win_rate()
        }
        
        return metrics
    
    def calculate_drawdown(self, equity):
        rolling_max = equity.expanding().max()
        drawdown = (equity - rolling_max) / rolling_max
        return drawdown.min() * 100
    
    def calculate_win_rate(self):
        if len(self.trades) < 2:
            return 0.0
        
        wins = 0
        for i in range(0, len(self.trades) - 1, 2):
            if self.trades[i+1]['price'] > self.trades[i]['price']:
                wins += 1
        
        return wins / (len(self.trades) // 2) * 100
