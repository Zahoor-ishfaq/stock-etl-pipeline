import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
from sqlalchemy import create_engine, text
from config import DATABASE_URL
import pandas as pd

def load_to_database(df):
    """Load transformed data to PostgreSQL with upsert logic"""
    if df.empty:
        print("⚠️  No data to load")
        return
    
    try:
        engine = create_engine(DATABASE_URL)
        
        print(f"📊 Attempting to load {len(df)} records...")
        
        # Prepare data - only columns in schema
        df_to_load = df[['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']].copy()
        
        # Insert records one by one with conflict handling
        loaded_count = 0
        skipped_count = 0
        
        with engine.connect() as conn:
            for _, row in df_to_load.iterrows():
                try:
                    # Try to insert, skip if duplicate
                    query = text("""
                        INSERT INTO stock_data (symbol, date, open, high, low, close, volume)
                        VALUES (:symbol, :date, :open, :high, :low, :close, :volume)
                        ON CONFLICT (symbol, date) DO NOTHING
                    """)
                    
                    conn.execute(query, {
                        'symbol': row['symbol'],
                        'date': row['date'],
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'close': float(row['close']),
                        'volume': int(row['volume'])
                    })
                    conn.commit()
                    loaded_count += 1
                    
                except Exception as e:
                    skipped_count += 1
                    continue
        
        print(f"✓ Loaded {loaded_count} new records")
        if skipped_count > 0:
            print(f"⚠️  Skipped {skipped_count} duplicate records")
        
    except Exception as e:
        print(f"❌ Error loading to database: {str(e)}")