VerdictX
Most stock analysis tools give you one of three things: raw data, fixed indicators, or news sentiment. They rarely do what actually matters — reason through conflicting signals.
VerdictX is my attempt to fix that.
It's an AI-powered stock research engine built for the Indian market. Instead of one model giving you an answer, it runs a structured debate between a Bull agent and a Bear agent, then lets a neutral Judge synthesize both sides into a final, explainable verdict.

Why I built this
Markets are messy. Simple rules break constantly:

Low P/E doesn't always mean undervalued
Good news doesn't always mean bullish
A strong past doesn't guarantee a strong future

Most tools fail at edge cases — and markets are full of them. VerdictX tries to handle that by comparing perspectives instead of trusting a single signal.

How it works
When you search a stock ticker (say, TCS or IRCTC), VerdictX runs a 7-step pipeline in the background:
1. Financial Data Ingestion
Pulls real-time fundamentals from yfinance — P/E, EPS, Market Cap, Book Value, historical prices, trading metrics.
2. Live News Aggregation
Scrapes high-signal news from MoneyControl, Economic Times, and Mint.
3. Sentiment Analysis
An AI model reads the news, classifies market mood (Positive / Negative / Neutral / Mixed), and generates a baseline sentiment score.
4. Bull Agent
An optimistic, growth-focused LLM builds the bullish case — upside catalysts, expansion signals, reasons to be excited — and produces a Bull Score.
5. Bear Agent
A skeptical, risk-aware LLM argues the other side — weaknesses, red flags, downside risks — and produces a Bear Score.
6. Algorithmic Validation Layer
A deterministic Python layer cross-checks the AI outputs against actual financial data to reduce hallucination risk and generate a Fundamentals Score.
7. Judge Agent
A neutral LLM reads both arguments alongside the validated scores and delivers a final institutional-style verdict — anywhere from Strong Sell to Strong Buy — with full reasoning.

Tech Stack
Backend

Python, Flask, Streamlit
yfinance, Pandas, NumPy
BeautifulSoup / Requests
Ollama / Nvidia NIM API (LLM)

Frontend (in progress)

React, Tailwind CSS, Framer Motion
Server-Sent Events (SSE)


Honest limitations
This is v1, so let me be upfront about where it falls short:

Latency — Running four LLMs sequentially (Sentiment → Bull → Bear → Judge) takes 30–60 seconds per analysis. Async execution is next on the list.
Data fragility — The pipeline depends on yfinance and web scraping. If portals change their structure or enforce rate limits, things can break.
NSE only — Currently hardcoded for the National Stock Exchange. No US or global market support yet.
No technical analysis — The system focuses on fundamentals and news. RSI, MACD, Fibonacci — none of that feeds into the verdict right now.
Surface-level context — It reads recent news and basic fundamentals. It doesn't dig into 50-page earnings transcripts or long-term debt restructuring plans. Yet.


What's coming next

Async AI execution (fixing the latency)
Technical Analyst Agent
Backtesting & accuracy tracking
RAG for earnings transcripts
Premium data integrations
Global market expansion


Run it locally
bashgit clone https://github.com/your-username/verdictx.git
cd verdictx
pip install -r requirements.txt
python api.py
bashcd verdictx-ui
npm install
npm run dev
