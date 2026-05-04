# VerdictX

VerdictX is an intelligent investment research engine built for the Indian stock market. By combining live financial data and real-time news with a unique Multi-Agent AI architecture, VerdictX forces "Bull" and "Bear" AI agents to debate a stock's potential. A neutral "Judge" agent then delivers a final, data-driven verdict, providing users with institutional-grade insights in seconds.

---

## Overview

VerdictX is an experiment in building a more **structured and explainable way to analyze stocks**.

Most tools either:
- dump raw data  
- rely heavily on indicators  
- or follow news sentiment  

They rarely **reason through conflicting signals**.

This project approaches the problem differently.

---

## The Core Idea of VerdictX:

Instead of relying on a single AI that might hallucinate or be biased, VerdictX uses an "AI Debate" framework to analyze stocks.

It forces two AI agents with completely opposing viewpoints—an optimistic Bull and a pessimistic Bear—to argue over the same real-time financial data and news.

A neutral Judge AI then evaluates their arguments to deliver a highly balanced, objective, and institutional-grade stock recommendation, completely free of human emotion or single-model bias.

---

## What it does

Whenever a user searches for a stock ticker (e.g., TCS or IRCTC), VerdictX activates a 7-step analysis pipeline on the backend.

### Financial Data Ingestion  
Connects to yfinance to fetch real-time fundamentals (P/E, EPS, Market Cap, Book Value), historical prices, and trading metrics.

### Live News Aggregation  
Collects the latest, high-signal news from sources like MoneyControl, Economic Times, and Mint.

### Sentiment Analysis  
An AI model evaluates the news to classify market mood (Positive, Negative, Neutral, Mixed) and generate a baseline sentiment score.

### Bull Agent
An optimistic, growth-focused LLM identifies upside catalysts, expansion signals, and bullish arguments — producing a Bull Score.

### Bear Agent
A risk-aware, skeptical LLM analyzes the same data to surface weaknesses, risks, and downside factors — producing a Bear Score.

### Algorithmic Validation Layer
A deterministic Python layer cross-checks AI outputs against actual financial data, generating a Fundamentals Score and reducing hallucination risk.

### Judge Agent
A neutral LLM synthesizes Bull vs Bear arguments with validated scores, delivering a structured, institutional-style report and a final verdict — from Strong Sell to Strong Buy.

---

## Why this approach

Markets are not clean.

Simple rules break often:
- low PE ≠ always undervalued  
- good news ≠ always bullish  
- strong past ≠ strong future  

Most failures come from **edge cases and context**.

This project tries to handle that by:

> comparing perspectives instead of trusting a single signal

---

## Tech stack

**Backend**
- Python
- Streamlit
- Flask
- yfinance
- Pandas & NumPy
- BeautifulSoup / Requests
- Custom data pipeline
- LLM integration (Ollama/Nvidia Nim API)

**Frontend (in progress)**
- React
- Tailwind CSS
- Framer Motion
- Server-Sent Events (SSE)

---

## Current limitations

**Data Reliability Risks:**  
It relies heavily on free data sources like yfinance and web-scraping (for news). If Yahoo Finance or news portals change their web structures or enforce strict rate limits, the data pipeline could temporarily break or provide delayed metrics.

**Analysis Latency:**  
Because it runs a complex multi-agent system (triggering Sentiment, Bull, Bear, and Judge LLMs sequentially), generating a full research report can take 30 to 60 seconds.

**Limited to Indian Markets:**  
The pipeline is currently hardcoded and optimized specifically for the NSE (National Stock Exchange). It does not seamlessly support US equities (NYSE/NASDAQ) or global markets.

**Context Blind Spots:**  
The AI makes decisions based purely on the immediate data it scrapes (recent news and surface-level fundamentals). It does not read 50-page quarterly earnings transcripts or deep-dive into long-term debt restructuring plans.

**No Technical Indicator Integration:**  
The system heavily favors fundamental data and news sentiment. It does not actively factor in technical analysis indicators like MACD, RSI, or Fibonacci retracements into the final verdict.

---

## Upcoming Updates

- Asynchronous AI Execution (Fixes Latency)  
- Premium Data Integrations  
- Technical Analyst Agent  
- Backtesting and accuracy tracking  
- RAG for Earnings Transcripts  
- Global Market Expansion  

---

## Running locally

```bash
git clone https://github.com/your-username/verdictx.git
cd verdictx
pip install -r requirements.txt
python api.py
cd verdictx-ui
npm install
npm run dev
