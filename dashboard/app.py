import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from sqlalchemy import create_engine, text
import os
import requests
from datetime import datetime

# Get database URL from Streamlit secrets or environment
try:
    DATABASE_URL = st.secrets["DATABASE_URL"]
    ALPHA_VANTAGE_API_KEY = st.secrets["ALPHA_VANTAGE_API_KEY"]
except (KeyError, FileNotFoundError):
    from dotenv import load_dotenv
    load_dotenv()
    DATABASE_URL = os.getenv('DATABASE_URL')
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

# Page config
st.set_page_config(
    page_title="Stock ETL Dashboard",
    page_icon="📈",
    layout="wide"
)

# Title
st.title("📈 Stock Market Dashboard")

# Database connection
@st.cache_resource
def get_engine():
    return create_engine(DATABASE_URL)

# Data source selection
data_source = st.sidebar.radio(
    "Data Source:",
    ["Historical Data (Database)", "Live Data (API)"]
)

st.sidebar.markdown("---")

# HISTORICAL DATA FROM DATABASE
if data_source == "Historical Data (Database)":
    st.markdown("**Source:** PostgreSQL Database (Historical Records)")
    
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def load_historical_data():
        engine = get_engine()
        query = """
        SELECT symbol, date, open, high, low, close, volume
        FROM stock_data
        ORDER BY date DESC, symbol
        """
        df = pd.read_sql(query, engine)
        df['date'] = pd.to_datetime(df['date'])
        return df
    
    try:
        df = load_historical_data()
        
        if df.empty:
            st.warning("⚠️ No data in database. Run ETL pipeline first!")
            st.stop()
        
        # Filters
        st.sidebar.header("Filters")
        symbols = df['symbol'].unique()
        selected_symbol = st.sidebar.selectbox("Select Stock", symbols)
        
        # Date range filter
        min_date = df['date'].min().date()
        max_date = df['date'].max().date()
        date_range = st.sidebar.date_input(
            "Date Range:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Filter data
        symbol_df = df[df['symbol'] == selected_symbol].sort_values('date')
        
        if len(date_range) == 2:
            mask = (symbol_df['date'].dt.date >= date_range[0]) & (symbol_df['date'].dt.date <= date_range[1])
            symbol_df = symbol_df[mask]
        
        if symbol_df.empty:
            st.warning("No data for selected filters")
            st.stop()
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        latest = symbol_df.iloc[-1]
        first = symbol_df.iloc[0]
        
        period_change = latest['close'] - first['close']
        period_change_pct = (period_change / first['close']) * 100
        
        with col1:
            st.metric(
                "Latest Close",
                f"${latest['close']:.2f}",
                f"{period_change:+.2f} ({period_change_pct:+.2f}%)"
            )
        
        with col2:
            st.metric("Period High", f"${symbol_df['high'].max():.2f}")
        
        with col3:
            st.metric("Period Low", f"${symbol_df['low'].min():.2f}")
        
        with col4:
            st.metric("Avg Volume", f"{symbol_df['volume'].mean():,.0f}")
        
        # Charts (your existing code)
        st.subheader(f"{selected_symbol} Price History")
        
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=symbol_df['date'],
            open=symbol_df['open'],
            high=symbol_df['high'],
            low=symbol_df['low'],
            close=symbol_df['close'],
            name=selected_symbol
        ))
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Price (USD)",
            height=500,
            xaxis_rangeslider_visible=False
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Volume chart
        st.subheader("Trading Volume")
        fig_volume = px.bar(symbol_df, x='date', y='volume')
        fig_volume.update_layout(height=300)
        st.plotly_chart(fig_volume, use_container_width=True)
        
        # Raw data
        with st.expander("📊 View Raw Data"):
            st.dataframe(symbol_df, use_container_width=True)
        
        # Info
        st.sidebar.markdown("---")
        st.sidebar.subheader("Database Info")
        st.sidebar.info(f"""
        **Total Records:** {len(df)}
        **Stocks:** {', '.join(symbols)}
        **Date Range:** {min_date} to {max_date}
        """)
    
    except Exception as e:
        st.error(f"❌ Database error: {str(e)}")

# LIVE DATA FROM API
else:
    st.markdown("**Source:** Alpha Vantage API (Live/Recent Data)")
    
    @st.cache_data(ttl=300)
    def get_live_data(symbol):
        url = 'https://www.alphavantage.co/query'
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'apikey': ALPHA_VANTAGE_API_KEY,
            'outputsize': 'compact'
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'Time Series (Daily)' not in data:
                return None, data.get('Note', data.get('Error Message', 'Unknown error'))
            
            time_series = data['Time Series (Daily)']
            records = []
            for date, values in time_series.items():
                records.append({
                    'date': pd.to_datetime(date),
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'close': float(values['4. close']),
                    'volume': int(values['5. volume'])
                })
            
            df = pd.DataFrame(records).sort_values('date')
            return df, None
            
        except Exception as e:
            return None, str(e)
    
    # Get available symbols from database
    @st.cache_data(ttl=3600)
    def get_available_symbols():
        try:
            engine = get_engine()
            query = "SELECT DISTINCT symbol FROM stock_data ORDER BY symbol"
            result = pd.read_sql(query, engine)
            return result['symbol'].tolist()
        except:
            return ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']  # Fallback list
    
    # Stock selection
    st.sidebar.header("Stock Selection")
    available_symbols = get_available_symbols()
    selected_symbol = st.sidebar.selectbox("Select Stock:", available_symbols)
    
    with st.spinner(f'Fetching live data for {selected_symbol}...'):
        df, error = get_live_data(selected_symbol)
        
        if error:
            st.error(f"Error: {error}")
            st.info("Try again in a moment. API may have rate limits.")
            st.stop()
        
        if df is None or df.empty:
            st.warning("No data returned")
            st.stop()
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        latest = df.iloc[-1]
        previous = df.iloc[-2] if len(df) > 1 else latest
        
        price_change = latest['close'] - previous['close']
        price_change_pct = (price_change / previous['close']) * 100
        
        with col1:
            st.metric(
                "Current Price",
                f"${latest['close']:.2f}",
                f"{price_change:+.2f} ({price_change_pct:+.2f}%)"
            )
        
        with col2:
            st.metric("Today's High", f"${latest['high']:.2f}")
        
        with col3:
            st.metric("Today's Low", f"${latest['low']:.2f}")
        
        with col4:
            st.metric("Volume", f"{latest['volume']:,}")
        
        # Price chart
        st.subheader(f"{selected_symbol} Recent Price History (Live)")
        
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name=selected_symbol
        ))
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Price (USD)",
            height=500,
            xaxis_rangeslider_visible=False
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Raw data
        with st.expander("View Raw Data"):
            st.dataframe(df.sort_values('date', ascending=False), use_container_width=True)
        
        st.sidebar.info(f"""
        **Symbol:** {selected_symbol}
        **Records:** {len(df)}
        **Latest:** {latest['date'].strftime('%Y-%m-%d')}
        **Cached for:** 5 minutes
        """)