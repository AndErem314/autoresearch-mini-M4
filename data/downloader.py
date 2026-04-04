import pandas as pd
from binance.client import Client

def download_btc_data(start_date, end_date, interval='4h'):
    """Download BTC/USDT data from Binance."""
    client = Client()
    
    # Convert dates to timestamps
    start_ts = int(pd.to_datetime(start_date).timestamp() * 1000)
    end_ts = int(pd.to_datetime(end_date).timestamp() * 1000)
    
    # Download klines
    klines = client.get_klines(
        symbol='BTCUSDT',
        interval=Client.KLINE_INTERVAL_4HOUR,
        startTime=start_ts,
        endTime=end_ts,
        limit=1000
    )
    
    # Convert to DataFrame
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades',
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])
    
    # Convert types
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col])
    
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    
    return df[['open', 'high', 'low', 'close', 'volume']]
