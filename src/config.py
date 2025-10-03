import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']  # Stocks to track

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL')  # PostgreSQL connection string