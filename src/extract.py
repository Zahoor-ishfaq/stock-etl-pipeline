import requests
import pandas as pd
from config import ALPHA_VANTAGE_API_KEY
import time

def extract_stock_data(symbol):
    """Extract daily stock data from Alpha Vantage API"""
    url = f'https://www.alphavantage.co/query'
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': symbol,
        'apikey': ALPHA_VANTAGE_API_KEY,
        'outputsize': 'compact'  # Last 100 days
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'Time Series (Daily)' not in data:
            print(f"Error for {symbol}: {data.get('Note', 'Unknown error')}")
            return None
            
        time_series = data['Time Series (Daily)']
        
        # Convert to list of dictionaries
        records = []
        for date, values in time_series.items():
            records.append({
                'symbol': symbol,
                'date': date,
                'open': float(values['1. open']),
                'high': float(values['2. high']),
                'low': float(values['3. low']),
                'close': float(values['4. close']),
                'volume': int(values['5. volume'])
            })
        
        return pd.DataFrame(records)
    
    except Exception as e:
        print(f"Error extracting {symbol}: {str(e)}")
        return None

def extract_all_stocks(symbols):
    """Extract data for multiple stocks with rate limiting"""
    all_data = []
    
    for symbol in symbols:
        print(f"Extracting {symbol}...")
        df = extract_stock_data(symbol)
        if df is not None:
            all_data.append(df)
        time.sleep(15)  # Rate limit: 4 calls/min = 15 sec between calls
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()