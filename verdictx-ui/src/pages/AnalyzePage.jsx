import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

// 6 steps — each maps to one real operation in api.py
const STEPS = [
  { icon: '🔍', label: 'Fetching market data + news in parallel',   color: '#22d3ee' },
  { icon: '🧠', label: 'Analyzing market sentiment',                  color: '#a78bfa' },
  { icon: '🟢', label: 'Bull agent scanning positive signals',        color: '#4ade80' },
  { icon: '🔴', label: 'Bear agent scanning risks & red flags',       color: '#f87171' },
  { icon: '📊', label: 'Technical agent analyzing price action',      color: '#06b6d4' },
  { icon: '⚖️', label: 'Judge writing final verdict',                 color: '#fbbf24' },
  { icon: '📋', label: 'Preparing your research report',              color: '#34d399' },
];

export default function AnalyzePage() {
  const { ticker } = useParams();
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [pct, setPct] = useState(0);
  const [msg, setMsg] = useState('Starting analysis…');
  const [error, setError] = useState(null);
  const [done, setDone] = useState(false);
  const [partials, setPartials] = useState({});   // live agent scores as they stream in
  const esRef = useRef(null);
  const connectedRef = useRef(false);   // tracks whether we ever received a valid message

  useEffect(() => {
    if (!ticker) return;

    const API_BASE = import.meta.env.VITE_API_URL || '';
    const url = `${API_BASE}/api/analyze?ticker=${encodeURIComponent(ticker.toUpperCase())}`;
    const es = new EventSource(url);
    esRef.current = es;

    es.onmessage = (e) => {
      connectedRef.current = true;   // we've received at least one message — backend is live
      try {
        const data = JSON.parse(e.data);

        if (data.type === 'progress') {
          // api.py sends step 1–4; convert to 0-indexed for the STEPS array
          setCurrentStep(Math.max(0, (data.step || 1) - 1));
          setPct(data.pct || 0);
          setMsg(data.msg || '');
        }

        if (data.type === 'partial') {
          // Stream agent scores as they arrive — before the full done event
          setPartials(prev => ({ ...prev, ...data }));
        }

        if (data.type === 'done') {
          setDone(true);
          setPct(100);
          setMsg('Analysis complete!');
          es.close();
          setTimeout(() => {
            navigate(`/results/${ticker.toUpperCase()}`, {
              state: { result: data.result },
            });
          }, 700);
        }

        if (data.type === 'error') {
          setError(data.message || 'Analysis failed. Please try again.');
          es.close();
        }
      } catch (err) {
        console.error('SSE parse error:', err);
      }
    };

    es.onerror = () => {
      // Only show the "backend down" error if we never received a single message.
      // EventSource fires onerror on normal reconnection attempts too — don't
      // treat those as failures when the stream is still healthy.
      if (!connectedRef.current) {
        setError(
          'Could not connect to the API server.\n\n' +
          'Make sure api.py is running:\n  python api.py'
        );
        es.close();
      }
      // If we already received messages, it's a transient hiccup — ignore it.
    };

    return () => es.close();
  }, [ticker, navigate]);


  return (
    <div style={{
      minHeight: '100vh',
      background: '#050a0e',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      color: 'white',
      fontFamily: 'inherit',
      padding: '2rem',
    }}>

      {/* Background glow */}
      <div style={{
        position: 'fixed', inset: 0, pointerEvents: 'none',
        background: 'radial-gradient(ellipse 60% 50% at 50% 50%, rgba(34,211,238,0.07) 0%, transparent 70%)',
      }} />

      <div style={{ position: 'relative', zIndex: 10, width: '100%', maxWidth: 520 }}>

        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
            <span style={{ color: '#22d3ee', fontWeight: 900, fontSize: 22 }}>X</span>
            <span style={{ color: 'white', fontWeight: 700, fontSize: 16, letterSpacing: '0.14em' }}>VERDICTX</span>
          </div>
        </div>

        {/* Ticker + status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ textAlign: 'center', marginBottom: 36 }}
        >
          <div style={{
            display: 'inline-block',
            padding: '4px 16px', borderRadius: 999,
            background: 'rgba(34,211,238,0.08)',
            border: '1px solid rgba(34,211,238,0.2)',
            color: '#22d3ee', fontSize: 12, fontWeight: 700,
            letterSpacing: '0.1em', marginBottom: 14,
          }}>
            ANALYZING
          </div>
          <h1 style={{
            fontSize: 36, fontWeight: 900, letterSpacing: '-0.02em',
            margin: '0 0 8px',
          }}>
            {ticker?.toUpperCase()}
          </h1>
          <p style={{ color: '#64748b', fontSize: 14, margin: 0 }}>
            Multi-agent AI research in progress…
          </p>
        </motion.div>

        {/* Progress bar */}
        <div style={{
          background: 'rgba(255,255,255,0.05)',
          borderRadius: 999, height: 6,
          marginBottom: 32, overflow: 'hidden',
        }}>
          <motion.div
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
            style={{
              height: '100%', borderRadius: 999,
              background: done
                ? 'linear-gradient(90deg, #22d3ee, #4ade80)'
                : 'linear-gradient(90deg, #06b6d4, #22d3ee)',
            }}
          />
        </div>

        {/* Steps list */}
        <div style={{
          background: 'rgba(8,14,24,0.9)',
          border: '1px solid rgba(255,255,255,0.07)',
          borderRadius: 16, padding: '8px 0', marginBottom: 24,
        }}>
          {STEPS.map((step, i) => {
            const isDone = i < currentStep;
            const isActive = i === currentStep;
            const isPending = i > currentStep;
            return (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: 14,
                padding: '12px 20px',
                opacity: isPending ? 0.3 : 1,
                transition: 'opacity 0.3s',
                background: isActive ? 'rgba(34,211,238,0.04)' : 'transparent',
                borderLeft: isActive ? `2px solid ${step.color}` : '2px solid transparent',
              }}>
                {/* Status dot */}
                <div style={{
                  width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 13,
                  background: isDone
                    ? 'rgba(74,222,128,0.15)'
                    : isActive
                      ? `rgba(34,211,238,0.1)`
                      : 'rgba(255,255,255,0.04)',
                  border: isDone
                    ? '1px solid rgba(74,222,128,0.4)'
                    : isActive
                      ? `1px solid ${step.color}40`
                      : '1px solid rgba(255,255,255,0.08)',
                  transition: 'all 0.3s',
                }}>
                  {isDone ? '✓' : step.icon}
                </div>

                <div style={{ flex: 1 }}>
                  <div style={{
                    fontSize: 13.5, fontWeight: isActive ? 600 : 400,
                    color: isDone ? '#94a3b8' : isActive ? 'white' : '#475569',
                    transition: 'color 0.3s',
                  }}>
                    {step.label}
                  </div>
                  {isActive && msg && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      style={{ fontSize: 11, color: step.color, marginTop: 2 }}
                    >
                      {msg}
                    </motion.div>
                  )}
                  {/* Sentiment badge on step 1 (index 1) */}
                  {i === 1 && partials.sentiment && (
                    <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}
                      style={{ display: 'flex', gap: 6, marginTop: 5, flexWrap: 'wrap' }}>
                      <span style={{ fontSize: 10, fontWeight: 700, padding: '2px 8px',
                        borderRadius: 999, background: 'rgba(167,139,250,0.12)',
                        border: '1px solid rgba(167,139,250,0.3)', color: '#a78bfa' }}>
                        🧠 {partials.sentiment}
                        {partials.sentiment_score !== undefined && ` (${partials.sentiment_score > 0 ? '+' : ''}${partials.sentiment_score})`}
                      </span>
                    </motion.div>
                  )}

                  {/* Bull score badge on step 2 (index 2) */}
                  {i === 2 && partials.bull_score !== undefined && (
                    <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}
                      style={{ display: 'flex', gap: 6, marginTop: 5 }}>
                      <span style={{ fontSize: 10, fontWeight: 700, padding: '2px 8px',
                        borderRadius: 999, background: 'rgba(74,222,128,0.12)',
                        border: '1px solid rgba(74,222,128,0.3)', color: '#4ade80' }}>
                        🟢 Score: {partials.bull_score}/100
                      </span>
                    </motion.div>
                  )}

                  {/* Bear score badge on step 3 (index 3) */}
                  {i === 3 && partials.bear_score !== undefined && (
                    <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}
                      style={{ display: 'flex', gap: 6, marginTop: 5 }}>
                      <span style={{ fontSize: 10, fontWeight: 700, padding: '2px 8px',
                        borderRadius: 999, background: 'rgba(248,113,113,0.12)',
                        border: '1px solid rgba(248,113,113,0.3)', color: '#f87171' }}>
                        🔴 Score: {partials.bear_score}/100
                      </span>
                    </motion.div>
                  )}

                  {/* Technical score badge on step 4 (index 4) */}
                  {i === 4 && partials.technical_score !== undefined && (
                    <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}
                      style={{ display: 'flex', gap: 6, marginTop: 5 }}>
                      <span style={{ fontSize: 10, fontWeight: 700, padding: '2px 8px',
                        borderRadius: 999, background: 'rgba(6,182,212,0.12)',
                        border: '1px solid rgba(6,182,212,0.3)', color: '#06b6d4' }}>
                        📊 Score: {partials.technical_score}/100 ({partials.technical_bias})
                      </span>
                    </motion.div>
                  )}
                </div>

                {isDone && (
                  <span style={{ color: '#4ade80', fontSize: 12 }}>✓</span>
                )}
                {isActive && (
                  <motion.div
                    animate={{ opacity: [1, 0.3, 1] }}
                    transition={{ repeat: Infinity, duration: 1.4 }}
                    style={{
                      width: 6, height: 6, borderRadius: '50%',
                      background: step.color,
                    }}
                  />
                )}
              </div>
            );
          })}
        </div>

        {/* Error state */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              style={{
                padding: '16px 20px', borderRadius: 12,
                background: 'rgba(248,113,113,0.08)',
                border: '1px solid rgba(248,113,113,0.25)',
                color: '#f87171', fontSize: 13, lineHeight: 1.6,
                marginBottom: 16,
              }}
            >
              <div style={{ fontWeight: 700, marginBottom: 4 }}>❌ Error</div>
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Back button */}
        <div style={{ textAlign: 'center' }}>
          <button
            onClick={() => navigate('/')}
            style={{
              padding: '9px 24px', borderRadius: 9,
              background: 'transparent',
              border: '1px solid rgba(255,255,255,0.1)',
              color: '#64748b', cursor: 'pointer',
              fontSize: 13, fontFamily: 'inherit',
              transition: 'all 0.18s',
            }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.25)'; e.currentTarget.style.color = 'white'; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)'; e.currentTarget.style.color = '#64748b'; }}
          >
            ← Back to Home
          </button>
        </div>
      </div>
    </div>
  );
}
