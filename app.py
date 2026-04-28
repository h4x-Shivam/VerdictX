import streamlit as st
import json
import time
import yfinance as yf
import plotly.graph_objects as go
from main import (
    get_basic_data, get_news, get_news_text,
    analyze_sentiment, run_bull_agent, run_bear_agent,
    run_judge_agent, save_prediction, check_outcomes,
    calculate_accuracy, get_prediction_history,
    generate_pdf_report, get_days_until_eval,
    compute_fundamentals_score, compute_final_score,
    validate_and_adjust,
    fmt_rupee, fmt_cr, fmt_pct,
)

st.set_page_config(
    page_title="StockAI — NSE Research",
    layout="wide",
    initial_sidebar_state="collapsed"
)

for k, v in {
    "dark_mode": True,
    "page": "home",
    "analysis_data": None,
    "ticker_val": "",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

DM = st.session_state.dark_mode

if DM:
    BG     = "#07080f"
    BG2    = "#0c0e18"
    CARD   = "#0f1120"
    CARD2  = "#141628"
    BORDER = "#1a1e30"
    BDR2   = "#22273d"
    TPRI   = "#eef0ff"
    TSEC   = "#7c85a8"
    TMUTE  = "#363d5c"
    INPUT  = "#0c0e18"
else:
    BG     = "#f2f3f9"
    BG2    = "#eaecf5"
    CARD   = "#ffffff"
    CARD2  = "#f5f6fb"
    BORDER = "#dde0ef"
    BDR2   = "#c8cce0"
    TPRI   = "#090b18"
    TSEC   = "#50587a"
    TMUTE  = "#9ba3c0"
    INPUT  = "#ffffff"

GREEN  = "#00e5a0"
RED    = "#ff3d6b"
YELLOW = "#ffc400"
ACCENT = "#6366f1"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');

*   {{ box-sizing:border-box; margin:0; padding:0; }}
html,body,[class*="css"],.stApp {{
  font-family:'Outfit',sans-serif !important;
  background:{BG} !important;
  color:{TPRI} !important;
}}
#MainMenu,footer,header {{ visibility:hidden !important; }}
section[data-testid="stSidebar"] {{ display:none !important; }}
.block-container {{ padding:0 !important; max-width:100% !important; }}
div[data-testid="stToolbar"] {{ display:none !important; }}
[data-testid="stDecoration"] {{ display:none !important; }}
::-webkit-scrollbar {{ width:4px; }}
::-webkit-scrollbar-track {{ background:{BG}; }}
::-webkit-scrollbar-thumb {{ background:{BDR2}; border-radius:4px; }}

.stTextInput>div>div>input {{
  background:{INPUT} !important; border:1.5px solid {BDR2} !important;
  border-radius:12px !important; color:{TPRI} !important;
  padding:.8rem 1rem !important; font-size:.95rem !important;
  font-family:'Outfit',sans-serif !important; height:50px !important;
  transition:border-color .2s !important;
}}
.stTextInput>div>div>input:focus {{
  border-color:{ACCENT} !important;
  box-shadow:0 0 0 3px rgba(99,102,241,.12) !important;
}}
.stTextInput>div>div>input::placeholder {{ color:{TMUTE} !important; }}
.stTextInput label {{ display:none !important; }}
.stTextInput>div {{ border:none !important; }}

.stButton>button {{
  font-family:'Outfit',sans-serif !important; font-weight:600 !important;
  border-radius:10px !important; border:none !important;
  cursor:pointer !important; transition:all .18s ease !important;
}}
.stButton>button:hover {{
  transform:translateY(-1px) !important; filter:brightness(1.08) !important;
}}

.stProgress>div>div>div>div {{
  background:linear-gradient(90deg,{ACCENT},{GREEN}) !important;
  border-radius:4px !important;
}}
.stProgress>div>div>div {{
  background:{BORDER} !important; border-radius:4px !important; height:3px !important;
}}

@keyframes fadeUp {{
  from {{ opacity:0; transform:translateY(16px); }}
  to   {{ opacity:1; transform:translateY(0); }}
}}
@keyframes blink {{
  0%,100% {{ opacity:1; }} 50% {{ opacity:.3; }}
}}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def fp(v, is_indian=True):
    if v is None: return "N/A"
    sym = "₹" if is_indian else "$"
    try: return f"{sym}{float(v):,.2f}"
    except: return str(v)

def vc(v):
    # 5-tier color mapping
    return {
        "STRONG BUY": "#00ffb3",   # brighter teal for STRONG BUY
        "BUY":        GREEN,
        "HOLD":       YELLOW,
        "SELL":       RED,
        "STRONG SELL":"#ff1744",   # deeper red for STRONG SELL
    }.get(v, TSEC)

def verdict_label(v):
    return {
        "STRONG BUY":  "Exceptional Opportunity",
        "BUY":         "Positive Signal — Consider Buying",
        "HOLD":        "Hold — Neutral Outlook",
        "SELL":        "Weak Signal — Consider Exiting",
        "STRONG SELL": "High Risk — Strong Exit Signal",
    }.get(v, "")

def verdict_bg(v):
    return {
        "STRONG BUY":  "rgba(0,255,179,.10)",
        "BUY":         "rgba(0,229,160,.08)",
        "HOLD":        "rgba(255,196,0,.08)",
        "SELL":        "rgba(255,61,107,.08)",
        "STRONG SELL": "rgba(255,23,68,.12)",
    }.get(v, "rgba(99,102,241,.06)")

def verdict_border(v):
    return {
        "STRONG BUY":  "rgba(0,255,179,.35)",
        "BUY":         "rgba(0,229,160,.22)",
        "HOLD":        "rgba(255,196,0,.22)",
        "SELL":        "rgba(255,61,107,.22)",
        "STRONG SELL": "rgba(255,23,68,.35)",
    }.get(v, BORDER)

def ring(pct, color, size=92):
    r = 34; c = size//2
    circ = 2*3.14159*r
    f = circ*(max(0,min(100,pct))/100); g = circ-f
    return f"""<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  <circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="{BDR2}" stroke-width="6"/>
  <circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="{color}"
    stroke-width="6" stroke-linecap="round"
    stroke-dasharray="{f:.1f} {g:.1f}" transform="rotate(-90 {c} {c})"/>
  <text x="{c}" y="{c-3}" text-anchor="middle"
    font-family="Outfit,sans-serif" font-weight="800" font-size="14" fill="{TPRI}">{pct}%</text>
  <text x="{c}" y="{c+11}" text-anchor="middle"
    font-family="Outfit,sans-serif" font-size="8" fill="{TSEC}">confidence</text>
</svg>"""

def card_wrap(content, pad="1.3rem 1.5rem", radius="15px"):
    return (f'<div style="background:{CARD};border:1px solid {BORDER};'
            f'border-radius:{radius};padding:{pad};">{content}</div>')


# ─────────────────────────────────────────────────────────────────
# HOME PAGE
# ─────────────────────────────────────────────────────────────────

def render_home():
    a, b = st.columns([11, 1])
    with a:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;
             padding:1.2rem 2.5rem;border-bottom:1px solid {BORDER};">
          <div style="width:32px;height:32px;
               background:linear-gradient(135deg,{ACCENT},{GREEN});
               border-radius:9px;display:flex;align-items:center;
               justify-content:center;font-size:15px;">📈</div>
          <div>
            <div style="font-weight:800;font-size:.95rem;color:{TPRI};">StockAI</div>
            <div style="font-size:.62rem;color:{TMUTE};">NSE Stock Analysis</div>
          </div>
        </div>""", unsafe_allow_html=True)
    with b:
        st.markdown("<div style='padding-top:.85rem;'>", unsafe_allow_html=True)
        if st.button("☀️" if DM else "🌙", key="th_home"):
            st.session_state.dark_mode = not DM; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    hero_grad = (
        f"radial-gradient(ellipse 100% 70% at 50% -5%,rgba(99,102,241,.22) 0%,transparent 60%),"
        f"radial-gradient(ellipse 55% 45% at 90% 95%,rgba(0,229,160,.1) 0%,transparent 55%)"
        if DM else
        f"radial-gradient(ellipse 100% 60% at 50% -5%,rgba(99,102,241,.1) 0%,transparent 60%)"
    )
    st.markdown(f"""
    <div style="min-height:56vh;display:flex;flex-direction:column;
         align-items:center;justify-content:center;text-align:center;
         padding:5rem 1rem 2rem;background:{hero_grad};">
      <div style="font-size:clamp(2.6rem,5.5vw,4.8rem);font-weight:900;
           letter-spacing:-.03em;color:{TPRI};line-height:1.05;">Smart Analysis.</div>
      <div style="font-size:clamp(2.6rem,5.5vw,4.8rem);font-weight:900;
           letter-spacing:-.03em;line-height:1.05;margin-bottom:1.4rem;
           background:linear-gradient(90deg,{ACCENT},{GREEN});
           -webkit-background-clip:text;-webkit-text-fill-color:transparent;">Smarter Decisions.</div>
      <div style="font-size:1rem;color:{TSEC};line-height:1.7;max-width:360px;">
        NSE-powered AI research on any Indian stock — in seconds.
      </div>
    </div>""", unsafe_allow_html=True)

    _, sc, _ = st.columns([1, 5, 1])
    with sc:
        c1, c2 = st.columns([5, 1], gap="small")
        with c1:
            ticker_home = st.text_input("Ticker", "",
                placeholder="🔍  e.g. IRCTC, TCS, RELIANCE, LENSKART",
                key="ht", label_visibility="collapsed")
        with c2:
            st.markdown(f"""<style>
            div[data-testid="column"]:nth-child(2) .stButton>button {{
              background:linear-gradient(135deg,{ACCENT},#8b5cf6) !important;
              color:#fff !important; height:50px !important;
              width:100% !important; font-size:.95rem !important;
              box-shadow:0 4px 18px rgba(99,102,241,.3) !important;
              margin-top:-1px !important;
            }}</style>""", unsafe_allow_html=True)
            st.markdown("<div style='margin-top:1px;'></div>", unsafe_allow_html=True)
            if st.button("Analyze →", key="ha"):
                t = ticker_home.strip() or "IRCTC"
                st.session_state.ticker_val = t
                st.session_state.page = "loading"
                st.rerun()

    st.markdown(f'<div style="text-align:center;font-size:.72rem;color:{TMUTE};'
                f'margin:.9rem 0 .5rem;text-transform:uppercase;letter-spacing:.07em;'
                f'font-weight:500;">Popular searches</div>', unsafe_allow_html=True)
    _, cc, _ = st.columns([1, 7, 1])
    with cc:
        chips = ["IRCTC","TCS","RELIANCE","INFY","HDFC","WIPRO","LENSKART","AAPL","NVDA"]
        cols  = st.columns(len(chips))
        for i, ch in enumerate(chips):
            with cols[i]:
                st.markdown(f"""<style>
                div[data-testid="column"]:nth-child({i+1}) .stButton>button {{
                  background:{CARD} !important; color:{TSEC} !important;
                  border:1px solid {BDR2} !important;
                  padding:.35rem .7rem !important; font-size:.78rem !important;
                  font-weight:500 !important; width:100% !important;
                }}</style>""", unsafe_allow_html=True)
                if st.button(ch, key=f"c_{ch}"):
                    st.session_state.ticker_val = ch
                    st.session_state.page = "loading"
                    st.rerun()

    st.markdown("<div style='height:2.5rem'></div>", unsafe_allow_html=True)
    _, fc, _ = st.columns([1, 8, 1])
    with fc:
        f1, f2, f3 = st.columns(3, gap="medium")
        feats = [
            (f"rgba(99,102,241,.12)", f"rgba(99,102,241,.3)", "🏛️",
             "Real NSE Data",
             "Live prices, VWAP, delivery %, 52-week range — straight from NSE's own endpoints."),
            (f"rgba(0,229,160,.08)",  f"rgba(0,229,160,.25)",  "🤖",
             "Multi-Agent AI",
             "Bull, Bear, and Judge agents debate the stock using actual data, not guesses."),
            (f"rgba(255,196,0,.08)",  f"rgba(255,196,0,.25)",  "📰",
             "Filtered News",
             "MoneyControl, Economic Times, Mint — filtered to only show relevant articles."),
        ]
        for col, (bg, bc, icon, title, desc) in zip([f1, f2, f3], feats):
            with col:
                st.markdown(f"""
                <div style="background:{bg};border:1px solid {bc};
                     border-radius:16px;padding:1.5rem 1.4rem;">
                  <div style="width:48px;height:48px;background:{'rgba(0,0,0,.2)' if DM else 'rgba(255,255,255,.6)'};
                       border-radius:12px;display:flex;align-items:center;justify-content:center;
                       font-size:1.5rem;margin-bottom:.9rem;">{icon}</div>
                  <div style="font-weight:700;font-size:.95rem;color:{TPRI};margin-bottom:.45rem;">{title}</div>
                  <div style="font-size:.82rem;color:{TSEC};line-height:1.65;">{desc}</div>
                </div>""", unsafe_allow_html=True)

    st.markdown(f'<div style="text-align:center;font-size:.7rem;color:{TMUTE};'
                f'margin-top:2.5rem;padding-bottom:1.5rem;">'
                f'⚠️ For informational purposes only. Not financial advice.</div>',
                unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# LOADING PAGE — animated steps with time estimates (Fix 4)
# ─────────────────────────────────────────────────────────────────

def render_loading():
    ticker = st.session_state.ticker_val

    st.markdown(f"""
    <div style="min-height:100vh;display:flex;flex-direction:column;
         align-items:center;justify-content:center;padding:2rem;
         background:radial-gradient(ellipse 70% 50% at 50% 50%,
           rgba(99,102,241,.14) 0%,transparent 65%);">
      <div style="width:60px;height:60px;
           background:linear-gradient(135deg,{ACCENT},{GREEN});
           border-radius:16px;display:flex;align-items:center;
           justify-content:center;font-size:1.7rem;margin-bottom:1.3rem;
           box-shadow:0 8px 28px rgba(99,102,241,.35);">📊</div>
      <div style="font-size:1.5rem;font-weight:800;color:{TPRI};
           letter-spacing:-.02em;margin-bottom:.35rem;">
        Analyzing {ticker.upper()}</div>
      <div style="font-size:.88rem;color:{TSEC};margin-bottom:2rem;">
        Multi-agent AI building your research report…</div>
    </div>""", unsafe_allow_html=True)

    # Steps with estimated durations shown to user
    steps = [
        ("🔍", "Researching company data…",                     "~3s"),
        ("📰", "Fetching news from MoneyControl, ET, Mint…",    "~5s"),
        ("🧠", "Analyzing market sentiment…",                   "~15s"),
        ("🟢", "Bull agent scanning positive signals…",         "~20s"),
        ("🔴", "Bear agent scanning risks and red flags…",      "~20s"),
        ("⚖️",  "Neutral agent making final report…",           "~20s"),
        ("📋", "Preparing your research report…",               "~2s"),
    ]

    step_ph = st.empty()
    prog_ph = st.progress(0)
    stat_ph = st.empty()

    def show_steps(active):
        rows = ""
        for i, (icon, label, est) in enumerate(steps):
            done  = i < active
            cur   = i == active
            opac  = "1" if (cur or done) else ".35"
            bg    = f"rgba(99,102,241,.09)" if cur else "transparent"
            brd   = f"1px solid rgba(99,102,241,.2)" if cur else f"1px solid transparent"
            dot_bg= GREEN if done else (ACCENT if cur else BDR2)
            sym   = "✓" if done else icon
            fw    = "800" if cur else ("600" if done else "400")
            fc2   = TPRI if cur else (TSEC if done else TMUTE)
            anim_css = "animation:blink 1.2s ease infinite;" if cur else ""
            # Show time estimate only on current step
            est_html = (
                f'<span style="font-size:.72rem;color:{TMUTE};margin-left:auto;">{est}</span>'
                if cur else ""
            )
            rows += (
                f'<div style="display:flex;align-items:center;gap:13px;'
                f'padding:.65rem 1rem;border-radius:10px;'
                f'background:{bg};border:{brd};opacity:{opac};transition:all .3s;">'
                f'<div style="{anim_css}width:32px;height:32px;flex-shrink:0;'
                f'background:{dot_bg};border-radius:50%;'
                f'display:flex;align-items:center;justify-content:center;'
                f'font-size:.78rem;font-weight:700;color:#fff;">{sym}</div>'
                f'<div style="font-size:.88rem;font-weight:{fw};color:{fc2};flex:1;">{label}</div>'
                f'{est_html}'
                f'</div>'
            )
        step_ph.markdown(
            f'<div style="max-width:480px;margin:0 auto;'
            f'background:{CARD};border:1px solid {BORDER};'
            f'border-radius:18px;padding:1rem .6rem;'
            f'margin-top:-55vh;">{rows}</div>',
            unsafe_allow_html=True
        )

    # Run pipeline — upgraded decision engine
    show_steps(0); prog_ph.progress(4)
    data = get_basic_data(ticker)
    fund_summary = data["summary"]; raw = data["raw"]; info = data["info"]
    hist = data.get("hist"); fv = data.get("fair_value", {})

    # Component 1: Compute fundamentals score
    fund_data = compute_fundamentals_score(info, raw)

    show_steps(1); prog_ph.progress(18)
    news_items = get_news(info.get("company_name", ""), ticker)
    news_text  = get_news_text(news_items)

    show_steps(2); prog_ph.progress(34)
    sent = analyze_sentiment(news_text)

    show_steps(3); prog_ph.progress(52)
    bull = run_bull_agent(fund_summary, news_text)

    show_steps(4); prog_ph.progress(68)
    bear = run_bear_agent(fund_summary, news_text)

    # Component 2: Weighted scoring engine
    fv_upside = fv.get("primary", {}).get("upside", 0)
    score_result = compute_final_score(
        bull_score=bull.get("overall_bull_score", 50),
        bear_score=bear.get("overall_bear_score", 50),
        sent_score=sent.get("score", 0),
        fundamentals_score=fund_data["score"],
        fair_value_upside=fv_upside,
        data_completeness=fund_data["data_completeness"],
    )

    # Component 3: Validation layer
    validated = validate_and_adjust(
        score_result=score_result,
        fundamentals_score=fund_data["score"],
        bull_score=bull.get("overall_bull_score", 50),
        bear_score=bear.get("overall_bear_score", 50),
        data_completeness=fund_data["data_completeness"],
    )

    show_steps(5); prog_ph.progress(84)
    # Component 5: Judge writes reasoning for pre-computed verdict
    verdict = run_judge_agent(bull, bear, sent,
                              verdict_data=validated,
                              fundamentals_data=fund_data)

    show_steps(6); prog_ph.progress(100)
    cur_price = raw.get("currentPrice") or 0
    save_prediction(ticker, verdict,
                    bull.get("overall_bull_score", 50),
                    bear.get("overall_bear_score", 50),
                    float(cur_price),
                    fundamentals_score=fund_data["score"],
                    scores=validated.get("scores"))
    check_outcomes()

    stat_ph.markdown(
        f'<div style="text-align:center;color:{GREEN};font-weight:700;'
        f'font-size:.88rem;margin-top:.5rem;">✓ Analysis complete!</div>',
        unsafe_allow_html=True
    )
    time.sleep(0.6)

    st.session_state.analysis_data = {
        "info": info, "fund": fund_summary, "raw": raw,
        "hist": hist, "fv": fv,
        "news_items": news_items, "sent": sent,
        "bull": bull, "bear": bear, "verdict": verdict,
        "fund_data": fund_data, "validated": validated,
    }
    st.session_state.page = "results"
    st.rerun()


# ─────────────────────────────────────────────────────────────────
# RESULTS PAGE
# ─────────────────────────────────────────────────────────────────

def render_results(ticker):
    d       = st.session_state.analysis_data
    info    = d["info"];   raw  = d["raw"];    hist = d["hist"]
    fv      = d.get("fv", {}); fv_p = fv.get("primary", {})
    news    = d["news_items"]; sent = d["sent"]
    bull    = d["bull"];   bear = d["bear"];   verd = d["verdict"]

    vv   = verd.get("verdict", "HOLD")
    cf   = verd.get("confidence", 50)
    rsk  = verd.get("risk", "MEDIUM")
    tf   = verd.get("timeframe", "short-term")
    rsn  = verd.get("final_reasoning", "")
    bkd  = verd.get("signal_breakdown", "")
    krc  = verd.get("key_catalyst", "")
    krk  = verd.get("key_risk", "")
    tgt  = verd.get("target_upside_pct")
    vc_  = vc(vv)

    cur   = raw.get("currentPrice")
    # FIX 2: use computed pchange from main.py (now always reliable)
    pch   = raw.get("pchange", 0) or 0
    ch_   = raw.get("change",  0) or 0
    cc_   = GREEN if pch >= 0 else RED
    csn   = "+" if pch >= 0 else ""

    bs    = bull.get("overall_bull_score", 50)
    ber   = bear.get("overall_bear_score", 50)

    sv    = sent.get("sentiment", "N/A")
    ss    = sent.get("score", 0)
    sc_   = {"POSITIVE":GREEN,"NEGATIVE":RED,"NEUTRAL":YELLOW,"MIXED":YELLOW}.get(sv, TSEC)
    rc_   = {"LOW":GREEN,"MEDIUM":YELLOW,"HIGH":RED}.get(rsk, TSEC)

    # Real fundamentals score from data-driven engine
    fund_data = d.get("fund_data", {})
    fund_score = fund_data.get("score", 50) if fund_data else 50
    h_s   = round(fund_score / 10, 1)
    h_c   = GREEN if h_s >= 7 else (YELLOW if h_s >= 4 else RED)

    # Scores breakdown from validated result
    validated = d.get("validated", {})
    scores_dict = validated.get("scores", verd.get("scores", {}))
    validation_applied = validated.get("validation_applied", verd.get("validation_applied", []))
    composite_score = validated.get("composite", verd.get("composite", 0))

    company  = info.get("company_name", ticker)
    sector   = info.get("sector", "")
    isin     = info.get("isin", "")
    src      = info.get("data_source", "")
    is_indian = True  # all NSE stocks

    # ── Top bar ──
    tb1, tb2, tb3 = st.columns([2, 6, 2])
    with tb1:
        st.markdown(f"<div style='padding:1rem 0 0 2rem;'>", unsafe_allow_html=True)
        if st.button("← Back", key="bk"):
            st.session_state.page = "home"
            st.session_state.analysis_data = None
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with tb2:
        st.markdown(f"""
        <div style="display:flex;align-items:center;justify-content:center;
             gap:10px;padding:1.1rem 0;border-bottom:1px solid {BORDER};">
          <div style="width:28px;height:28px;
               background:linear-gradient(135deg,{ACCENT},{GREEN});
               border-radius:8px;display:flex;align-items:center;
               justify-content:center;font-size:13px;">📈</div>
          <span style="font-weight:700;font-size:.92rem;color:{TPRI};">New Analysis</span>
          <span style="font-size:.7rem;color:{TMUTE};background:{BORDER};
               border-radius:20px;padding:2px 10px;">{src}</span>
        </div>""", unsafe_allow_html=True)
    with tb3:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"<div style='padding:.9rem 0 0 0;text-align:right;'>", unsafe_allow_html=True)
            if st.button("☀️" if DM else "🌙", key="th_r"):
                st.session_state.dark_mode = not DM; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with c2:
            # FIX 5: PDF download button
            st.markdown(f"<div style='padding:.9rem 0 0 0;'>", unsafe_allow_html=True)
            try:
                pdf_bytes = generate_pdf_report(
                    ticker, d, sent, bull, bear, verd, news
                )
                st.download_button(
                    label="📄 PDF",
                    data=pdf_bytes,
                    file_name=f"StockAI_{ticker}_{vv}.pdf",
                    mime="application/pdf",
                    key="pdf_dl",
                )
            except Exception as e:
                st.caption(f"PDF unavailable")
            st.markdown("</div>", unsafe_allow_html=True)

    pad = "padding:1.4rem 2.5rem 0;"

    # ── Header ──
    st.markdown(f"<div style='{pad}'>", unsafe_allow_html=True)
    h1, h2 = st.columns([3, 2], gap="large")
    with h1:
        tags = ""
        for t, tbg, tc, tb in [
            (sector, f"rgba(99,102,241,.1)", "#a5b4fc" if DM else "#4f46e5", "rgba(99,102,241,.25)"),
            (isin,   f"rgba(0,229,160,.07)", "#6ee7b7" if DM else "#059669", "rgba(0,229,160,.2)"),
        ]:
            if t:
                tags += (f'<span style="background:{tbg};color:{tc};border:1px solid {tb};'
                         f'border-radius:6px;padding:3px 10px;font-size:.72rem;'
                         f'font-weight:600;">{t}</span> ')

        st.markdown(f"""
        <div style="display:flex;gap:14px;align-items:flex-start;margin-bottom:.9rem;">
          <div style="width:54px;height:54px;flex-shrink:0;
               background:{'linear-gradient(135deg,#181a2e,#1e2040)' if DM else 'linear-gradient(135deg,#ede9fe,#ddd6fe)'};
               border-radius:14px;border:1px solid {BDR2};
               display:flex;align-items:center;justify-content:center;font-size:1.4rem;">🏢</div>
          <div>
            <div style="font-size:1.55rem;font-weight:900;color:{TPRI};
                 letter-spacing:-.025em;">{company}</div>
            <div style="font-size:.82rem;color:{TSEC};margin:2px 0 7px;">
              NSE: {info.get('nse_symbol', ticker)}</div>
            <div style="display:flex;gap:6px;flex-wrap:wrap;">{tags}</div>
          </div>
        </div>
        <div style="font-size:.68rem;color:{TMUTE};text-transform:uppercase;
             letter-spacing:.1em;margin-bottom:4px;">Current Price</div>
        <div style="font-size:2.3rem;font-weight:900;color:{TPRI};
             letter-spacing:-.03em;line-height:1;">{fp(cur)}</div>
        <div style="font-size:.86rem;color:{cc_};margin-top:5px;font-weight:500;">
          {csn}{ch_:.2f} ({csn}{pch:.2f}%) Today
        </div>""", unsafe_allow_html=True)

    with h2:
        vbg_  = verdict_bg(vv)
        vbrd_ = verdict_border(vv)
        slbl  = verdict_label(vv)
        tgt_html = f'<div style="font-size:.75rem;color:{TSEC};margin-top:8px;">Target: {csn}{tgt:.1f}%</div>' if tgt else ''
        # STRONG tiers get a subtle glow shadow
        glow = ""
        if vv == "STRONG BUY":
            glow = "box-shadow:0 0 28px rgba(0,255,179,.18);"
        elif vv == "STRONG SELL":
            glow = "box-shadow:0 0 28px rgba(255,23,68,.18);"
        # Show short display label — STRONG BUY becomes 2 lines
        display_vv = vv.replace(" ", "<br>") if " " in vv else vv
        font_size = "2.1rem" if " " in vv else "2.8rem"
        st.markdown(f"""<div style="background:{vbg_};border:1px solid {vbrd_};border-radius:18px;
             padding:1.5rem 1.7rem;display:flex;align-items:center;
             justify-content:space-between;height:100%;{glow}">
          <div>
            <div style="font-size:{font_size};font-weight:900;color:{vc_};
                 letter-spacing:-.03em;line-height:1.1;">{display_vv}</div>
            <div style="font-size:.78rem;color:{vc_};opacity:.85;
                 font-weight:500;margin-top:7px;line-height:1.4;">{slbl}</div>{tgt_html}
          </div>
          {ring(cf, vc_, size=94)}
        </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Metrics + Chart ──
    st.markdown(f"<div style='{pad}'>", unsafe_allow_html=True)
    m1, m2 = st.columns([2, 3], gap="large")
    with m1:
        rows_data = [
            ("Market Cap",   fmt_cr(info.get("market_cap"))),
            ("P/E (TTM)",    f"{info.get('trailing_pe'):.2f}" if info.get("trailing_pe") else "N/A"),
            ("P/B Ratio",    f"{info.get('pb_ratio'):.2f}"    if info.get("pb_ratio")    else "N/A"),
            ("EPS (TTM)",    fp(info.get("trailing_eps"))),
            ("Revenue",      fmt_cr(info.get("total_revenue"))),
            ("VWAP",         fp(raw.get("vwap")) if raw.get("vwap") else "N/A (market closed)"),
            ("Delivery %",   f"{info.get('delivery_pct')}%" if info.get("delivery_pct") else "N/A"),
            ("Div Yield",    fmt_pct(info.get("dividend_yield"))),
        ]
        rows_html = "".join([f"""
          <div style="display:flex;justify-content:space-between;align-items:center;
               padding:.6rem 0;border-bottom:1px solid {BORDER};">
            <span style="font-size:.8rem;color:{TSEC};">{k}</span>
            <span style="font-size:.84rem;font-weight:600;color:{TPRI};
                 font-family:'JetBrains Mono',monospace;">{v}</span>
          </div>""" for k, v in rows_data])
        st.markdown(f"""
        <div style="background:{CARD};border:1px solid {BORDER};
             border-radius:15px;padding:.9rem 1.1rem;">
          <div style="font-size:.7rem;color:{TMUTE};text-transform:uppercase;
               letter-spacing:.09em;font-weight:600;margin-bottom:.3rem;">Key Metrics</div>
          {rows_html}
        </div>""", unsafe_allow_html=True)

    with m2:
        if hist is not None and not hist.empty:
            cc2 = GREEN if pch >= 0 else RED
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist.index, y=hist["Close"], mode="lines",
                line=dict(color=cc2, width=2.2),
                fill="tozeroy",
                fillcolor=f"rgba({'0,229,160' if cc2==GREEN else '255,61,107'},.055)"
            ))
            fig.update_layout(
                plot_bgcolor=CARD, paper_bgcolor=CARD,
                xaxis=dict(showgrid=False, tickfont=dict(size=8,color=TMUTE), showline=False, zeroline=False),
                yaxis=dict(showgrid=True, gridcolor=BORDER, tickfont=dict(size=8,color=TMUTE),
                           side="right", showline=False, zeroline=False),
                margin=dict(l=0,r=4,t=8,b=0), height=205, showlegend=False,
            )
            st.markdown(f'<div style="background:{CARD};border:1px solid {BORDER};'
                        f'border-radius:15px;overflow:hidden;">', unsafe_allow_html=True)
            st.plotly_chart(fig, width="stretch")
            st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Metric tiles — FIX 3: Fair Value with method shown ──
    st.markdown(f"<div style='{pad}'>", unsafe_allow_html=True)
    t1, t2, t3, t4 = st.columns(4, gap="medium")
    fv_val    = fv_p.get("value")
    fv_upside = fv_p.get("upside", 0)
    fv_method = fv_p.get("method", "")
    fv_arrow  = "↑" if fv_upside >= 0 else "↓"
    fv_color  = GREEN if fv_upside >= 0 else RED

    tiles = [
        ("FAIR VALUE (EST.)",   fp(fv_val) if fv_val else "N/A",
         f"{fv_arrow}{abs(fv_upside):.2f}% {'Upside' if fv_upside>=0 else 'Downside'}",
         fv_color,
         fv_method[:35] + ("…" if len(fv_method)>35 else "")),

        ("MARKET SENTIMENT",    sv.title() if sv!="N/A" else "N/A",
         f"Score: {ss:+d}", sc_, ""),

        ("RISK LEVEL",          rsk,
         {"LOW":"Low Risk","MEDIUM":"Med Risk","HIGH":"High Risk"}.get(rsk,""), rc_, ""),

        ("FINANCIAL HEALTH",    f"{h_s}/10",
         "Strong" if h_s>=7 else "Moderate" if h_s>=5 else "Weak", h_c, ""),
    ]
    for col, (lbl, val, sub, clr, hint) in zip([t1,t2,t3,t4], tiles):
        with col:
            hint_html = (f'<div style="font-size:.65rem;color:{TMUTE};margin-top:4px;">{hint}</div>'
                         if hint else "")
            st.markdown(f"""
            <div style="background:{CARD};border:1px solid {BORDER};
                 border-radius:14px;padding:1rem 1.1rem;">
              <div style="font-size:.65rem;color:{TMUTE};text-transform:uppercase;
                   letter-spacing:.1em;font-weight:600;margin-bottom:.45rem;">{lbl}</div>
              <div style="font-size:1.25rem;font-weight:800;color:{TPRI};
                   line-height:1.1;letter-spacing:-.01em;">{val}</div>
              <div style="font-size:.75rem;color:{clr};font-weight:600;margin-top:4px;">{sub}</div>
              {hint_html}
            </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Score Breakdown (NEW) ──
    if scores_dict:
        st.markdown(f"<div style='{pad}'>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:{CARD};border:1px solid {BORDER};
             border-radius:15px;padding:1.1rem 1.3rem;">
          <div style="font-weight:700;font-size:.88rem;color:{TPRI};margin-bottom:.7rem;
               display:flex;align-items:center;gap:8px;">
            🧮 Decision Engine Scores
            <span style="font-size:.68rem;color:{TMUTE};background:{BORDER};
                 border-radius:20px;padding:2px 9px;">Composite: {composite_score}</span>
          </div>""", unsafe_allow_html=True)

        score_items = [
            ("Fundamentals", scores_dict.get("fundamentals", 0), "35%", ACCENT),
            ("Bull Agent", scores_dict.get("bull", 0), "20%", GREEN),
            ("Bear Agent", scores_dict.get("bear", 0), "20%", RED),
            ("Sentiment", scores_dict.get("sentiment", 0), "15%", YELLOW),
            ("Fair Value", scores_dict.get("fair_value", 0), "10%", "#8b5cf6"),
        ]
        bars_html = ""
        for label, val, weight, color in score_items:
            pct = max(0, min(100, val))
            bars_html += f"""
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:.5rem;">
              <div style="width:100px;font-size:.75rem;color:{TSEC};flex-shrink:0;">{label} <span style="color:{TMUTE};font-size:.65rem;">({weight})</span></div>
              <div style="flex:1;height:8px;background:{BORDER};border-radius:4px;overflow:hidden;">
                <div style="width:{pct}%;height:100%;background:{color};border-radius:4px;transition:width .3s;"></div>
              </div>
              <div style="width:40px;font-size:.75rem;font-weight:600;color:{TPRI};text-align:right;
                   font-family:'JetBrains Mono',monospace;">{val:.0f}</div>
            </div>"""

        st.markdown(f"<div style='padding:.3rem 0;'>{bars_html}</div>", unsafe_allow_html=True)

        # Data completeness
        dc = scores_dict.get("data_completeness", 0)
        dc_pct = int(dc * 100)
        dc_color = GREEN if dc >= 0.7 else (YELLOW if dc >= 0.5 else RED)
        st.markdown(f"""
          <div style="display:flex;align-items:center;gap:8px;margin-top:.3rem;
               padding-top:.5rem;border-top:1px solid {BORDER};">
            <span style="font-size:.72rem;color:{TMUTE};">Data Completeness:</span>
            <span style="font-size:.75rem;font-weight:700;color:{dc_color};">{dc_pct}%</span>
          </div>""", unsafe_allow_html=True)

        # Validation rules applied
        if validation_applied:
            rules_html = "".join(
                f'<div style="font-size:.7rem;color:{YELLOW};margin-top:3px;">⚠ {rule}</div>'
                for rule in validation_applied
            )
            st.markdown(f"""
              <div style="margin-top:.5rem;padding-top:.5rem;border-top:1px solid {BORDER};">
                <div style="font-size:.68rem;color:{TMUTE};text-transform:uppercase;
                     letter-spacing:.08em;font-weight:600;margin-bottom:3px;">Validation Rules Applied</div>
                {rules_html}
              </div>""", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Summary + Highlights ──
    st.markdown(f"<div style='{pad}'>", unsafe_allow_html=True)
    s1, s2 = st.columns([3, 2], gap="large")
    with s1:
        krc_html = f'<div style="margin-top:.8rem;padding:.7rem;background:{CARD2};border-radius:9px;border:1px solid {BORDER};"><span style="font-size:.72rem;color:{GREEN};font-weight:600;">KEY CATALYST</span><div style="font-size:.8rem;color:{TSEC};margin-top:3px;">{krc}</div></div>' if krc else ""
        krk_html = f'<div style="margin-top:.5rem;padding:.7rem;background:{CARD2};border-radius:9px;border:1px solid {BORDER};"><span style="font-size:.72rem;color:{RED};font-weight:600;">KEY RISK</span><div style="font-size:.8rem;color:{TSEC};margin-top:3px;">{krk}</div></div>' if krk else ""
        st.markdown(f"""
        <div style="background:{CARD};border:1px solid {BORDER};
             border-radius:15px;padding:1.3rem 1.5rem;">
          <div style="font-weight:700;font-size:.88rem;color:{TPRI};margin-bottom:.8rem;">
            AI Analysis Summary</div>
          <div style="font-size:.845rem;color:{TSEC};line-height:1.75;">{rsn}</div>{krc_html}{krk_html}
          <div style="margin-top:.8rem;font-size:.7rem;color:{TMUTE};
               font-family:'JetBrains Mono',monospace;">{bkd}</div>
          <div style="margin-top:.6rem;font-size:.78rem;color:{TSEC};">
            ⏱ Timeframe: <strong style="color:{TPRI};">{tf.title()}</strong></div>
        </div>""", unsafe_allow_html=True)

    with s2:
        bp  = [b.get("point","") for b in bull.get("bull_points",[])[:3]]
        brp = [b.get("point","") for b in bear.get("bear_points",[])[:2]]
        bh  = "".join([f'<div style="display:flex;gap:9px;align-items:flex-start;margin-bottom:.55rem;"><span style="color:{GREEN};flex-shrink:0;margin-top:1px;font-weight:700;">✓</span><span style="font-size:.8rem;color:{TSEC};line-height:1.5;">{p}</span></div>' for p in bp])
        brh = "".join([f'<div style="display:flex;gap:9px;align-items:flex-start;margin-bottom:.55rem;"><span style="color:{RED};flex-shrink:0;margin-top:1px;">△</span><span style="font-size:.8rem;color:{TSEC};line-height:1.5;">{p}</span></div>' for p in brp])
        st.markdown(f"""
        <div style="background:{CARD};border:1px solid {BORDER};
             border-radius:15px;padding:1.3rem 1.5rem;height:100%;">
          <div style="font-weight:700;font-size:.88rem;color:{TPRI};margin-bottom:.8rem;">Highlights</div>
          {bh}
          <div style="border-top:1px solid {BORDER};margin:.6rem 0;"></div>
          {brh}
        </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── News widget — FIX 1: only relevant articles shown, with age labels ──
    st.markdown(f"<div style='{pad}'>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-weight:700;font-size:.88rem;color:{TPRI};margin-bottom:.7rem;
         display:flex;align-items:center;gap:8px;">
      📰 Latest News
      <span style="font-size:.68rem;color:{TMUTE};background:{BORDER};
           border-radius:20px;padding:2px 9px;">{len(news)} relevant articles</span>
    </div>""", unsafe_allow_html=True)

    nc1, nc2 = st.columns(2, gap="medium")
    for i, item in enumerate(news[:8]):
        col  = nc1 if i % 2 == 0 else nc2
        titl = item.get("title","")
        link = item.get("link","#")
        src2 = item.get("source","News")
        age  = item.get("age_label","") or item.get("published","")[:10]
        smry = item.get("summary","")
        src_color = {
            "MoneyControl":"#ff6b35","Economic Times":"#e63946",
            "Mint":"#2563eb","Business Standard":"#7c3aed",
            "Hindu BusinessLine":"#059669","NDTV Profit":"#dc2626",
            "Financial Express":"#0891b2","CNBC TV18":"#9333ea",
            "Zee Business":"#0284c7","Reuters":"#ff8800","Bloomberg":"#2563eb",
        }.get(src2, ACCENT)
        with col:
            st.markdown(f"""
            <a href="{link}" target="_blank" style="text-decoration:none;">
            <div style="background:{CARD};border:1px solid {BORDER};border-radius:12px;
                 padding:.9rem 1.1rem;margin-bottom:9px;transition:border-color .15s;"
                 onmouseover="this.style.borderColor='{ACCENT}'"
                 onmouseout="this.style.borderColor='{BORDER}'">
              <div style="display:flex;justify-content:space-between;margin-bottom:.4rem;">
                <span style="font-size:.68rem;font-weight:700;color:{src_color};">{src2}</span>
                <span style="font-size:.68rem;color:{TMUTE};">{age}</span>
              </div>
              <div style="font-size:.82rem;font-weight:500;color:{TPRI};line-height:1.5;">
                {titl[:105]}{'…' if len(titl)>105 else ''}</div>
              {f'<div style="font-size:.74rem;color:{TSEC};margin-top:.3rem;">{smry[:90]}…</div>' if smry else ''}
            </div></a>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Bull vs Bear detail ──
    st.markdown(f"<div style='{pad}'>", unsafe_allow_html=True)
    st.markdown(f'<div style="font-weight:700;font-size:.88rem;color:{TPRI};margin-bottom:.7rem;">Agent Analysis</div>',
                unsafe_allow_html=True)
    ba1, ba2 = st.columns(2, gap="medium")

    def agent_block(pts_key, score_key, data, title, tc, sbg, icon_map, sev_key):
        sc2    = data.get(score_key, "N/A")
        pts    = data.get(pts_key, [])
        thesis = data.get("bull_thesis","") or data.get("bear_thesis","")
        ph = ""
        for pt in pts:
            sev  = pt.get(sev_key, "")
            icon = icon_map.get(sev, "•")
            impact_html = f'<div style="font-size:.7rem;color:{TSEC};margin-top:2px;font-style:italic;">{pt.get("impact","")}</div>' if pt.get("impact") else ""
            ph += f"""<div style="padding:.6rem 0;border-bottom:1px solid {BORDER};">
              <div style="display:flex;gap:8px;align-items:flex-start;">
                <span style="flex-shrink:0;margin-top:1px;">{icon}</span>
                <div>
                  <div style="font-size:.8rem;color:{TPRI};font-weight:500;line-height:1.45;">{pt.get('point','')}</div>
                  <div style="font-size:.68rem;color:{TMUTE};margin-top:2px;">Cited: {pt.get('metric_cited','')}</div>{impact_html}
                </div>
              </div>
            </div>"""
        
        thesis_html = f'<div style="font-size:.78rem;color:{TSEC};margin-bottom:.7rem;font-style:italic;">{thesis}</div>' if thesis else ""
        ph_html = ph if ph else f'<div style="font-size:.8rem;color:{TMUTE};">No data extracted.</div>'

        return f"""<div style="background:{CARD};border:1px solid {BORDER};border-radius:15px;padding:1.1rem 1.3rem;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.7rem;">
            <span style="font-weight:700;font-size:.88rem;color:{tc};">{title}</span>
            <span style="background:{sbg};border-radius:20px;padding:3px 12px;font-size:.75rem;font-weight:700;color:{tc};">{sc2}/100</span>
          </div>{thesis_html}{ph_html}
        </div>"""

    with ba1:
        st.markdown(agent_block("bull_points","overall_bull_score",bull,
            "🟢 Bull Case",GREEN,"rgba(0,229,160,.1)",
            {"STRONG":"💪","MODERATE":"👍","WEAK":"🤏"},"strength"),
            unsafe_allow_html=True)
    with ba2:
        st.markdown(agent_block("bear_points","overall_bear_score",bear,
            "🔴 Bear Case",RED,"rgba(255,61,107,.1)",
            {"SEVERE":"🚨","MODERATE":"⚠️","MINOR":"📌"},"severity"),
            unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Prediction History — FIX 4: show days remaining ──
    history = get_prediction_history()
    if history:
        st.markdown(f"<div style='{pad}'>", unsafe_allow_html=True)
        acc = calculate_accuracy()
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.7rem;">
          <div style="font-weight:700;font-size:.88rem;color:{TPRI};">Recent Predictions</div>
          <div style="font-size:.76rem;color:{TSEC};">
            Accuracy: <strong style="color:{GREEN if acc>=60 else YELLOW if acc>=40 else RED};">{acc}%</strong>
          </div>
        </div>""", unsafe_allow_html=True)

        for entry in reversed(history[-7:]):
            pred     = entry.get("prediction",{})
            ev       = pred.get("verdict","N/A")
            et       = entry.get("ticker","N/A")
            ts       = entry.get("timestamp","")[:10]
            base_px  = entry.get("baseline_price")
            checked  = entry.get("checked",False)
            evc      = vc(ev)
            evbg     = verdict_bg(ev)

            if checked:
                c   = entry.get("correct")
                pct = entry.get("actual_pct_change","?")
                if c is None:
                    out = f'<span style="color:{TMUTE};">⚪ HOLD (not scored)</span>'
                elif c:
                    out = f'<span style="color:{GREEN};font-weight:600;">✅ Correct ({pct}%)</span>'
                else:
                    out = f'<span style="color:{RED};font-weight:600;">❌ Wrong ({pct}%)</span>'
            else:
                # FIX 4: show how many days remaining
                days_left = get_days_until_eval(entry.get("timestamp",""))
                if days_left > 0:
                    out = f'<span style="color:{YELLOW};font-weight:600;">⏳ Awaiting {days_left} more day{"s" if days_left>1 else ""}</span>'
                else:
                    out = f'<span style="color:{YELLOW};font-weight:600;">⏳ Evaluating soon…</span>'

            base_html = (
                f'<span style="font-size:.7rem;color:{TMUTE};margin-left:8px;">@ {fmt_rupee(base_px)}</span>'
                if base_px else ""
            )

            st.markdown(f"""
            <div style="background:{CARD};border:1px solid {BORDER};border-radius:10px;
                 padding:.75rem 1.1rem;margin-bottom:5px;
                 display:flex;justify-content:space-between;align-items:center;">
              <div style="display:flex;align-items:center;gap:10px;">
                <span style="font-weight:700;font-size:.9rem;color:{TPRI};">{et}</span>
                <span style="font-size:.75rem;font-weight:700;color:{evc};
                     background:{evbg};padding:2px 9px;border-radius:20px;">{ev}</span>
                <span style="font-size:.72rem;color:{TMUTE};">{ts}</span>
                {base_html}
              </div>
              <div style="font-size:.82rem;">{out}</div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="text-align:center;font-size:.7rem;color:{TMUTE};
         padding:2rem 0 1.5rem;margin-top:1rem;border-top:1px solid {BORDER};">
      ⚠️ This analysis is for informational purposes only and not financial advice.
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────────────────────────

pg = st.session_state.page
if pg == "home":
    render_home()
elif pg == "loading":
    render_loading()
elif pg == "results":
    if st.session_state.analysis_data:
        render_results(st.session_state.ticker_val)
    else:
        st.session_state.page = "home"; st.rerun()