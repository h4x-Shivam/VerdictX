import requests
import yfinance as yf
from bs4 import BeautifulSoup
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate"
}

# ─────────────────────────────
# CLEAN VALUE
# ─────────────────────────────
def clean_value(val):
    if not val:
        return None

    # Extract all digits, commas, and dots
    val_str = str(val).replace(",", "").replace("₹", "").strip()
    
    # Handle multipliers
    multiplier = 1
    if "Cr" in val_str:
        multiplier = 1e7
    elif "Lakh" in val_str:
        multiplier = 1e5
        
    # Extract only the numeric part (e.g., from '1277386\n    \n   .')
    import re
    match = re.search(r'([0-9]*\.?[0-9]+)', val_str)
    if not match:
        return None
        
    try:
        return float(match.group(1)) * multiplier
    except:
        return None


# ─────────────────────────────
# NSE FETCH
# ─────────────────────────────
def fetch_nse(symbol):
    url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"

    try:
        s = requests.Session()
        s.get("https://www.nseindia.com", headers=HEADERS)
        r = s.get(url, headers=HEADERS)
        data = r.json()

        return {
            "price": data["priceInfo"]["lastPrice"],
            "sector": data.get("industryInfo", {}).get("industry"),
            "company": data.get("info", {}).get("companyName"),
        }
    except:
        return {}


# ─────────────────────────────
# YFINANCE FETCH
# ─────────────────────────────
def fetch_yf(ticker):
    try:
        info = yf.Ticker(ticker).info
        return {
            "pe": info.get("trailingPE"),
            "pb": info.get("priceToBook"),
            "roe": info.get("returnOnEquity"),
            "margin": info.get("profitMargins"),
            "growth": info.get("revenueGrowth"),
            "debt": info.get("debtToEquity"),
            "market_cap": info.get("marketCap"),
        }
    except:
        return {}


# ─────────────────────────────
# SCREENER FETCH (FIXED)
# ─────────────────────────────
def generate_slug(name):
    name = name.lower()
    name = re.sub(r"(ltd|limited|pvt|private|inc|corp)", "", name)
    name = re.sub(r"[^a-z0-9]", "", name)
    return name.strip()


def fetch_screener(symbol):
    # Screener.in uses the NSE/BSE symbol in the URL (e.g., TCS, HDFCBANK)
    url = f"https://www.screener.in/company/{symbol.upper()}/consolidated/"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        data = {}

        for li in soup.select("ul#top-ratios li"):
            name = li.select_one(".name")
            val = li.select_one(".value")

            if name and val:
                data[name.text.strip().lower()] = clean_value(val.text)

        return data

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {}


# ─────────────────────────────
# NORMALIZE
# ─────────────────────────────
def normalize(nse, yf, scr):
    return {
        "price": nse.get("price") or scr.get("current price"),

        "pe": scr.get("stock p/e") or yf.get("pe"),
        "pb": scr.get("price to book value") or yf.get("pb"),

        "roe": scr.get("return on equity") or yf.get("roe"),
        "margin": scr.get("net profit margin") or yf.get("margin"),

        "growth": scr.get("sales growth") or yf.get("growth"),
        "debt": scr.get("debt to equity") or yf.get("debt"),

        "market_cap": scr.get("market cap") or yf.get("market_cap"),
        "dividend_yield": scr.get("dividend yield") or yf.get("dividend_yield"),
    }


# ─────────────────────────────
# VALIDATE
# ─────────────────────────────
def validate(data):
    clean = {}

    for k, v in data.items():
        if v is None:
            continue

        try:
            v = float(v)
        except:
            continue

        if k == "pe" and (v <= 0 or v > 200):
            continue
        if k == "roe" and (v < -50 or v > 100):
            continue
        if k == "debt" and v > 500:
            continue
        if k == "market_cap" and v < 0:
            continue
        if k == "dividend_yield" and (v < 0 or v > 500):
            continue

        clean[k] = v

    return clean


# ─────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────
def get_clean_stock_data(symbol):
    nse = fetch_nse(symbol)
    yf  = fetch_yf(symbol + ".NS")
    # Always use the symbol for Screener, not the company name
    scr = fetch_screener(symbol)

    norm = normalize(nse, yf, scr)
    clean = validate(norm)

    completeness = round(len(clean) / 7, 2)

    return {
        "data": clean,
        "completeness": completeness
    }