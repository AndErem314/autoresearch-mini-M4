class RiskManager:
    def __init__(self, stop_loss=5.0, take_profit=10.0, position_size=10.0):
        self.stop_loss_pct = stop_loss
        self.take_profit_pct = take_profit
        self.position_size_pct = position_size
    
    def calculate_position(self, capital, price):
        """Calculate position size based on risk parameters."""
        position_value = capital * (self.position_size_pct / 100)
        return position_value / price
    
    def check_exit_conditions(self, entry_price, current_price):
        """Check if stop loss or take profit is triggered."""
        change_pct = (current_price - entry_price) / entry_price * 100
        
        if change_pct <= -self.stop_loss_pct:
            return 'stop_loss'
        elif change_pct >= self.take_profit_pct:
            return 'take_profit'
        
        return None
    
    def calculate_trailing_stop(self, highest_price, trail_pct=3.0):
        """Calculate trailing stop price."""
        return highest_price * (1 - trail_pct / 100)
