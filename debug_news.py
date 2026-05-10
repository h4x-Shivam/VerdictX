import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from main import get_news, _rss_fetch, _build_name_variants

ticker = "COALINDIA"
company = "Coal India"

# Test raw RSS first
print("=== Raw RSS test ===")
raw = _rss_fetch(f"{ticker} site:moneycontrol.com", limit=4)
print(f"moneycontrol raw: {len(raw)} items")
for r in raw[:2]:
    print(f"  {r['title'][:80]}")

raw2 = _rss_fetch(f"{ticker} NSE stock India", limit=6)
print(f"general raw: {len(raw2)} items")
for r in raw2[:2]:
    print(f"  {r['title'][:80]}")

# Test variant matching
variants = _build_name_variants(company, ticker)
print(f"\nVariants: {variants}")

# Test full pipeline
print("\n=== Full get_news ===")
news = get_news(company, ticker)
print(f"Total relevant: {len(news)}")
for n in news[:5]:
    print(f"  [{n['source']}] {n['title'][:80]}")
