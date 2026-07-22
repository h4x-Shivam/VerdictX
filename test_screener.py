from data_pipeline import fetch_screener
import traceback

try:
    data = fetch_screener('HDFCBANK')
    print("DATA:")
    print(data)
except Exception as e:
    print("EXCEPTION:")
    traceback.print_exc()
