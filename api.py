"""
VerdictX Flask API
Wraps main.py pipeline with SSE (Server-Sent Events) for real-time streaming.
Run with: python api.py
"""

import json
import time
import traceback
from flask import Flask, Response, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow React dev server (localhost:5173)


# ─────────────────────────────────────────────────────────────────
# JSON serializer — handles pandas DataFrames, numpy types, etc.
# ─────────────────────────────────────────────────────────────────

def _safe_json(obj):
    """Recursively convert non-serializable objects to JSON-safe types."""
    import numpy as np
    try:
        import pandas as pd
        if isinstance(obj, (pd.DataFrame, pd.Series)):
            return None  # Don't serialize historical data — too large
    except ImportError:
        pass
    if isinstance(obj, dict):
        return {k: _safe_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_safe_json(i) for i in obj]
    try:
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
    except Exception:
        pass
    if isinstance(obj, float) and (obj != obj):  # NaN check
        return None
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


def _emit(event_type: str, payload: dict) -> str:
    """Format a single SSE event."""
    data = json.dumps({"type": event_type, **payload})
    return f"data: {data}\n\n"


# ─────────────────────────────────────────────────────────────────
# SSE Analysis Stream
# ─────────────────────────────────────────────────────────────────

def _analysis_generator(ticker: str):
    """Generator that runs the full analysis pipeline and yields SSE events."""
    from main import (
        get_basic_data, get_news, get_news_text,
        analyze_sentiment, run_bull_agent, run_bear_agent,
        run_judge_agent, save_prediction, check_outcomes,
        compute_fundamentals_score, compute_final_score, validate_and_adjust,
    )

    try:
        # ── Step 1: Basic stock data ──
        yield _emit("progress", {"step": 1, "total": 7, "pct": 5,
                                  "msg": f"Fetching NSE data for {ticker.upper()}…"})
        data = get_basic_data(ticker)
        fund_summary = data["summary"]
        raw = data["raw"]
        info = data["info"]
        fv = data.get("fair_value", {})

        yield _emit("progress", {"step": 1, "total": 7, "pct": 15,
                                  "msg": "Stock data fetched ✓"})

        # ── Step 2: Fundamentals score ──
        yield _emit("progress", {"step": 2, "total": 7, "pct": 20,
                                  "msg": "Computing fundamentals score…"})
        fund_data = compute_fundamentals_score(info, raw)

        # ── Step 3: News ──
        yield _emit("progress", {"step": 3, "total": 7, "pct": 28,
                                  "msg": "Fetching news from MoneyControl, ET, Mint…"})
        company_name = info.get("company_name", ticker)
        news_items = get_news(company_name, ticker)
        news_text = get_news_text(news_items)

        yield _emit("progress", {"step": 3, "total": 7, "pct": 36,
                                  "msg": f"{len(news_items)} articles found ✓"})

        # ── Step 4: Sentiment ──
        yield _emit("progress", {"step": 4, "total": 7, "pct": 44,
                                  "msg": "Analyzing market sentiment…"})
        sent = analyze_sentiment(news_text)

        yield _emit("progress", {"step": 4, "total": 7, "pct": 50,
                                  "msg": f"Sentiment: {sent.get('sentiment', 'N/A')} ✓"})

        # ── Step 5: Bull agent ──
        yield _emit("progress", {"step": 5, "total": 7, "pct": 56,
                                  "msg": "🟢 Bull agent scanning positive signals…"})
        bull = run_bull_agent(fund_summary, news_text)

        yield _emit("progress", {"step": 5, "total": 7, "pct": 65,
                                  "msg": f"Bull score: {bull.get('overall_bull_score', '?')} ✓"})

        # ── Step 6: Bear agent ──
        yield _emit("progress", {"step": 6, "total": 7, "pct": 70,
                                  "msg": "🔴 Bear agent scanning risks…"})
        bear = run_bear_agent(fund_summary, news_text)

        yield _emit("progress", {"step": 6, "total": 7, "pct": 78,
                                  "msg": f"Bear score: {bear.get('overall_bear_score', '?')} ✓"})

        # ── Step 7: Score + validate + judge ──
        yield _emit("progress", {"step": 7, "total": 7, "pct": 82,
                                  "msg": "⚖️ Running decision engine…"})
        fv_upside = fv.get("primary", {}).get("upside", 0)
        score_result = compute_final_score(
            bull_score=bull.get("overall_bull_score", 50),
            bear_score=bear.get("overall_bear_score", 50),
            sent_score=sent.get("score", 0),
            fundamentals_score=fund_data["score"],
            fair_value_upside=fv_upside,
            data_completeness=fund_data["data_completeness"],
        )
        validated = validate_and_adjust(
            score_result=score_result,
            fundamentals_score=fund_data["score"],
            bull_score=bull.get("overall_bull_score", 50),
            bear_score=bear.get("overall_bear_score", 50),
            data_completeness=fund_data["data_completeness"],
        )

        yield _emit("progress", {"step": 7, "total": 7, "pct": 88,
                                  "msg": "⚖️ Judge writing final verdict…"})
        verdict = run_judge_agent(bull, bear, sent,
                                   verdict_data=validated,
                                   fundamentals_data=fund_data)

        # ── Save prediction ──
        yield _emit("progress", {"step": 7, "total": 7, "pct": 95,
                                  "msg": "Saving prediction…"})
        cur_price = raw.get("currentPrice") or 0
        save_prediction(
            ticker, verdict,
            bull.get("overall_bull_score", 50),
            bear.get("overall_bear_score", 50),
            float(cur_price),
            fundamentals_score=fund_data["score"],
            scores=validated.get("scores"),
        )
        check_outcomes()

        # ── Done — build result payload ──
        yield _emit("progress", {"step": 7, "total": 7, "pct": 100,
                                  "msg": "Analysis complete ✓"})

        result = _safe_json({
            "ticker": ticker.upper(),
            "info": info,
            "raw": raw,
            "fv": fv,
            "news_items": news_items,
            "sent": sent,
            "bull": bull,
            "bear": bear,
            "verdict": verdict,
            "fund_data": fund_data,
            "validated": validated,
        })

        yield _emit("done", {"result": result})

    except Exception as e:
        tb = traceback.format_exc()
        safe_msg = f"[API ERROR] {ticker}: {e}\n{tb}".encode("utf-8", "replace").decode("utf-8", "replace")
        print(safe_msg)
        yield _emit("error", {"message": str(e), "detail": tb[-500:]})


# ─────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "VerdictX API"})


@app.route("/api/analyze", methods=["GET"])
def analyze():
    ticker = request.args.get("ticker", "").strip().upper()
    if not ticker:
        return jsonify({"error": "Missing ticker parameter"}), 400

    return Response(
        _analysis_generator(ticker),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.route("/api/history", methods=["GET"])
def history():
    """Return recent prediction history."""
    try:
        from main import get_prediction_history
        history = get_prediction_history()
        return jsonify({"history": _safe_json(history)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("[VerdictX API] Running on http://localhost:5001")
    print("   Endpoints:")
    print("   GET  /api/health")
    print("   GET  /api/analyze?ticker=TCS")
    print("   GET  /api/history")
    app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)
