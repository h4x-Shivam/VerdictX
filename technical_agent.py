"""
VerdictX — Technical Analysis Agent
Pure deterministic indicator computation + LLM for key_insight/bias only.
Uses `ta` library for all indicator calculations.
"""

import numpy as np
import pandas as pd
import yfinance as yf
from ta.trend import EMAIndicator, ADXIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator


# ─────────────────────────────────────────────────────────────────
# 1. Data Fetching & Validation
# ─────────────────────────────────────────────────────────────────

def _fetch_ohlcv(symbol: str) -> pd.DataFrame:
    """Fetch 1-year daily OHLCV for {symbol}.NS with validation."""
    ticker = f"{symbol.upper().replace('.NS','').replace('.BO','')}.NS"
    df = yf.Ticker(ticker).history(period="1y", interval="1d")

    if df is None or len(df) < 100:
        raise ValueError(f"Insufficient data for {ticker}: got {len(df) if df is not None else 0} rows")

    required = ["Open", "High", "Low", "Close", "Volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # Drop rows where Close is NaN or zero
    df = df[df["Close"].notna() & (df["Close"] > 0)].copy()
    if len(df) < 100:
        raise ValueError(f"Only {len(df)} valid rows after cleaning")

    return df


import time

_nifty_cache = {"data": None, "timestamp": 0}

def _fetch_nifty() -> pd.Series:
    """Fetch 1-year daily Close for Nifty 50 (cached for 1 hour to optimize latency)."""
    global _nifty_cache
    now = time.time()
    
    # Return cached data if it's less than 1 hour old (3600 seconds)
    if _nifty_cache["data"] is not None and (now - _nifty_cache["timestamp"] < 3600):
        return _nifty_cache["data"]

    try:
        df = yf.Ticker("^NSEI").history(period="1y", interval="1d")
        if df is None or len(df) < 50:
            return None
            
        result = df["Close"].dropna()
        _nifty_cache = {"data": result, "timestamp": now}
        return result
    except Exception as e:
        print(f"[TechnicalAgent] Warning: Failed to fetch Nifty 50 for relative strength: {e}")
        return _nifty_cache["data"]  # Return stale cache if available, else None


# ─────────────────────────────────────────────────────────────────
# 2. Indicator Computation
# ─────────────────────────────────────────────────────────────────

def _compute_indicators(df: pd.DataFrame, nifty: pd.Series = None) -> dict:
    """Compute all 12 indicators from OHLCV. Returns raw values dict."""
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    ind = {}

    # ── Trend ──
    ind["ema20"] = EMAIndicator(close, window=20).ema_indicator().iloc[-1]
    ind["ema50"] = EMAIndicator(close, window=50).ema_indicator().iloc[-1]
    ind["ema200"] = EMAIndicator(close, window=200).ema_indicator().iloc[-1]
    ind["price"] = close.iloc[-1]

    adx_obj = ADXIndicator(high, low, close, window=14)
    ind["adx"] = round(adx_obj.adx().iloc[-1], 1) if not np.isnan(adx_obj.adx().iloc[-1]) else 0
    ind["di_plus"] = adx_obj.adx_pos().iloc[-1]
    ind["di_minus"] = adx_obj.adx_neg().iloc[-1]

    # Supertrend (manual — ATR based, period=7, multiplier=3)
    atr7 = AverageTrueRange(high, low, close, window=7).average_true_range()
    hl2 = (high + low) / 2
    upper_band = hl2 + 3 * atr7
    lower_band = hl2 - 3 * atr7

    supertrend_dir = "BULLISH"
    if close.iloc[-1] < upper_band.iloc[-1] and close.iloc[-2] >= upper_band.iloc[-2]:
        supertrend_dir = "BEARISH"
    elif close.iloc[-1] > lower_band.iloc[-1]:
        supertrend_dir = "BULLISH"
    elif close.iloc[-1] < lower_band.iloc[-1]:
        supertrend_dir = "BEARISH"
    # Refine: if price below EMA50, lean bearish
    if ind["price"] < ind["ema50"]:
        supertrend_dir = "BEARISH"
    ind["supertrend"] = supertrend_dir

    # EMA alignment
    ind["ema_aligned_bull"] = ind["ema20"] > ind["ema50"] > ind["ema200"]
    ind["ema_aligned_bear"] = ind["ema20"] < ind["ema50"] < ind["ema200"]

    # ── Momentum ──
    rsi_series = RSIIndicator(close, window=14).rsi()
    ind["rsi"] = round(rsi_series.iloc[-1], 1)
    # RSI trend (declining = last 5 values trending down)
    rsi_last5 = rsi_series.iloc[-5:].values
    ind["rsi_declining"] = rsi_last5[-1] < rsi_last5[0] if len(rsi_last5) == 5 else False

    macd_obj = MACD(close, window_slow=26, window_fast=12, window_sign=9)
    macd_hist = macd_obj.macd_diff()
    ind["macd_hist"] = round(macd_hist.iloc[-1], 2)
    ind["macd_hist_prev"] = round(macd_hist.iloc[-2], 2) if len(macd_hist) > 1 else 0
    ind["macd_hist_shrinking"] = abs(ind["macd_hist"]) < abs(ind["macd_hist_prev"])
    ind["macd_positive"] = ind["macd_hist"] > 0

    # RSI divergence: price making higher high but RSI making lower high
    price_last20 = close.iloc[-20:]
    rsi_last20 = rsi_series.iloc[-20:]
    if len(price_last20) >= 20:
        mid = 10
        price_hh = price_last20.iloc[mid:].max() > price_last20.iloc[:mid].max()
        rsi_lh = rsi_last20.iloc[mid:].max() < rsi_last20.iloc[:mid].max()
        ind["rsi_bearish_divergence"] = price_hh and rsi_lh
        price_ll = price_last20.iloc[mid:].min() < price_last20.iloc[:mid].min()
        rsi_hl = rsi_last20.iloc[mid:].min() > rsi_last20.iloc[:mid].min()
        ind["rsi_bullish_divergence"] = price_ll and rsi_hl
    else:
        ind["rsi_bearish_divergence"] = False
        ind["rsi_bullish_divergence"] = False

    # ── Volume ──
    obv_series = OnBalanceVolumeIndicator(close, volume).on_balance_volume()
    obv_last10 = obv_series.iloc[-10:]
    ind["obv_rising"] = obv_last10.iloc[-1] > obv_last10.iloc[0] if len(obv_last10) >= 2 else False

    vol_ma20 = volume.rolling(20).mean().iloc[-1]
    vol_current = volume.iloc[-5:].mean()  # avg last 5 days
    ind["vol_ratio"] = round(vol_current / vol_ma20, 1) if vol_ma20 > 0 else 1.0
    ind["vol_spike"] = ind["vol_ratio"] >= 1.5

    # ── Volatility ──
    bb = BollingerBands(close, window=20, window_dev=2)
    bb_upper = bb.bollinger_hband().iloc[-1]
    bb_lower = bb.bollinger_lband().iloc[-1]
    bb_width = (bb_upper - bb_lower) / close.iloc[-1] * 100
    bb_width_20 = ((bb.bollinger_hband() - bb.bollinger_lband()) / close * 100).rolling(20).mean().iloc[-1]
    ind["bb_width"] = round(bb_width, 2)
    ind["bb_squeeze"] = bb_width < bb_width_20 * 0.8  # squeeze = width below 80% of its 20-day avg
    ind["bb_upper"] = round(bb_upper, 2)
    ind["bb_lower"] = round(bb_lower, 2)

    atr14 = AverageTrueRange(high, low, close, window=14).average_true_range()
    ind["atr"] = round(atr14.iloc[-1], 2)
    ind["atr_pct"] = round(atr14.iloc[-1] / close.iloc[-1] * 100, 2)  # ATR as % of price

    # ── Structure ──
    ind["w52_high"] = round(high.iloc[-252:].max(), 2) if len(high) >= 252 else round(high.max(), 2)
    ind["w52_low"] = round(low.iloc[-252:].min(), 2) if len(low) >= 252 else round(low.min(), 2)
    ind["dist_to_52h"] = round((ind["w52_high"] - ind["price"]) / ind["price"] * 100, 1)
    ind["dist_to_52l"] = round((ind["price"] - ind["w52_low"]) / ind["price"] * 100, 1)

    # Swing S/R — recent pivot highs/lows (last 60 candles)
    recent = df.iloc[-60:]
    pivot_highs = []
    pivot_lows = []
    for i in range(2, len(recent) - 2):
        h = recent["High"].iloc
        l = recent["Low"].iloc
        if h[i] > h[i-1] and h[i] > h[i-2] and h[i] > h[i+1] and h[i] > h[i+2]:
            pivot_highs.append(h[i])
        if l[i] < l[i-1] and l[i] < l[i-2] and l[i] < l[i+1] and l[i] < l[i+2]:
            pivot_lows.append(l[i])

    # Nearest resistance = closest pivot high above price
    resistances = sorted([p for p in pivot_highs if p > ind["price"]])
    supports = sorted([p for p in pivot_lows if p < ind["price"]], reverse=True)
    ind["resistance"] = round(resistances[0], 2) if resistances else ind["w52_high"]
    ind["support"] = round(supports[0], 2) if supports else ind["w52_low"]
    ind["dist_to_resistance"] = round((ind["resistance"] - ind["price"]) / ind["price"] * 100, 1)
    ind["dist_to_support"] = round((ind["price"] - ind["support"]) / ind["price"] * 100, 1)

    # ── Market Context ──
    if nifty is not None and len(nifty) >= 63:
        # 3-month relative strength
        stock_3m = (close.iloc[-1] / close.iloc[-63] - 1) * 100 if len(close) >= 63 else 0
        nifty_3m = (nifty.iloc[-1] / nifty.iloc[-63] - 1) * 100
        ind["rs_vs_nifty"] = round(stock_3m - nifty_3m, 1)
        ind["stock_3m_return"] = round(stock_3m, 1)
        ind["nifty_3m_return"] = round(nifty_3m, 1)
    else:
        ind["rs_vs_nifty"] = 0
        ind["stock_3m_return"] = 0
        ind["nifty_3m_return"] = 0

    return ind


# ─────────────────────────────────────────────────────────────────
# 3. Deterministic Scoring Engine
# ─────────────────────────────────────────────────────────────────

RUPEE = "\u20b9"


def _score_trend(ind: dict) -> dict:
    score = 50
    data = []

    if ind["ema_aligned_bull"]:
        score += 25
        data.append("EMA 20 > 50 > 200 aligned")
    elif ind["ema_aligned_bear"]:
        score -= 25
        data.append("EMA 20 < 50 < 200 (bearish alignment)")
    else:
        data.append("EMA partially aligned")

    adx = ind["adx"]
    if adx >= 25:
        score += 10
        data.append(f"ADX: {adx} (Strong trend)")
    elif adx >= 20:
        data.append(f"ADX: {adx} (Moderate)")
    else:
        score -= 5
        data.append(f"ADX: {adx} (Weak/No trend)")

    st = ind["supertrend"]
    if st == "BULLISH":
        score += 15
    else:
        score -= 15
    data.append(f"Supertrend: {st.capitalize()}")

    score = max(0, min(100, score))
    if score >= 65:
        status = "bullish"
    elif score <= 35:
        status = "bearish"
    else:
        status = "neutral"

    return {"status": status, "data": data, "score": score}


def _score_momentum(ind: dict) -> dict:
    score = 50
    data = []

    rsi = ind["rsi"]
    if rsi > 70:
        score -= 10
        data.append(f"RSI: {rsi} (overbought)")
    elif rsi < 30:
        score += 10
        data.append(f"RSI: {rsi} (oversold — bounce potential)")
    elif rsi >= 50:
        score += 5
        desc = "declining" if ind["rsi_declining"] else "stable"
        data.append(f"RSI: {rsi} ({desc})")
    else:
        score -= 5
        data.append(f"RSI: {rsi} (below midline)")

    if ind["rsi_declining"]:
        score -= 8

    if ind["macd_positive"]:
        score += 10
    else:
        score -= 10

    if ind["macd_hist_shrinking"]:
        score -= 5
        data.append("MACD histogram shrinking")
    else:
        data.append("MACD histogram expanding")

    if ind["rsi_bearish_divergence"]:
        score -= 15
        data.append("Bearish RSI divergence detected")
    elif ind["rsi_bullish_divergence"]:
        score += 15
        data.append("Bullish RSI divergence detected")

    score = max(0, min(100, score))
    if score >= 60:
        status = "bullish"
    elif score >= 40:
        status = "weakening"
    else:
        status = "bearish"

    return {"status": status, "data": data, "score": score}


def _score_volume(ind: dict) -> dict:
    score = 50
    data = []

    if ind["obv_rising"]:
        score += 20
        data.append("OBV rising (accumulation)")
    else:
        score -= 15
        data.append("OBV declining (distribution)")

    ratio = ind["vol_ratio"]
    if ratio >= 1.5:
        score += 15
        data.append(f"Volume {ratio}x 20-day average (spike)")
    elif ratio >= 1.0:
        score += 5
        data.append(f"Volume {ratio}x 20-day average")
    else:
        score -= 5
        data.append(f"Volume {ratio}x 20-day average (below avg)")

    if ind["obv_rising"] and ratio >= 1.0:
        data.append("Smart money confirming")
    elif not ind["obv_rising"] and ratio >= 1.5:
        data.append("High volume on distribution — caution")

    score = max(0, min(100, score))
    if score >= 60:
        status = "confirming"
    elif score >= 40:
        status = "neutral"
    else:
        status = "diverging"

    return {"status": status, "data": data, "score": score}


def _score_volatility(ind: dict) -> dict:
    score = 50
    data = []

    if ind["bb_squeeze"]:
        score -= 5  # uncertainty
        data.append("BB Squeeze forming — breakout imminent")
    else:
        data.append("Bollinger Bands normal width")

    atr_pct = ind["atr_pct"]
    if atr_pct > 3.0:
        score -= 10
        data.append(f"ATR: {atr_pct}% (high volatility)")
    elif atr_pct > 1.5:
        data.append(f"ATR: {atr_pct}% (moderate)")
    else:
        score += 5
        data.append(f"ATR: {atr_pct}% (low volatility)")

    if ind["bb_squeeze"]:
        data.append("Direction unclear — wait for confirmation")

    score = max(0, min(100, score))
    if score >= 60:
        status = "bullish"
    elif score >= 40:
        status = "watch"
    else:
        status = "caution"

    return {"status": status, "data": data, "score": score}


def _score_structure(ind: dict) -> dict:
    score = 50
    data = []

    dist_r = ind["dist_to_resistance"]
    dist_s = ind["dist_to_support"]

    data.append(f"Resistance {RUPEE}{ind['resistance']:,.0f} ({dist_r}% away)")
    data.append(f"Support {RUPEE}{ind['support']:,.0f} ({dist_s}% below)")

    # Good structure = far from resistance, close support
    if dist_r > 10:
        score += 15
    elif dist_r > 5:
        score += 5
    elif dist_r < 3:
        score -= 15
        data.append("Near resistance — unfavorable entry")

    if dist_s < 3:
        score -= 10
    elif dist_s > 10:
        score += 5

    # Near 52W high = momentum but risk
    if ind["dist_to_52h"] < 5:
        score += 5
        data.append(f"Near 52W High ({RUPEE}{ind['w52_high']:,.0f})")
    elif ind["dist_to_52l"] < 10:
        score -= 10

    score = max(0, min(100, score))
    if score >= 60:
        status = "bullish"
    elif score >= 40:
        status = "caution"
    else:
        status = "bearish"

    return {"status": status, "data": data, "score": score}


def _score_market_context(ind: dict) -> dict:
    score = 50
    data = []

    rs = ind["rs_vs_nifty"]
    if rs > 5:
        score += 20
        data.append(f"+{rs}% vs Nifty 50 (3-month)")
    elif rs > 0:
        score += 10
        data.append(f"+{rs}% vs Nifty 50 (3-month)")
    elif rs > -5:
        score -= 5
        data.append(f"{rs}% vs Nifty 50 (3-month)")
    else:
        score -= 15
        data.append(f"{rs}% vs Nifty 50 (underperforming)")

    data.append(f"3-month relative strength")
    data.append(f"52W High: {RUPEE}{ind['w52_high']:,.0f} / 52W Low: {RUPEE}{ind['w52_low']:,.0f}")

    score = max(0, min(100, score))
    if score >= 60:
        status = "outperforming"
    elif score >= 40:
        status = "neutral"
    else:
        status = "bearish"

    return {"status": status, "data": data, "score": score}


def _score_dimensions(ind: dict) -> tuple:
    """Score all 6 dimensions. Returns (dimensions_dict, technical_score)."""
    dims = {
        "trend":          _score_trend(ind),
        "momentum":       _score_momentum(ind),
        "volume":         _score_volume(ind),
        "volatility":     _score_volatility(ind),
        "structure":      _score_structure(ind),
        "market_context": _score_market_context(ind),
    }

    # Weighted average
    weights = {
        "trend": 0.25, "momentum": 0.20, "volume": 0.15,
        "volatility": 0.10, "structure": 0.15, "market_context": 0.15,
    }
    technical_score = sum(dims[k]["score"] * weights[k] for k in dims)
    technical_score = round(max(0, min(100, technical_score)), 0)

    return dims, int(technical_score)


def _detect_regime(ind: dict) -> dict:
    """Detect market regime from ADX + Supertrend."""
    adx = ind["adx"]
    if adx >= 25:
        regime_type = "TRENDING"
    elif adx <= 20:
        regime_type = "RANGING"
    else:
        regime_type = "BREAKOUT PENDING"

    return {
        "type": regime_type,
        "adx": adx,
        "supertrend": ind["supertrend"],
    }


# ─────────────────────────────────────────────────────────────────
# 4. LLM Key Insight Generation
# ─────────────────────────────────────────────────────────────────

def _generate_insight(ind: dict, dims: dict, score: int) -> dict:
    """Use LLM to generate key_insight and bias from raw indicator data."""
    from main import _llm_call

    dim_summary = ""
    for name, d in dims.items():
        dim_summary += f"  {name.upper()}: {d['status']} (score {d['score']}/100) — {', '.join(d['data'])}\n"

    prompt = f"""You are a technical analyst. Given these computed indicators and dimension scores,
write a concise key insight and determine the bias.

INDICATORS:
  Price: {ind['price']:.2f} | EMA20: {ind['ema20']:.2f} | EMA50: {ind['ema50']:.2f} | EMA200: {ind['ema200']:.2f}
  ADX: {ind['adx']} | Supertrend: {ind['supertrend']}
  RSI: {ind['rsi']} (declining: {ind['rsi_declining']}) | MACD Hist: {ind['macd_hist']}
  OBV Rising: {ind['obv_rising']} | Vol Ratio: {ind['vol_ratio']}x
  BB Squeeze: {ind['bb_squeeze']} | ATR%: {ind['atr_pct']}
  Resistance: {ind['resistance']} ({ind['dist_to_resistance']}% away)
  Support: {ind['support']} ({ind['dist_to_support']}% below)
  RS vs Nifty: {ind['rs_vs_nifty']}%

DIMENSION SCORES:
{dim_summary}
OVERALL TECHNICAL SCORE: {score}/100

Return ONLY valid JSON — no markdown:
{{
  "key_insight": "2-3 sentences synthesizing the technical picture. Be specific with numbers.",
  "bias": "one of: Strongly Bullish / Cautiously Bullish / Neutral / Cautiously Bearish / Strongly Bearish"
}}
"""
    result = _llm_call(prompt, required_keys=["key_insight", "bias"])
    return {
        "key_insight": result.get("key_insight", "Technical analysis complete."),
        "bias": result.get("bias", "Neutral"),
    }


def _fallback_bias(score: int) -> str:
    """Deterministic bias if LLM fails."""
    if score >= 75:
        return "Strongly Bullish"
    elif score >= 60:
        return "Cautiously Bullish"
    elif score >= 40:
        return "Neutral"
    elif score >= 25:
        return "Cautiously Bearish"
    else:
        return "Strongly Bearish"


# ─────────────────────────────────────────────────────────────────
# 5. Public API
# ─────────────────────────────────────────────────────────────────

def compute_technical_indicators(symbol: str) -> tuple:
    """
    Stage 1 — pure computation, no LLM. Safe to run in parallel.
    Returns (indicators_dict, dimensions_dict, regime_dict, score).
    """
    try:
        df = _fetch_ohlcv(symbol)
        nifty = _fetch_nifty()
        ind = _compute_indicators(df, nifty)
        dims, score = _score_dimensions(ind)
        regime = _detect_regime(ind)
        return ind, dims, regime, score
    except Exception as e:
        print(f"[TechnicalAgent] Error computing indicators for {symbol}: {e}")
        return None, None, None, None


def generate_technical_insight(ind: dict, dims: dict, score: int) -> dict:
    """
    Stage 2 — LLM call for key_insight + bias. Run sequentially with other LLM calls.
    """
    try:
        return _generate_insight(ind, dims, score)
    except Exception as e:
        print(f"[TechnicalAgent] LLM insight failed: {e}")
        return {"key_insight": "Technical analysis complete.", "bias": _fallback_bias(score)}


def run_technical_agent(symbol: str) -> dict:
    """
    Full pipeline — compute + LLM insight. Returns the exact JSON shape for frontend.
    Can be called standalone for testing.
    """
    ind, dims, regime, score = compute_technical_indicators(symbol)

    if ind is None:
        return {
            "regime": {"type": "N/A", "adx": 0, "supertrend": "N/A"},
            "dimensions": {},
            "technical_score": 0,
            "bias": "Neutral",
            "key_insight": "Technical analysis unavailable — insufficient data.",
        }

    insight = generate_technical_insight(ind, dims, score)

    # Strip internal 'score' from dimensions before sending to frontend
    clean_dims = {}
    for k, v in dims.items():
        clean_dims[k] = {"status": v["status"], "data": v["data"]}

    return {
        "regime": regime,
        "dimensions": clean_dims,
        "technical_score": score,
        "bias": insight["bias"],
        "key_insight": insight["key_insight"],
    }


# ─────────────────────────────────────────────────────────────────
# Quick test
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    SYM = "RELIANCE"
    print(f"\nRunning Technical Agent for {SYM}...")
    result = run_technical_agent(SYM)
    print(json.dumps(result, indent=2, ensure_ascii=False))
