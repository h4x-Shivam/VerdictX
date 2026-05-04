# VerdictX

VerdictX is an AI-powered Bull vs Bear debate engine delivering clear, unbiased trading decisions.
AI-powered stock analysis system based on multi-agent reasoning.

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

## Core Idea

Instead of a single model giving an answer, VerdictX simulates a small system:

- A **bullish view** (growth, upside, tailwinds)  
- A **bearish view** (risks, valuation, weaknesses)  
- A **final evaluation layer** that compares both  

The goal is not prediction, but **structured reasoning**.

---

## What it does

Given a stock:

- pulls key data (price, basic fundamentals)
- collects recent news and filters it
- runs a multi-agent analysis
- outputs:
  - BUY / HOLD / SELL
  - confidence (heuristic for now)
  - strongest bullish and bearish points
  - short reasoning summary

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
- Custom data pipeline
- LLM integration (Ollama / Groq)

**Frontend (in progress)**
- React
- Tailwind CSS
- Framer Motion

---

## Current limitations

- News still influences output more than desired  
- Confidence score is not probabilistic yet  
- Fundamentals layer is basic (not fully deep analysis)  
- System is not backtested yet  

---

## What’s next

- Better fundamentals integration  
- Reduced news bias  
- Backtesting and accuracy tracking  
- More robust scoring system  
- Cleaner frontend (React UI in progress)

---

## Running locally

```bash
git clone https://github.com/your-username/verdictx.git
cd verdictx

pip install -r requirements.txt
streamlit run app.py
