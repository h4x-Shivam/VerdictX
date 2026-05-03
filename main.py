import io
import json
import os
import re
import time
from dotenv import load_dotenv
from datetime import datetime, timedelta
from data_pipeline import get_clean_stock_data

import feedparser
import requests
import yfinance as yf

try:
    from config import RAPIDAPI_KEY
except ImportError:
    RAPIDAPI_KEY = ""


# ─────────────────────────────────────────────────────────────────
# Formatting helpers — ASCII-safe, no Unicode that can mangle
# ─────────────────────────────────────────────────────────────────

RUPEE = "\u20b9"  # ₹ — define once, use everywhere


def fmt_rupee(v):
    if v is None:
        return "N/A"
    try:
        return f"{RUPEE}{float(v):,.2f}"
    except Exception:
        return str(v)


def fmt_cr(v):
    """Convert raw value to Indian Crore notation."""
    if v is None:
        return "N/A"
    try:
        cr = float(v) / 1e7
        if cr >= 1e5:
            return f"{RUPEE}{cr / 1e5:.2f} Lakh Cr"
        if cr >= 1e3:
            return f"{RUPEE}{cr / 1e3:.1f}K Cr"
        return f"{RUPEE}{cr:.1f} Cr"
    except Exception:
        return str(v)


def fmt_pct(v):
    if v is None:
        return "N/A"
    try:
        return f"{float(v) * 100:.2f}%"
    except Exception:
        return str(v)


def safe_html(s: str) -> str:
    """Escape a string for safe embedding in HTML attributes/text."""
    if not s:
        return ""
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


# ─────────────────────────────────────────────────────────────────
# LLM utilities
# ─────────────────────────────────────────────────────────────────

import os
import json
import re
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "nvidia")  # "nvidia" or "ollama"

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_MODEL   = "meta/llama-3.1-70b-instruct"

OLLAMA_MODEL   = "mistral"
OLLAMA_URL     = "http://localhost:11434/api/chat"

# ─────────────────────────────────────────────
# JSON extractor (keep your original logic)
# ─────────────────────────────────────────────

def _extract_json(text: str) -> dict:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    else:
        raw_obj = re.search(r"\{.*\}", text, re.DOTALL)
        if raw_obj:
            text = raw_obj.group()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        return {"_parse_error": str(e), "_raw": text[:400]}


# ─────────────────────────────────────────────
# NVIDIA CALL (Kimi)
# ─────────────────────────────────────────────

def _call_nvidia(messages):
    url = "https://integrate.api.nvidia.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        url,
        headers=headers,
        json={
            "model": NVIDIA_MODEL,
            "messages": messages,
            "temperature": 0.3
        },
        timeout=120
    )

    data = response.json()

    return data["choices"][0]["message"]["content"]


# ─────────────────────────────────────────────
# OLLAMA CALL (fallback)
# ─────────────────────────────────────────────

def _call_ollama(messages):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False
        },
        timeout=300
    )

    data = response.json()
    return data["message"]["content"]


# ─────────────────────────────────────────────
# MAIN LLM CALL (SMART ROUTER)
# ─────────────────────────────────────────────

def _llm_call(prompt: str, required_keys: list, max_retries: int = 2) -> dict:
    messages = [{"role": "user", "content": prompt}]

    raw, result = "", {}

    for attempt in range(max_retries + 1):
        try:
            if LLM_PROVIDER == "nvidia":
                raw = _call_nvidia(messages)
            else:
                raw = _call_ollama(messages)

        except Exception as e:
            # fallback to ollama if nvidia fails
            if LLM_PROVIDER == "nvidia":
                print(f"[LLM ERROR -> NVIDIA] {e} -> Falling back to Ollama")
                raw = _call_ollama(messages)
            else:
                raise e

        result = _extract_json(raw)

        missing = [k for k in required_keys if result.get(k) is None]

        if not missing:
            result["_raw"] = raw
            return result

        # retry logic
        if attempt < max_retries:
            messages.append({"role": "assistant", "content": raw})
            messages.append({
                "role": "user",
                "content": f"Missing keys: {missing}. Return ONLY valid JSON. No markdown."
            })

    result["_schema_error"] = f"Missing keys after retries: {missing}"
    result["_raw"] = raw
    return result


# ─────────────────────────────────────────────────────────────────
# NSE data fetching
# ─────────────────────────────────────────────────────────────────

def _nse_fetch(symbol: str) -> dict:
    symbol = symbol.upper().strip()
    try:
        from jugaad_data.nse import NSELive
        nse   = NSELive()
        quote = nse.stock_quote(symbol)
        trade = nse.trade_info(symbol)
        return _parse_nse_response(symbol, quote, trade, source="jugaad-data")
    except ImportError:
        pass
    except Exception as e:
        print(f"[NSE/jugaad] {symbol}: {e}")
    return _nse_direct(symbol)


def _nse_direct(symbol: str) -> dict:
    BASE = "https://www.nseindia.com"
    headers = {
        "Host":             "www.nseindia.com",
        "Referer":          f"https://www.nseindia.com/get-quotes/equity?symbol={symbol}",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent":       (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        ),
        "Accept":           "*/*",
        "Accept-Language":  "en-GB,en-US;q=0.9,en;q=0.8",
        "Accept-Encoding":  "gzip, deflate, br",
        "Cache-Control":    "no-cache",
        "Connection":       "keep-alive",
        "sec-fetch-dest":   "empty",
        "sec-fetch-mode":   "cors",
        "sec-fetch-site":   "same-origin",
    }
    s = requests.Session()
    s.headers.update(headers)
    try:
        s.get(f"{BASE}/get-quotes/equity?symbol={symbol}", timeout=12)
        time.sleep(0.5)
        r1    = s.get(f"{BASE}/api/quote-equity", params={"symbol": symbol}, timeout=14)
        quote = r1.json() if r1.status_code == 200 else {}
        r2    = s.get(f"{BASE}/api/quote-equity",
                      params={"symbol": symbol, "section": "trade_info"}, timeout=14)
        trade = r2.json() if r2.status_code == 200 else {}
    except Exception as e:
        return {"ok": False, "_error": str(e)}
    if not quote:
        return {"ok": False, "_error": "NSE returned empty response"}
    return _parse_nse_response(symbol, quote, trade, source="NSE direct")


def _parse_nse_response(symbol: str, quote: dict, trade: dict, source: str = "NSE") -> dict:
    pi   = quote.get("priceInfo", {})
    meta = quote.get("metadata", {})
    si   = quote.get("securityInfo", {})
    ii   = quote.get("industryInfo", {})
    ti   = _safe_get(trade, "tradeInfo") or {}

    cur  = _safe_get(pi, "lastPrice") or _safe_get(pi, "close")
    w52h = _safe_get(pi, "weekHighLow", "max")
    w52l = _safe_get(pi, "weekHighLow", "min")

    position = "N/A"
    if cur and w52l and w52h and (w52h - w52l) > 0:
        pct      = round((cur - w52l) / (w52h - w52l) * 100, 1)
        position = f"{pct}% of 52-week range"

    return {
        "ok":            True,
        "data_source":   source,
        "symbol":        symbol,
        "company_name":  meta.get("companyName", symbol),
        "isin":          meta.get("isin", ""),
        "series":        meta.get("series", "EQ"),
        "listing_date":  meta.get("listingDate", ""),
        "face_value":    si.get("faceValue"),
        "sector":        ii.get("sector", ""),
        "industry":      ii.get("industry", ""),
        "current_price": cur,
        "prev_close":    _safe_get(pi, "previousClose"),
        "day_high":      _safe_get(pi, "intraDayHighLow", "max"),
        "day_low":       _safe_get(pi, "intraDayHighLow", "min"),
        "week52_high":   w52h,
        "week52_low":    w52l,
        "vwap":          _safe_get(pi, "vwap"),
        "change":        _safe_get(pi, "change", default=0),
        "pchange":       _safe_get(pi, "pChange", default=0),
        "momentum":      position,
        "total_vol":     _safe_get(ti, "totalTradedVolume"),
        "total_val":     _safe_get(ti, "totalTradedValue"),
        "delivery_qty":  _safe_get(ti, "deliveryQuantity"),
        "delivery_pct":  _safe_get(ti, "deliveryToTradedQuantity"),
    }


def _yf_fetch(ticker_ns: str) -> dict:
    try:
        stk  = yf.Ticker(ticker_ns)
        info = stk.info
        hist = stk.history(period="6mo")
        price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("previousClose")
        )
        prev = info.get("previousClose") or info.get("regularMarketPreviousClose")
        return {
            "ok":               True,
            "current_price":    price,
            "prev_close":       prev,
            "market_cap":       info.get("marketCap"),
            "trailing_pe":      info.get("trailingPE"),
            "forward_pe":       info.get("forwardPE"),
            "trailing_eps":     info.get("trailingEps"),
            "forward_eps":      info.get("forwardEps"),
            "pb_ratio":         info.get("priceToBook"),
            "profit_margins":   info.get("profitMargins"),
            "gross_margins":    info.get("grossMargins"),
            "ebitda_margins":   info.get("ebitdaMargins"),
            "revenue_growth":   info.get("revenueGrowth") or info.get("earningsGrowth"),
            "total_revenue":    info.get("totalRevenue"),
            "net_income":       info.get("netIncomeToCommon"),
            "free_cash_flow":   info.get("freeCashflow"),
            "debt_to_equity":   info.get("debtToEquity"),
            "current_ratio":    info.get("currentRatio"),
            "return_on_equity": info.get("returnOnEquity"),
            "return_on_assets": info.get("returnOnAssets"),
            "dividend_yield":   info.get("dividendYield"),
            "beta":             info.get("beta"),
            "recommendation":   info.get("recommendationKey"),
            "target_price":     info.get("targetMeanPrice"),
            "n_analysts":       info.get("numberOfAnalystOpinions"),
            "long_name":        info.get("longName"),
            "short_name":       info.get("shortName"),
            "sector":           info.get("sector", ""),
            "industry":         info.get("industry", ""),
            "hist":             hist,
            "_raw_info":        info,
        }
    except Exception as e:
        return {"ok": False, "_yf_error": str(e), "hist": None}


def _jugaad_extras(symbol: str) -> dict:
    try:
        from jugaad_data.nse import live_stock_data
        live = live_stock_data(symbol)
        return {
            "jugaad_pe":        live.get("pe"),
            "jugaad_pb":        live.get("pb"),
            "jugaad_div_yield": live.get("dividendYield"),
        }
    except Exception:
        return {}

# Screener API


# Screener logic moved to data_pipeline.py

# ─────────────────────────────────────────────────────────────────
# Fair Value calculation
# ─────────────────────────────────────────────────────────────────

_SECTOR_PE_RULES = [
    ("software",          28), ("information tech", 28), ("it service",  28),
    ("technology",        26), ("pharma",           32), ("healthcare",  30),
    ("hospital",          35), ("bank",             15), ("financial",   18),
    ("nbfc",              18), ("insurance",        22), ("fmcg",        45),
    ("consumer staple",   40), ("consumer goods",   38), ("retail",      40),
    ("consumer cyclical", 35), ("automobile",       25), ("auto",        22),
    ("energy",            14), ("oil",              12), ("gas",         12),
    ("power",             16), ("utility",          16), ("telecom",     20),
    ("communication",     20), ("metal",            10), ("steel",       10),
    ("cement",            18), ("material",         18), ("real estate", 22),
    ("realty",            22), ("infrastructure",   20), ("capital good",28),
    ("industrial",        24), ("chemical",         22), ("textile",     18),
    ("media",             25), ("aviation",         20), ("travel",      28),
    ("tourism",           28), ("logistics",        24), ("agri",        20),
]
_DEFAULT_PE = 22


def _lookup_sector_pe(sector: str, industry: str) -> tuple:
    combined = f"{sector} {industry}".lower()
    for keyword, pe in _SECTOR_PE_RULES:
        if keyword in combined:
            return pe, f"{keyword.title()} sector"
    return _DEFAULT_PE, "broad market"


def calculate_fair_value(current_price, trailing_pe, trailing_eps,
                         pb_ratio, sector, industry,
                         target_price, n_analysts) -> dict:
    results   = {}
    cur       = current_price or 0
    sector_pe, sector_label = _lookup_sector_pe(sector or "", industry or "")

    if target_price and n_analysts and int(n_analysts) >= 3:
        upside = round((target_price - cur) / cur * 100, 2) if cur else 0
        results["analyst"] = {
            "value":    round(float(target_price), 2),
            "upside":   upside,
            "method":   f"Analyst consensus ({n_analysts} analysts)",
            "reliable": True,
        }

    if trailing_eps and float(trailing_eps) > 0:
        val_b  = round(float(trailing_eps) * sector_pe, 2)
        up_b   = round((val_b - cur) / cur * 100, 2) if cur else 0
        results["sector_pe"] = {
            "value":    val_b,
            "upside":   up_b,
            "method":   f"Sector PE ({sector_pe}x - {sector_label})",
            "reliable": trailing_pe is not None and float(trailing_pe or 0) > 0,
        }

    bvps = (cur / float(pb_ratio)) if pb_ratio and float(pb_ratio) > 0 and cur else None
    if trailing_eps and bvps and float(trailing_eps) > 0 and bvps > 0:
        graham = round((22.5 * float(trailing_eps) * bvps) ** 0.5, 2)
        up_g   = round((graham - cur) / cur * 100, 2) if cur else 0
        results["graham"] = {
            "value":    graham,
            "upside":   up_g,
            "method":   "Graham Number",
            "reliable": trailing_pe and float(trailing_pe) < 35,
        }

    primary = None
    for key in ["analyst", "sector_pe", "graham"]:
        if key in results:
            primary = {**results[key], "method_key": key}
            break

    if not primary:
        primary = {
            "value": cur, "upside": 0.0,
            "method": "Insufficient data", "reliable": False, "method_key": "none",
        }

    return {"primary": primary, "all": results, "current": cur}


# ─────────────────────────────────────────────────────────────────
# Component 1: Fundamentals Scoring Engine (pure data, no LLM)
# ─────────────────────────────────────────────────────────────────

def compute_fundamentals_score(info: dict, raw: dict) -> dict:
    """
    Score the company on hard financial metrics.
    Returns a score 0-100, per-metric breakdown, and data_completeness.
    Each metric is scored 0-10 and weighted.
    """
    breakdown = {}
    weights_used = {}
    available_weight = 0.0

    def _num(val, default=None):
        if val is None: return default
        try: return float(val)
        except (ValueError, TypeError): return default

    trailing_pe = _num(info.get("trailing_pe") or raw.get("trailingPE"))
    sector = info.get("sector", "") or ""
    industry = info.get("industry", "") or ""
    sector_pe, sector_label = _lookup_sector_pe(sector, industry)

    if trailing_pe is not None and trailing_pe > 0:
        pe_ratio = trailing_pe / sector_pe
        pe_score = 9 if pe_ratio < 0.8 else (7 if pe_ratio < 1.0 else (5 if pe_ratio < 1.3 else (3 if pe_ratio < 1.8 else 1)))
        breakdown["pe_vs_sector"] = {"score": pe_score, "value": round(pe_ratio, 2), "detail": f"PE {trailing_pe:.1f} vs sector {sector_pe} ({sector_label})"}
        weights_used["pe_vs_sector"] = 0.15
        available_weight += 0.15

    profit_margins = _num(info.get("profit_margins") or raw.get("profitMargins"))
    if profit_margins is not None:
        pm_pct = profit_margins * 100 if abs(profit_margins) < 1 else profit_margins
        pm_score = 9 if pm_pct > 20 else (8 if pm_pct > 15 else (6 if pm_pct > 10 else (4 if pm_pct > 5 else (2 if pm_pct > 0 else 1))))
        breakdown["profit_margins"] = {"score": pm_score, "value": round(pm_pct, 2), "detail": f"Profit margin {pm_pct:.1f}%"}
        weights_used["profit_margins"] = 0.15
        available_weight += 0.15

    rev_growth = _num(raw.get("revenueGrowth"))
    if rev_growth is not None:
        rg_pct = rev_growth * 100 if abs(rev_growth) < 5 else rev_growth
        rg_score = 10 if rg_pct > 25 else (8 if rg_pct > 15 else (6 if rg_pct > 10 else (5 if rg_pct > 5 else (3 if rg_pct > 0 else 1))))
        breakdown["revenue_growth"] = {"score": rg_score, "value": round(rg_pct, 2), "detail": f"Revenue growth {rg_pct:.1f}%"}
        weights_used["revenue_growth"] = 0.15
        available_weight += 0.15

    roe = _num(info.get("return_on_equity") or raw.get("returnOnEquity"))
    if roe is not None:
        roe_pct = roe * 100 if abs(roe) < 5 else roe
        roe_score = 10 if roe_pct > 25 else (8 if roe_pct > 18 else (5 if roe_pct > 10 else (3 if roe_pct > 0 else 1)))
        breakdown["roe"] = {"score": roe_score, "value": round(roe_pct, 2), "detail": f"ROE {roe_pct:.1f}%"}
        weights_used["roe"] = 0.12
        available_weight += 0.12

    d2e = _num(info.get("debt_to_equity") or raw.get("debtToEquity"))
    if d2e is not None:
        de_score = 10 if d2e < 30 else (8 if d2e < 50 else (5 if d2e < 100 else (3 if d2e < 150 else 1)))
        breakdown["debt_to_equity"] = {"score": de_score, "value": round(d2e, 2), "detail": f"D/E ratio {d2e:.1f}"}
        weights_used["debt_to_equity"] = 0.12
        available_weight += 0.12

    cur_ratio = _num(info.get("current_ratio"))
    if cur_ratio is not None:
        cr_score = 9 if cur_ratio > 2.0 else (7 if cur_ratio > 1.5 else (5 if cur_ratio > 1.0 else (3 if cur_ratio > 0.7 else 1)))
        breakdown["current_ratio"] = {"score": cr_score, "value": round(cur_ratio, 2), "detail": f"Current ratio {cur_ratio:.2f}"}
        weights_used["current_ratio"] = 0.08
        available_weight += 0.08

    fcf = _num(info.get("free_cash_flow"))
    if fcf is not None:
        if fcf > 0:
            mkt_cap = _num(info.get("market_cap") or raw.get("marketCap"))
            if mkt_cap and mkt_cap > 0:
                fcf_yield = (fcf / mkt_cap) * 100
                fcf_score = 9 if fcf_yield > 5 else (7 if fcf_yield > 3 else 5)
            else:
                fcf_score = 6
        else:
            fcf_score = 2
        breakdown["free_cash_flow"] = {"score": fcf_score, "value": round(fcf / 1e7, 1), "detail": f"FCF {fcf/1e7:.1f} Cr"}
        weights_used["free_cash_flow"] = 0.08
        available_weight += 0.08

    fv_upside = _num(raw.get("_fair_value_upside"))
    if fv_upside is None:
        tgt = _num(info.get("target_mean_price"))
        cur_price = _num(raw.get("currentPrice"))
        if tgt and cur_price and cur_price > 0:
            fv_upside = ((tgt - cur_price) / cur_price) * 100
    if fv_upside is not None:
        fvu_score = 10 if fv_upside > 25 else (8 if fv_upside > 15 else (6 if fv_upside > 5 else (4 if fv_upside > 0 else (2 if fv_upside > -10 else 1))))
        breakdown["fair_value_upside"] = {"score": fvu_score, "value": round(fv_upside, 2), "detail": f"Fair value upside {fv_upside:+.1f}%"}
        weights_used["fair_value_upside"] = 0.15
        available_weight += 0.15

    if available_weight > 0:
        weighted_sum = sum(breakdown[k]["score"] * weights_used[k] for k in breakdown)
        score = round((weighted_sum / available_weight) * 10, 1)
    else:
        score = 50.0

    data_completeness = round(available_weight / 1.0, 2)
    return {
        "score": min(100, max(0, score)),
        "breakdown": breakdown,
        "weights_used": weights_used,
        "data_completeness": data_completeness,
        "metrics_available": len(breakdown),
        "metrics_total": 8,
    }


# ─────────────────────────────────────────────────────────────────
# Component 2: Weighted Final Scoring Engine
# ─────────────────────────────────────────────────────────────────

def compute_final_score(bull_score: int, bear_score: int, sent_score: int,
                        fundamentals_score: float, fair_value_upside: float,
                        data_completeness: float) -> dict:
    W_FUND, W_BULL, W_BEAR, W_SENT, W_FAIR = 0.35, 0.20, 0.20, 0.15, 0.10
    fund_norm = max(0, min(100, fundamentals_score))
    bull_norm = max(0, min(100, float(bull_score)))
    bear_norm = max(0, min(100, float(bear_score)))
    sent_norm = max(0, min(100, (float(sent_score) + 100) / 2))

    # Bear is inverted: high bear score = bad, treated as low bull
    # This guarantees neutral stock (all=50) → composite = 50 with no magic offset
    bear_inv = 100 - bear_norm

    # FIX: Fair value scoring — any positive upside ≥ 55 (not below neutral)
    if fair_value_upside is not None:
        if   fair_value_upside > 30:  fv_score = 90
        elif fair_value_upside > 15:  fv_score = 78
        elif fair_value_upside > 5:   fv_score = 65
        elif fair_value_upside > 0:   fv_score = 55   # was 45 — positive upside should be above neutral
        elif fair_value_upside > -10: fv_score = 40
        elif fair_value_upside > -25: fv_score = 25
        else:                          fv_score = 12
    else:
        fv_score = 50  # unknown = perfectly neutral

    # Pure weighted average — no magic offset needed
    composite = (
        W_FUND * fund_norm +
        W_BULL * bull_norm +
        W_BEAR * bear_inv  +
        W_SENT * sent_norm +
        W_FAIR * fv_score
    )
    composite = max(0, min(100, composite))

    # 5-Tier verdict system
    if   composite >= 75: verdict = "STRONG BUY"
    elif composite >= 60: verdict = "BUY"
    elif composite <= 25: verdict = "STRONG SELL"
    elif composite <= 40: verdict = "SELL"
    else:                  verdict = "HOLD"

    # Confidence: distance from the nearest threshold, scaled 30-95
    if verdict == "HOLD":
        # Max distance inside HOLD zone is 10 (40→50 or 50→60)
        dist = min(abs(composite - 40), abs(composite - 60))
        confidence = int(30 + (dist / 10.0) * 35)     # 30–65 inside HOLD
    elif verdict in ("BUY", "SELL"):
        # Distance beyond the 60/40 threshold (max 15 before STRONG zone)
        dist = min(abs(composite - 60), abs(composite - 40)) if verdict == "BUY" else abs(composite - 40)
        dist = abs(composite - 60) if verdict == "BUY" else abs(composite - 40)
        dist = min(dist, 15)
        confidence = int(55 + (dist / 15.0) * 25)     # 55–80
    else:  # STRONG BUY / STRONG SELL
        dist = abs(composite - 75) if verdict == "STRONG BUY" else abs(composite - 25)
        dist = min(dist, 25)
        confidence = int(75 + (dist / 25.0) * 20)     # 75–95

    # Penalty for low data completeness
    if data_completeness < 0.8:
        confidence = int(confidence * (0.5 + 0.5 * data_completeness))

    confidence = max(10, min(95, confidence))

    risk = "HIGH" if (bear_norm > 70 or (bear_norm > bull_norm + 20)) else ("MEDIUM" if (bear_norm > 50 or (bear_norm > bull_norm + 5)) else "LOW")

    return {
        "verdict": verdict, "confidence": confidence, "risk": risk, "composite": round(composite, 1),
        "scores": {
            "fundamentals": round(fund_norm, 1), "bull": round(bull_norm, 1), "bear": round(bear_norm, 1),
            "sentiment": round(sent_norm, 1), "fair_value": fv_score, "data_completeness": data_completeness,
        },
        "weights": {"fundamentals": W_FUND, "bull": W_BULL, "bear": W_BEAR, "sentiment": W_SENT, "fair_value": W_FAIR},
        "breakdown": f"Fund {fund_norm:.0f}x{W_FUND} + Bull {bull_norm:.0f}x{W_BULL} + BearInv {bear_inv:.0f}x{W_BEAR} + Sent {sent_norm:.0f}x{W_SENT} + FV {fv_score}x{W_FAIR} = {composite:.1f} → {verdict}",
    }


# ─────────────────────────────────────────────────────────────────
# Component 3: Validation Layer — hard rules applied AFTER scoring
# ─────────────────────────────────────────────────────────────────
def validate_and_adjust(
    score_result: dict,
    fundamentals_score: float,
    bull_score: int,
    bear_score: int,
    data_completeness: float
) -> dict:

    result = score_result.copy()
    applied = []

    verdict    = result.get("verdict", "HOLD")
    confidence = result.get("confidence", 50)
    risk       = result.get("risk", "MEDIUM")

    # ─────────────────────────────────────────
    # 🧠 RULE 1: Weak fundamentals block any BUY tier
    # ─────────────────────────────────────────
    if fundamentals_score < 30 and verdict in ("BUY", "STRONG BUY"):
        result["verdict"] = "HOLD"
        confidence = min(confidence, 50)
        applied.append("Rule 1: Weak fundamentals (<30) blocked BUY → HOLD")

    # ─────────────────────────────────────────
    # 🧠 RULE 2: Strong bear dominance blocks any BUY tier
    # ─────────────────────────────────────────
    if (bear_score - bull_score) >= 20 and verdict in ("BUY", "STRONG BUY"):
        result["verdict"] = "HOLD"
        confidence = min(confidence, 45)
        applied.append("Rule 2: Bear dominance blocked BUY → HOLD")

    # ─────────────────────────────────────────
    # 🧠 RULE 2B: Downgrade STRONG BUY → BUY if bear is elevated
    # ─────────────────────────────────────────
    if bear_score > 55 and verdict == "STRONG BUY":
        result["verdict"] = "BUY"
        confidence = min(confidence, 75)
        applied.append("Rule 2B: Elevated bear risk downgraded STRONG BUY → BUY")

    # ─────────────────────────────────────────
    # 🧠 RULE 3: Strong bull dominance softens any SELL tier
    # ─────────────────────────────────────────
    if (bull_score - bear_score) >= 25 and verdict in ("SELL", "STRONG SELL"):
        result["verdict"] = "HOLD"
        confidence = max(confidence, 55)
        applied.append("Rule 3: Bull dominance softened SELL → HOLD")

    # ─────────────────────────────────────────
    # 🧠 RULE 4: LOW DATA COMPLETENESS (CRITICAL)
    # ─────────────────────────────────────────
    if data_completeness < 0.5:
        if verdict in ("BUY", "STRONG BUY"):
            result["verdict"] = "HOLD"
            confidence = min(confidence, 40)
            applied.append("Rule 4A: Low data completeness blocked BUY → HOLD")
        elif confidence > 40:
            confidence = 40
            applied.append("Rule 4B: Low data completeness capped confidence")

    # ─────────────────────────────────────────
    # 🧠 RULE 5: High risk blocks STRONG BUY, downgrades BUY
    # ─────────────────────────────────────────
    if risk == "HIGH":
        if result["verdict"] == "STRONG BUY":
            result["verdict"] = "BUY"
            confidence = min(confidence, 65)
            applied.append("Rule 5A: High risk downgraded STRONG BUY → BUY")
        elif result["verdict"] == "BUY":
            result["verdict"] = "HOLD"
            confidence = min(confidence, 50)
            applied.append("Rule 5B: High risk blocked BUY → HOLD")

    # ─────────────────────────────────────────
    # 🧠 RULE 6: Very strong fundamentals upgrade HOLD
    # ─────────────────────────────────────────
    if fundamentals_score > 75 and result["verdict"] == "HOLD":
        if bull_score > bear_score:
            result["verdict"] = "BUY"
            confidence = max(confidence, 60)
            applied.append("Rule 6: Strong fundamentals upgraded HOLD → BUY")

    # ─────────────────────────────────────────
    # 🧠 RULE 7: Exceptional fundamentals + bull = STRONG BUY
    # ─────────────────────────────────────────
    if fundamentals_score > 85 and result["verdict"] == "BUY" and bull_score > 70 and bear_score < 40:
        result["verdict"] = "STRONG BUY"
        confidence = max(confidence, 78)
        applied.append("Rule 7: Exceptional fundamentals + bull dominance → STRONG BUY")

    # ─────────────────────────────────────────
    # 🧠 RULE 7: Confidence sanity bounds
    # ─────────────────────────────────────────
    confidence = max(10, min(confidence, 95))

    # ─────────────────────────────────────────
    # FINAL ASSIGNMENT
    # ─────────────────────────────────────────
    result["confidence"] = int(confidence)
    result["applied_rules"] = applied

    return result


# ─────────────────────────────────────────────────────────────────
# Main data entry point
# ─────────────────────────────────────────────────────────────────

def get_basic_data(ticker: str) -> dict:
    nse_sym   = ticker.upper().replace(".NS","").replace(".BO","").replace("-","").strip()
    yf_ticker = f"{nse_sym}.NS"

    pipeline = get_clean_stock_data(nse_sym)
    clean_data = pipeline["data"]
    completeness = pipeline["completeness"]

    nse = _nse_fetch(nse_sym)
    yf  = _yf_fetch(yf_ticker)
    jg  = _jugaad_extras(nse_sym) if not yf.get("trailing_pe") else {}

    cur_price  = nse.get("current_price") or yf.get("current_price")
    prev_close = nse.get("prev_close")    or yf.get("prev_close")

    if cur_price and prev_close and float(prev_close) > 0:
        price_change     = round(float(cur_price) - float(prev_close), 2)
        price_change_pct = round(price_change / float(prev_close) * 100, 2)
    else:
        price_change     = nse.get("change", 0) or 0
        price_change_pct = nse.get("pchange", 0) or 0

    company  = nse.get("company_name") or yf.get("long_name") or yf.get("short_name") or nse_sym
    sector   = nse.get("sector")   or yf.get("sector",   "N/A")
    industry = nse.get("industry") or yf.get("industry", "N/A")

    mkt_cap   = yf.get("market_cap")
    t_pe      = clean_data.get("pe")
    pb        = clean_data.get("pb")
    roe       = clean_data.get("roe")
    d2e       = clean_data.get("debt")
    rev_gr    = clean_data.get("growth")
    p_margins = clean_data.get("margin")
    f_pe      = yf.get("forward_pe")
    t_eps     = yf.get("trailing_eps")
    g_margins = yf.get("gross_margins")
    tot_rev   = yf.get("total_revenue")
    fcf       = yf.get("free_cash_flow")
    cur_ratio = yf.get("current_ratio")
    roa       = yf.get("return_on_assets")
    div_yield = yf.get("dividend_yield") or jg.get("jugaad_div_yield")
    beta      = yf.get("beta")
    rec       = yf.get("recommendation", "N/A")
    tgt_price = yf.get("target_price")
    n_an      = yf.get("n_analysts")
    w52h      = nse.get("week52_high") or yf.get("_raw_info", {}).get("fiftyTwoWeekHigh")
    w52l      = nse.get("week52_low")  or yf.get("_raw_info", {}).get("fiftyTwoWeekLow")
    data_src  = nse.get("data_source", "NSE") if nse.get("ok") else "yfinance (delayed)"

    fv = calculate_fair_value(
        current_price=cur_price, trailing_pe=t_pe, trailing_eps=t_eps,
        pb_ratio=pb, sector=sector, industry=industry,
        target_price=tgt_price, n_analysts=n_an,
    )

    summary = f"""
=== {company} ({nse_sym}) | Source: {data_src} ===

PRICE DATA
  Current Price    : {fmt_rupee(cur_price)}
  Previous Close   : {fmt_rupee(prev_close)}
  Change Today     : {price_change:+.2f} ({price_change_pct:+.2f}%)
  Today High / Low : {fmt_rupee(nse.get('day_high'))} / {fmt_rupee(nse.get('day_low'))}
  52-Week High     : {fmt_rupee(w52h)}
  52-Week Low      : {fmt_rupee(w52l)}
  52-Week Position : {nse.get('momentum', 'N/A')}
  VWAP             : {fmt_rupee(nse.get('vwap'))}

COMPANY
  Sector           : {sector}
  Industry         : {industry}
  Market Cap       : {fmt_cr(mkt_cap)}
  Face Value       : {fmt_rupee(nse.get('face_value'))}
  ISIN             : {nse.get('isin', 'N/A')}
  Listed Since     : {nse.get('listing_date', 'N/A')}

VALUATION
  P/E (Trailing)   : {t_pe if t_pe else 'N/A'}
  P/E (Forward)    : {f_pe if f_pe else 'N/A'}
  P/B Ratio        : {pb  if pb   else 'N/A'}
  EPS (TTM)        : {fmt_rupee(t_eps)}
  Dividend Yield   : {fmt_pct(div_yield)}
  Beta             : {beta if beta else 'N/A'}
  Fair Value (Est) : {fmt_rupee(fv['primary']['value'])} ({fv['primary']['method']})
  Upside / Down    : {fv['primary']['upside']:+.2f}%

FINANCIALS
  Revenue (TTM)    : {fmt_cr(tot_rev)}
  Revenue Growth   : {fmt_pct(rev_gr)}
  Profit Margins   : {fmt_pct(p_margins)}
  Gross Margins    : {fmt_pct(g_margins)}
  Free Cash Flow   : {fmt_cr(fcf)}
  Debt / Equity    : {d2e       if d2e       else 'N/A'}
  Current Ratio    : {cur_ratio if cur_ratio else 'N/A'}
  ROE              : {fmt_pct(roe)}
  ROA              : {roa if roa else 'N/A'}

TRADING (NSE)
  Volume           : {nse.get('total_vol', 'N/A')}
  Traded Value     : {fmt_cr(nse.get('total_val'))}
  Delivery %       : {nse.get('delivery_pct', 'N/A')}%

ANALYST VIEW
  Consensus        : {rec.upper() if rec else 'N/A'}
  Target Price     : {fmt_rupee(tgt_price)}
  Analyst Count    : {n_an if n_an else 'N/A'}
""".strip()

    return {
        "completeness": completeness,
        "summary": summary,
        "info": {
            "company_name":       company,
            "nse_symbol":         nse_sym,
            "isin":               nse.get("isin", ""),
            "listing_date":       nse.get("listing_date", ""),
            "face_value":         nse.get("face_value"),
            "sector":             sector,
            "industry":           industry,
            "market_cap":         mkt_cap,
            "trailing_pe":        t_pe,
            "forward_pe":         f_pe,
            "pb_ratio":           pb,
            "trailing_eps":       t_eps,
            "profit_margins":     p_margins,
            "gross_margins":      g_margins,
            "total_revenue":      tot_rev,
            "free_cash_flow":     fcf,
            "debt_to_equity":     d2e,
            "current_ratio":      cur_ratio,
            "return_on_equity":   roe,
            "return_on_assets":   roa,
            "dividend_yield":     div_yield,
            "beta":               beta,
            "recommendation":     rec,
            "target_mean_price":  tgt_price,
            "number_of_analysts": n_an,
            "data_source":        data_src,
            "delivery_pct":       nse.get("delivery_pct"),
            "vwap":               nse.get("vwap"),
        },
        "raw": {
            "currentPrice":   cur_price,
            "prevClose":      prev_close,
            "change":         price_change,
            "pchange":        price_change_pct,
            "dayHigh":        nse.get("day_high"),
            "dayLow":         nse.get("day_low"),
            "week52High":     w52h,
            "week52Low":      w52l,
            "vwap":           nse.get("vwap"),
            "deliveryPct":    nse.get("delivery_pct"),
            "marketCap":      mkt_cap,
            "trailingPE":     t_pe,
            "profitMargins":  p_margins,
            "revenueGrowth":  rev_gr,
            "debtToEquity":   d2e,
            "returnOnEquity": roe,
            "beta":           beta,
        },
        "hist":       yf.get("hist"),
        "fair_value": fv,
        "nse_raw":    nse,
        "yf_raw":     yf,
    }


# ─────────────────────────────────────────────────────────────────
# News fetching — strict title-level relevance filter
# ─────────────────────────────────────────────────────────────────

_URL_SOURCE_MAP = {
    "moneycontrol":         "MoneyControl",
    "economictimes":        "Economic Times",
    "livemint":             "Mint",
    "business-standard":    "Business Standard",
    "thehindubusinessline": "Hindu BusinessLine",
    "ndtvprofit":           "NDTV Profit",
    "financialexpress":     "Financial Express",
    "cnbctv18":             "CNBC TV18",
    "zeebiz":               "Zee Business",
    "reuters":              "Reuters",
    "bloomberg":            "Bloomberg",
    "upstox":               "Upstox",
    "msn":                  "MSN",
    "etretail":             "ET Retail",
}

_SOURCE_PRIORITY = [
    "moneycontrol", "economic times", "mint", "business standard",
    "hindu businessline", "ndtv profit", "financial express",
    "cnbc", "zee business", "reuters", "bloomberg",
    "upstox", "et retail", "msn",
]


def _source_from_url(url: str) -> str:
    u = url.lower()
    for fragment, name in _URL_SOURCE_MAP.items():
        if fragment in u:
            return name
    return "News"


def _parse_age(pub_str: str) -> tuple:
    if not pub_str:
        return None, ""
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
    ]
    dt = None
    for fmt in formats:
        try:
            dt = datetime.strptime(pub_str.strip(), fmt)
            break
        except ValueError:
            continue
    if not dt:
        return None, pub_str[:10]
    try:
        dt_naive = dt.replace(tzinfo=None)
    except Exception:
        dt_naive = dt
    delta = datetime.utcnow() - dt_naive
    if delta.days == 0:
        h = delta.seconds // 3600
        label = "Just now" if h == 0 else f"{h}h ago"
    elif delta.days == 1:
        label = "Yesterday"
    elif delta.days <= 6:
        label = f"{delta.days} days ago"
    elif delta.days <= 30:
        w = delta.days // 7
        label = f"{w} week{'s' if w > 1 else ''} ago"
    else:
        label = dt_naive.strftime("%d %b %Y")
    return dt_naive, label


def _build_name_variants(company_name: str, nse_symbol: str) -> list:
    variants = set()
    sym = nse_symbol.strip().upper()
    if len(sym) > 2:
        variants.add(sym.lower())
    parts = company_name.split()
    if not parts:
        return list(variants)
    first = re.sub(r'[^a-zA-Z0-9]', '', parts[0]).lower()
    if len(first) > 2:
        variants.add(first)
    if len(parts) >= 2:
        two = f"{parts[0]} {parts[1]}".lower()
        if len(two) > 4:
            variants.add(two)
    clean = re.sub(
        r'\b(ltd|limited|solutions|technologies|tech|industries|'
        r'corp|inc|pvt|private|services|enterprises|group|holdings)\b',
        '', company_name, flags=re.IGNORECASE
    ).strip().lower()
    clean = re.sub(r'\s+', ' ', clean)
    if len(clean) > 3:
        variants.add(clean)
        cp = clean.split()
        if cp and len(cp[0]) > 2:
            variants.add(cp[0])
    return [v for v in variants if len(v) > 2]


def _title_is_relevant(title: str, variants: list) -> bool:
    t = title.lower()
    return any(v in t for v in variants)


def _rss_fetch(query: str, limit: int = 8) -> list:
    encoded = query.replace(" ", "%20").replace(":", "%3A").replace("/", "%2F")
    url     = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        feed  = feedparser.parse(url)
        items = []
        for entry in feed.entries[:limit]:
            src_obj = entry.get("source", {})
            source  = (
                src_obj.get("title", "") if isinstance(src_obj, dict) else str(src_obj)
            ) or _source_from_url(entry.get("link", ""))
            pub_str      = entry.get("published", "")
            dt, age_lbl  = _parse_age(pub_str)
            items.append({
                "title":     entry.get("title", ""),
                "link":      entry.get("link", "#"),
                "source":    source,
                "published": pub_str[:16],
                "age_label": age_lbl,
                "pub_dt":    dt,
                "summary":   re.sub(r"<[^>]+>", "", entry.get("summary", ""))[:200],
            })
        return items
    except Exception:
        return []


def get_news(company_name: str, nse_symbol: str = "") -> list:
    search_term = nse_symbol.upper() if nse_symbol else company_name
    variants    = _build_name_variants(company_name, search_term)
    collected   = []

    for site in [
        "site:moneycontrol.com",
        "site:economictimes.indiatimes.com",
        "site:livemint.com",
        "site:business-standard.com",
    ]:
        collected.extend(_rss_fetch(f"{search_term} {site}", limit=4))

    collected.extend(_rss_fetch(f"{search_term} NSE stock India",            limit=6))
    collected.extend(_rss_fetch(f"{search_term} quarterly results earnings",  limit=3))

    relevant = [item for item in collected if _title_is_relevant(item["title"], variants)]

    seen, unique = set(), []
    for item in relevant:
        key = item["title"][:55].lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(item)

    def _sort_key(item):
        src  = item.get("source", "").lower()
        rank = 99
        for i, name in enumerate(_SOURCE_PRIORITY):
            if name in src:
                rank = i
                break
        dt  = item.get("pub_dt")
        age = (datetime.utcnow() - dt).total_seconds() if dt else 999999
        return (rank, age)

    unique.sort(key=_sort_key)
    return unique[:10]


def get_news_text(news_items: list) -> str:
    return "\n".join(
        f"- {item['title']} [{item.get('source', '')}]"
        for item in news_items
    )


# ─────────────────────────────────────────────────────────────────
# AI Agents
# ─────────────────────────────────────────────────────────────────

def analyze_sentiment(news_text: str) -> dict:
    prompt = f"""
You are a financial sentiment analyst covering Indian equity markets.
Read these headlines and assess how the market feels about this stock.

Headlines:
{news_text}

Return ONLY valid JSON, no markdown:
{{
  "sentiment": "POSITIVE",
  "score": 45,
  "reasons": ["observation 1", "observation 2"],
  "key_themes": ["earnings beat", "FII buying"]
}}

sentiment: POSITIVE / NEGATIVE / NEUTRAL / MIXED
score: integer -100 to +100
reasons: 2-3 specific things from the actual headlines
key_themes: 1-3 short labels for dominant stories
"""
    return _llm_call(prompt, required_keys=["sentiment", "score", "reasons"])


def run_bull_agent(fundamental_summary: str, news_text: str) -> dict:
    prompt = f"""
You are a bullish equity analyst covering NSE-listed Indian stocks.

PRIORITY ORDER — analyse fundamentals FIRST, news SECOND:
1. Financial strength: revenue growth, profit margins, ROE, free cash flow
2. Valuation cushion: P/E vs sector, fair value upside, analyst targets
3. Company-specific catalysts: order wins, capacity expansion, market share gains
4. Sector/macro tailwinds (only if backed by specific data)

QUALITY RULES:
- Every point MUST cite the EXACT metric value or headline it comes from
- Do NOT cite generic signals like "market rally", "analyst targets" without numbers,
  or broad macro headlines unrelated to this specific company
- metric_cited MUST contain a specific number, ratio, or headline quote
- Do not invent anything not in the data

Company Data:
{fundamental_summary}

Recent News:
{news_text}

Return ONLY valid JSON — no markdown:
{{
  "bull_points": [
    {{
      "point": "clear bullish observation with specific data",
      "metric_cited": "exact value e.g. 'Revenue growth 18.5%' or headline quote",
      "strength": "STRONG",
      "impact": "why this should push the stock higher"
    }}
  ],
  "overall_bull_score": 65,
  "bull_thesis": "one crisp sentence summarising the bull case"
}}

  overall_bull_score → integer 0-100 (be honest — weak data = low score)
  strength           → STRONG / MODERATE / WEAK
  Aim for 3-5 points. Fewer strong points > many weak ones.
"""
    return _llm_call(prompt, required_keys=["bull_points", "overall_bull_score"])


def run_bear_agent(fundamental_summary: str, news_text: str) -> dict:
    prompt = f"""
You are a bearish equity analyst covering NSE-listed Indian stocks.

PRIORITY ORDER — analyse financial weaknesses FIRST, news SECOND:
1. Financial red flags: declining margins, high debt/equity, negative FCF, weak ROE
2. Valuation risk: P/E above sector, overvalued vs fair value, high forward PE
3. Company-specific risks: customer concentration, regulatory, competition
4. Negative news (only company-specific, NOT generic market fears)

QUALITY RULES:
- Every point MUST cite the EXACT metric value or headline it comes from
- Do NOT cite generic fears like "market downturn", "global uncertainty"
- metric_cited MUST contain a specific number, ratio, or headline quote
- Do not invent anything not in the data

Company Data:
{fundamental_summary}

Recent News:
{news_text}

Return ONLY valid JSON — no markdown:
{{
  "bear_points": [
    {{
      "point": "clear bearish risk with specific data",
      "metric_cited": "exact value e.g. 'Debt/Equity 145.2' or headline quote",
      "severity": "MODERATE",
      "impact": "how this could push the stock lower"
    }}
  ],
  "overall_bear_score": 60,
  "bear_thesis": "one crisp sentence summarising the bear case"
}}

  overall_bear_score → integer 0-100 (100 = extremely risky, be honest)
  severity           → SEVERE / MODERATE / MINOR
  Aim for 3-5 points. Fewer strong points > many weak ones.
"""
    return _llm_call(prompt, required_keys=["bear_points", "overall_bear_score"])


def run_judge_agent(bull_result: dict, bear_result: dict, sentiment: dict,
                    verdict_data: dict = None, fundamentals_data: dict = None) -> dict:
    """
    Component 5: Simplified Judge Agent.
    The verdict is PRE-COMPUTED by compute_final_score() + validate_and_adjust().
    The LLM's only job: write final_reasoning, key_catalyst, key_risk.
    """
    bull_score = bull_result.get("overall_bull_score", 50)
    bear_score = bear_result.get("overall_bear_score", 50)
    sent_score = sentiment.get("score", 0)

    if verdict_data:
        verdict    = verdict_data.get("verdict", "HOLD")
        confidence = verdict_data.get("confidence", 50)
        risk       = verdict_data.get("risk", "MEDIUM")
        composite  = verdict_data.get("composite", 50)
        breakdown  = verdict_data.get("breakdown", "")
        scores     = verdict_data.get("scores", {})
        validation = verdict_data.get("validation_applied", [])

        fund_score = scores.get("fundamentals", "N/A")
        validation_text = "\n".join(f"  - {v}" for v in validation) if validation else "  None"

        prompt = f"""
You are a senior portfolio manager at an Indian equity fund.
The verdict has been MATHEMATICALLY COMPUTED — you CANNOT change it.

PRE-COMPUTED DECISION (do NOT override):
  Verdict     : {verdict}
  Confidence  : {confidence}%
  Risk        : {risk}
  Composite   : {composite}/100
  Breakdown   : {breakdown}
  Fundamentals: {fund_score}/100
  Validation rules applied:
{validation_text}

Bull case ({bull_score}/100): {bull_result.get('bull_thesis', '')}
Bear case ({bear_score}/100): {bear_result.get('bear_thesis', '')}
Sentiment: {sentiment.get('sentiment', 'N/A')} (score: {sent_score})

Bull points:
{json.dumps(bull_result.get('bull_points', []), indent=2)}

Bear points:
{json.dumps(bear_result.get('bear_points', []), indent=2)}

YOUR TASK: Write reasoning to EXPLAIN the pre-computed {verdict} verdict.
Do NOT suggest a different verdict.

Return ONLY valid JSON — no markdown:
{{
  "final_reasoning": "2-3 sentences explaining WHY this is a {verdict}",
  "key_catalyst": "single biggest upside driver from the data",
  "key_risk": "single biggest downside risk from the data",
  "timeframe": "short-term"
}}

  timeframe → short-term / medium-term / long-term
"""
        result = _llm_call(prompt, required_keys=["final_reasoning", "key_catalyst", "key_risk"])
        result["verdict"]            = verdict
        result["confidence"]         = confidence
        result["risk"]               = risk
        result["composite"]          = composite
        result["scores"]             = scores
        result["weights"]            = verdict_data.get("weights", {})
        result["validation_applied"] = validation
        result["signal_breakdown"]   = breakdown
        return result

    net = bull_score - bear_score
    direction = "BUY-leaning" if net > 15 else ("SELL-leaning" if net < -15 else "HOLD-leaning")
    prompt = f"""
You are a senior portfolio manager at an Indian equity fund.
Two analysts have done their work. Read both sides and make a final call.

  Bull score : {bull_score}/100
  Bear score : {bear_score}/100
  Sentiment  : {sentiment.get('sentiment', 'N/A')} (score: {sent_score})
  Direction  : {direction}

Return ONLY valid JSON — no markdown:
{{
  "verdict": "{direction.split('-')[0]}",
  "confidence": 50,
  "risk": "MEDIUM",
  "timeframe": "short-term",
  "final_reasoning": "2-3 sentences",
  "key_catalyst": "biggest upside driver",
  "key_risk": "biggest downside risk"
}}
"""
    result = _llm_call(prompt, required_keys=["verdict", "final_reasoning"])
    result["signal_breakdown"] = f"Bull {bull_score} - Bear {bear_score} = net {net:+d} (legacy)"
    return result





# ─────────────────────────────────────────────────────────────────
# Prediction store
# ─────────────────────────────────────────────────────────────────

_PRED_FILE = "predictions.json"
_EVAL_DAYS = 5


def _load_preds() -> list:
    if not os.path.exists(_PRED_FILE):
        return []
    with open(_PRED_FILE) as f:
        try:
            return json.load(f)
        except Exception:
            return []


def _save_preds(data: list):
    with open(_PRED_FILE, "w") as f:
        json.dump(data, f, indent=2)


def save_prediction(ticker: str, prediction: dict,
                    bull_score: int, bear_score: int,
                    current_price: float = 0,
                    fundamentals_score: float = 50,
                    scores: dict = None):
    data = _load_preds()
    data.append({
        "ticker":             ticker,
        "nse_symbol":         ticker.replace(".NS","").replace(".BO","").upper(),
        "prediction":         prediction,
        "bull_score":         bull_score,
        "bear_score":         bear_score,
        "fundamentals_score": fundamentals_score,
        "scores_breakdown":   scores or {},
        "baseline_price":     float(current_price) if current_price else 0,
        "timestamp":          datetime.utcnow().isoformat(),
        "eval_results":       {},  # { "3d": {...}, "7d": {...}, "14d": {...} }
        "checked":            False,
    })
    _save_preds(data)


def get_days_until_eval(timestamp_str: str) -> int:
    try:
        pred_dt = datetime.fromisoformat(timestamp_str)
        elapsed = (datetime.utcnow() - pred_dt).days
        return max(0, 3 - elapsed)
    except Exception:
        return 3


def check_outcomes():
    data = _load_preds()
    changed = False
    EVAL_PERIODS = [3, 7, 14]

    for entry in data:
        ts = entry.get("timestamp")
        if not ts: continue
        elapsed_days = (datetime.utcnow() - datetime.fromisoformat(ts)).days

        # Ensure eval_results dict exists
        if "eval_results" not in entry:
            entry["eval_results"] = {}

        # If already fully checked up to 14 days, skip
        if entry.get("checked") and "14d" in entry.get("eval_results", {}):
            continue

        baseline = entry.get("baseline_price")
        if not baseline: continue
        nse_sym = entry.get("nse_symbol", "")

        for period in EVAL_PERIODS:
            period_key = f"{period}d"
            if period_key in entry["eval_results"]:
                continue
            if elapsed_days < period:
                continue

            # Need to evaluate this period
            cur_price = None
            try:
                hist = yf.Ticker(f"{nse_sym}.NS").history(
                    start=(datetime.fromisoformat(ts) + timedelta(days=period-1)).strftime("%Y-%m-%d"),
                    end=(datetime.fromisoformat(ts) + timedelta(days=period+2)).strftime("%Y-%m-%d")
                )
                if not hist.empty:
                    cur_price = float(hist["Close"].iloc[-1])
            except Exception:
                pass

            if not cur_price:
                # Fallback to current if it's roughly the target time
                try:
                    cur_price = _nse_fetch(nse_sym).get("current_price")
                except Exception:
                    pass

            if not cur_price: continue

            pct_move = round((cur_price - baseline) / baseline * 100, 2)
            verdict = entry["prediction"].get("verdict", "")

            # Advanced scoring: Partial credit for small moves
            correct = False
            if verdict == "BUY" and pct_move > 1.0: correct = True
            elif verdict == "SELL" and pct_move < -1.0: correct = True
            elif verdict == "HOLD" and abs(pct_move) <= 3.0: correct = True

            entry["eval_results"][period_key] = {
                "price": cur_price,
                "pct_change": pct_move,
                "correct": correct
            }
            changed = True

        # Mark globally checked if at least one evaluation happened
        if entry.get("eval_results"):
            entry["checked"] = True

    if changed:
        _save_preds(data)


def calculate_accuracy() -> float:
    data = _load_preds()
    total_evals = 0
    correct_evals = 0

    for d in data:
        evals = d.get("eval_results", {})
        if evals:
            for res in evals.values():
                if res.get("correct") is not None:
                    total_evals += 1
                    if res["correct"]:
                        correct_evals += 1
        elif d.get("checked") and d.get("correct") is not None:
            total_evals += 1
            if d["correct"]:
                correct_evals += 1

    if not total_evals: return 0.0
    return round((correct_evals / total_evals) * 100, 2)


def get_prediction_history() -> list:
    return _load_preds()


# ─────────────────────────────────────────────────────────────────
# Quick test
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    SYM = "IRCTC"
    print(f"\n{'─'*55}  StockAI  {'─'*55}\n")
    data = get_basic_data(SYM)
    fv   = data["fair_value"]["primary"]
    print(f"Source     : {data['info']['data_source']}")
    print(f"Price      : {fmt_rupee(data['raw'].get('currentPrice'))}")
    print(f"Change     : {data['raw'].get('pchange', 0):+.2f}%")
    print(f"Fair Value : {fmt_rupee(fv['value'])} ({fv['method']})")
    print(f"Upside     : {fv['upside']:+.2f}%\n")
    news = get_news(data["info"]["company_name"], SYM)
    print(f"News ({len(news)} relevant articles):")
    for n in news[:3]:
        print(f"  [{n['source']}] [{n['age_label']}] {n['title'][:70]}")

    print("\nRunning agents...")
    ntxt = get_news_text(news)
    sent = analyze_sentiment(ntxt)
    bull = run_bull_agent(data["summary"], ntxt)
    bear = run_bear_agent(data["summary"], ntxt)

    fv_u = data["fair_value"]["primary"].get("upside", 0)

    # 1. Compute Fundamentals Score
    fund = compute_fundamentals_score(data["info"], data["raw"])

    # 2. Compute Weighted Final Score
    de = compute_final_score(
        bull_score=bull.get("overall_bull_score", 50),
        bear_score=bear.get("overall_bear_score", 50),
        sent_score=sent.get("score", 0),
        fundamentals_score=fund["score"],
        fair_value_upside=fv_u,
        data_completeness=fund["data_completeness"],
    )

    # 3. Apply Validation Rules
    validated = validate_and_adjust(
        de, fund["score"], bull.get("overall_bull_score", 50),
        bear.get("overall_bear_score", 50), fund["data_completeness"]
    )

    # 4. Final Reasoning via Judge Agent
    verd = run_judge_agent(bull, bear, sent, verdict_data=validated, fundamentals_data=fund)

    print(f"\nVerdict    : {verd.get('verdict')} | Conf: {verd.get('confidence')}%")
    print(f"Composite  : {validated['composite']}/100")
    print(f"Breakdown  : {validated['breakdown']}")
    for rule in validated.get("validation_applied", []):
        print(f"  > {rule}")

    cur = data["raw"].get("currentPrice", 0)
    save_prediction(SYM, verd,
                    bull.get("overall_bull_score", 50),
                    bear.get("overall_bear_score", 50),
                    cur or 0,
                    fundamentals_score=fund["score"],
                    scores=validated.get("scores"))
    check_outcomes()
    print(f"\nAccuracy   : {calculate_accuracy()}%")
