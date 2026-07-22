import traceback
from main import get_basic_data

try:
    data = get_basic_data('ITC')
    print("SUCCESS")
except Exception as e:
    traceback.print_exc()
