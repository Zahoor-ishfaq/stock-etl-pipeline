import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
# Get database URL from Streamlit secrets or environment
try:
    DATABASE_URL = st.secrets["DATABASE_URL"]
except (KeyError, FileNotFoundError):
    # Fallback to .env for local development
    from dotenv import load_dotenv
    load_dotenv()
    DATABASE_URL = os.getenv('DATABASE_URL')

# Page config
st.set_page_config(
    page_title="Stock ETL Dashboard",
    page_icon="📈",
    layout="wide"
)

# Title
st.title("📈 Stock Market ETL Pipeline Dashboard")
st.markdown("Real-time stock data from Alpha Vantage API")

# Database connection
@st.cache_resource
def get_engine():
    return create_engine(DATABASE_URL)

# Load data
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data():
    engine = get_engine()
    query = """
    SELECT symbol, date, open, high, low, close, volume
    FROM stock_data
    ORDER BY date DESC, symbol
    """
    df = pd.read_sql(query, engine)
    df['date'] = pd.to_datetime(df['date'])
    return df

# Load data
try:
    df = load_data()
    
    if df.empty:
        st.warning("⚠️ No data found in database. Run the ETL pipeline first!")
        st.stop()
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    symbols = df['symbol'].unique()
    selected_symbol = st.sidebar.selectbox("Select Stock", symbols)
    
    # Filter data
    symbol_df = df[df['symbol'] == selected_symbol].sort_values('date')
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    latest = symbol_df.iloc[0]
    previous = symbol_df.iloc[1] if len(symbol_df) > 1 else latest
    
    price_change = latest['close'] - previous['close']
    price_change_pct = (price_change / previous['close']) * 100
    
    with col1:
        st.metric(
            "Latest Close Price",
            f"${latest['close']:.2f}",
            f"{price_change:+.2f} ({price_change_pct:+.2f}%)"
        )
    
    with col2:
        st.metric("High", f"${latest['high']:.2f}")
    
    with col3:
        st.metric("Low", f"${latest['low']:.2f}")
    
    with col4:
        st.metric("Volume", f"{latest['volume']:,}")
    
    # Price chart
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
    
    fig_volume = px.bar(
        symbol_df,
        x='date',
        y='volume',
        title=f"{selected_symbol} Trading Volume"
    )
    
    fig_volume.update_layout(height=300)
    st.plotly_chart(fig_volume, use_container_width=True)
    
    # All stocks comparison
    st.subheader("All Stocks Comparison (Latest Close Price)")
    
    latest_prices = df.groupby('symbol').first().reset_index()
    
    fig_comparison = px.bar(
        latest_prices,
        x='symbol',
        y='close',
        color='symbol',
        title="Latest Close Prices"
    )
    
    st.plotly_chart(fig_comparison, use_container_width=True)
    
    # Raw data
    with st.expander("📊 View Raw Data"):
        st.dataframe(symbol_df, use_container_width=True)
    
    # Pipeline info
    st.sidebar.markdown("---")
    st.sidebar.subheader("Pipeline Info")
    st.sidebar.info(f"""
    **Total Records:** {len(df)}
    
    **Stocks Tracked:** {', '.join(symbols)}
    
    **Last Updated:** {df['date'].max().strftime('%Y-%m-%d')}
    """)

except Exception as e:
    st.error(f"❌ Error connecting to database: {str(e)}")
    st.info("Make sure your .env file has the correct DATABASE_URL")