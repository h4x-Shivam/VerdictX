import requests

try:
    requests.post('http://localhost:11434')
except Exception as e:
    print('STR:', str(e))
