import unittest
import pandas as pd
import numpy as np
from indicators.ichimoku import calculate_ichimoku

class TestIchimoku(unittest.TestCase):
    def test_basic_calculation(self):
        data = pd.DataFrame({
            'open': [40000] * 100,
            'high': [41000] * 100,
            'low': [39000] * 100,
            'close': [40000] * 100,
            'volume': [1000] * 100
        })
        
        result = calculate_ichimoku(data)
        
        self.assertIn('ichimoku_tenkan', result.columns)
        self.assertIn('ichimoku_kijun', result.columns)
        self.assertIn('price_above_cloud', result.columns)

if __name__ == '__main__':
    unittest.main()
