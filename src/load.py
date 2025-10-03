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
        # ✅ Add connect_args for Supabase pooler
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            connect_args={
                'connect_timeout': 10,
                'options': '-c statement_timeout=30000'
            }
        )
        
        print(f"📊 Attempting to load {len(df)} records...")
        
        # Prepare data
        df_to_load = df[['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']].copy()
        
        # Use begin() for proper transaction
        with engine.begin() as conn:
            for _, row in df_to_load.iterrows():
                try:
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
                    
                except Exception as e:
                    print(f"⚠️  Error with row: {e}")
                    continue
        
        print(f"✓ Data loaded successfully")
        engine.dispose()
        
    except Exception as e:
        print(f"❌ Error loading to database: {str(e)}")
        raise