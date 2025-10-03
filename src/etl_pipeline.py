import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

import extract
import transform
import load
import config
from alerts import send_alert
from datetime import datetime
def run_etl_pipeline():
    """Run the complete ETL pipeline with email alerts"""
    
    try:
        print(f"\n{'='*50}")
        print(f"Starting ETL Pipeline - {datetime.now()}")
        print(f"{'='*50}\n")
        
        # EXTRACT
        print("📥 EXTRACTING data from Alpha Vantage...")
        raw_data = extract.extract_all_stocks(config.SYMBOLS)
        
        if raw_data.empty:
            error_msg = "No data extracted from API. Check API limits or connection."
            print(f"❌ {error_msg}")
            send_alert("ETL Pipeline Warning", error_msg, is_error=True)
            return
        
        print(f"✓ Extracted {len(raw_data)} records\n")
        
        # TRANSFORM
        print("⚙️  TRANSFORMING data...")
        transformed_data = transform.transform_stock_data(raw_data)
        print(f"✓ Transformed {len(transformed_data)} records\n")
        
        # LOAD
        print("📤 LOADING data to database...")
        load.load_to_database(transformed_data)
        
        print(f"\n{'='*50}")
        print("✅ ETL Pipeline Completed Successfully")
        print(f"{'='*50}\n")
        
        # Success email
        send_alert(
            "ETL Pipeline Success",
            f"Successfully processed {len(transformed_data)} records for stocks: {', '.join(config.SYMBOLS)}\n\nTotal records loaded: {len(transformed_data)}"
        )
        
    except Exception as e:
        error_msg = f"Pipeline failed with error: {str(e)}"
        print(f"❌ {error_msg}")
        send_alert("ETL Pipeline Failed", error_msg, is_error=True)
        raise

if __name__ == "__main__":
    run_etl_pipeline()