import pandas as pd

def transform_stock_data(df):
    """Clean and transform stock data"""
    if df.empty:
        return df
    
    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Remove duplicates
    df = df.drop_duplicates(subset=['symbol', 'date'])
    
    # Sort by symbol and date
    df = df.sort_values(['symbol', 'date'], ascending=[True, False])
    
    # Add calculated columns
    df['daily_return'] = df.groupby('symbol')['close'].pct_change() * 100
    df['price_range'] = df['high'] - df['low']
    df['avg_price'] = (df['high'] + df['low']) / 2
    
    # Remove nulls in calculated columns (first row per symbol)
    df['daily_return'] = df['daily_return'].fillna(0)
    
    # Round decimal places
    df['daily_return'] = df['daily_return'].round(2)
    df['price_range'] = df['price_range'].round(2)
    df['avg_price'] = df['avg_price'].round(2)
    
    return df