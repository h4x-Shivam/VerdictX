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
# SSE Analysis Stream — Async parallel pipeline
# ─────────────────────────────────────────────────────────────────

def _analysis_generator(ticker: str):
    """
    Generator that runs the full analysis pipeline and yields SSE events.

    Parallelism strategy:
      Stage 1 (parallel): get_basic_data + get_news
      Stage 2 (parallel): analyze_sentiment + run_bull_agent + run_bear_agent
                          → each agent emits a 'partial' event the moment it finishes
      Stage 3 (serial):   compute_scores + validate + run_judge_agent
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from main import (
        get_basic_data, get_news, get_news_text,
        analyze_sentiment, run_bull_agent, run_bear_agent,
        run_judge_agent, save_prediction, check_outcomes,
        compute_fundamentals_score, compute_final_score, validate_and_adjust,
    )

    t0 = time.time()

    try:
        # ── Stage 1: data + news fetched in parallel ──────────────
        yield _emit("progress", {
            "step": 1, "total": 6, "pct": 5,
            "msg": f"Fetching market data + news for {ticker.upper()} in parallel…",
        })

        with ThreadPoolExecutor(max_workers=2) as pool:
            fut_data = pool.submit(get_basic_data, ticker)
            fut_news = pool.submit(get_news, ticker, ticker)

            # Yield heartbeat events while waiting (keeps SSE connection alive
            # and lets React show live sub-step progress)
            data_done = news_done = False
            while not (data_done and news_done):
                if fut_data.done() and not data_done:
                    data_done = True
                    yield _emit("progress", {
                        "step": 1, "total": 6, "pct": 12,
                        "msg": "Market data fetched ✓",
                    })
                if fut_news.done() and not news_done:
                    news_done = True
                    yield _emit("progress", {
                        "step": 1, "total": 6, "pct": 18,
                        "msg": "News articles fetched ✓",
                    })
                if not (data_done and news_done):
                    time.sleep(0.3)  # short poll interval

            data       = fut_data.result()
            news_items = fut_news.result()
            
            if not news_items:
                print(f"[API] Warning: No news items fetched for {ticker} (possible RSS rate limit).")

        fund_summary = data["summary"]
        raw          = data["raw"]
        info         = data["info"]
        fv           = data.get("fair_value", {})
        fund_data    = compute_fundamentals_score(info, raw)
        news_text    = get_news_text(news_items)
        t1 = time.time()

        yield _emit("progress", {
            "step": 2, "total": 4, "pct": 25,
            "msg": f"Stage 1 done in {t1 - t0:.1f}s — launching 3 AI agents in parallel…",
        })

        # ── Stage 2: LLM agents — sequential to respect NVIDIA rate limits ──
        # The _NVIDIA_SEM in main.py serializes API calls anyway — making them
        # explicit here avoids the overhead of ThreadPoolExecutor + as_completed
        # while keeping SSE streaming: each partial fires as the agent finishes.

        yield _emit("progress", {
            "step": 2, "total": 6, "pct": 22,
            "msg": f"Data ready in {t1 - t0:.1f}s — analyzing market sentiment…",
        })

        sent = analyze_sentiment(news_text)
        yield _emit("partial", {
            "agent": "sentiment",
            "sentiment":         sent.get("sentiment", "NEUTRAL"),
            "sentiment_score":   sent.get("score", 0),
            "sentiment_reasons": sent.get("reasons", []),
        })
        yield _emit("progress", {
            "step": 3, "total": 6, "pct": 38,
            "msg": f"Sentiment: {sent.get('sentiment', 'N/A')} ({sent.get('score', 0):+d}) ✓ — Bull agent scanning positive signals…",
        })

        bull = run_bull_agent(fund_summary, news_text)
        yield _emit("partial", {
            "agent": "bull",
            "bull_score":  bull.get("overall_bull_score", 50),
            "bull_thesis": bull.get("bull_thesis", ""),
            "bull_points": bull.get("bull_points", []),
        })
        yield _emit("progress", {
            "step": 4, "total": 6, "pct": 55,
            "msg": f"Bull score: {bull.get('overall_bull_score', '?')}/100 ✓ — Bear agent scanning risks…",
        })

        bear = run_bear_agent(fund_summary, news_text)
        yield _emit("partial", {
            "agent": "bear",
            "bear_score":  bear.get("overall_bear_score", 50),
            "bear_thesis": bear.get("bear_thesis", ""),
            "bear_points": bear.get("bear_points", []),
        })
        yield _emit("progress", {
            "step": 5, "total": 6, "pct": 70,
            "msg": f"Bear score: {bear.get('overall_bear_score', '?')}/100 ✓ — judge writing final verdict…",
        })

        t2 = time.time()
        yield _emit("progress", {
            "step": 5, "total": 6, "pct": 75,
            "msg": f"Agents done in {t2 - t1:.1f}s — running decision engine…",
        })

        # ── Stage 3: Scoring → Validation → Judge (serial) ────────
        fv_upside    = fv.get("primary", {}).get("upside", 0)
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

        yield _emit("progress", {
            "step": 5, "total": 6, "pct": 85,
            "msg": f"Verdict: {validated.get('verdict')} — judge writing reasoning…",
        })

        verdict = run_judge_agent(
            bull, bear, sent,
            verdict_data=validated,
            fundamentals_data=fund_data,
        )

        # ── Save prediction ────────────────────────────────────────
        yield _emit("progress", {"step": 6, "total": 6, "pct": 95, "msg": "Saving prediction…"})
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

        t3 = time.time()
        total_s = round(t3 - t0, 1)
        print(f"[API Async] {ticker}: stage1={t1-t0:.1f}s  stage2={t2-t1:.1f}s  "
              f"stage3={t3-t2:.1f}s  total={total_s}s")

        yield _emit("progress", {
            "step": 6, "total": 6, "pct": 100,
            "msg": f"Analysis complete in {total_s}s ✓",
        })

        # ── Final done event with full result payload ──────────────
        result = _safe_json({
            "ticker":     ticker.upper(),
            "info":       info,
            "raw":        raw,
            "fv":         fv,
            "news_items": news_items,
            "sent":       sent,
            "bull":       bull,
            "bear":       bear,
            "verdict":    verdict,
            "fund_data":  fund_data,
            "validated":  validated,
            "timings": {
                "stage1_data_news":   round(t1 - t0, 1),
                "stage2_llm_agents":  round(t2 - t1, 1),
                "stage3_judge_score": round(t3 - t2, 1),
                "total":              total_s,
            },
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
