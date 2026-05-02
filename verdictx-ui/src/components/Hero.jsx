import { motion } from 'framer-motion';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const popularStocks = ['IRCTC', 'TCS', 'RELIANCE', 'INFY', 'HDFCBANK', 'WIPRO', 'ITC', 'SBIN'];

export default function Hero() {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  const handleAnalyze = () => {
    const ticker = query.trim().toUpperCase() || 'IRCTC';
    navigate(`/analyze/${ticker}`);
  };

  return (
    <section style={{
      position: 'relative',
      width: '100%',
      marginTop: 57,           /* navbar height */
      overflow: 'hidden',
      background: 'linear-gradient(135deg, rgba(0,30,18,0.97) 0%, rgba(5,10,18,0.98) 45%, rgba(28,4,4,0.97) 100%)',
      minHeight: '82vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '72px 48px 80px',
    }}>

      {/* Ambient glow */}
      <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
        <div style={{
          position: 'absolute', top: '-10%', left: '20%',
          width: 700, height: 600,
          background: 'rgba(0,210,150,0.09)', borderRadius: '50%', filter: 'blur(130px)'
        }} />
        <div style={{
          position: 'absolute', top: '-10%', right: '15%',
          width: 600, height: 550,
          background: 'rgba(200,20,20,0.09)', borderRadius: '50%', filter: 'blur(120px)'
        }} />
      </div>

      {/* ── Bull — Left ── */}
      <div style={{
        position: 'absolute',
        left: -180,
        top: 0,
        bottom: 0,
        width: '58%',
        maxWidth: 820,
        pointerEvents: 'none',
        userSelect: 'none',
        zIndex: 2,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'flex-start',
      }}>
        <img
          src="/bull.png.png"
          alt="Bull"
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'contain',
            objectPosition: 'right center',
            opacity: 0.95,
            filter: 'hue-rotate(-10deg) saturate(1.6) brightness(1.1) drop-shadow(0 0 60px rgba(0,220,100,0.6))',
          }}
        />
        <div style={{
          position: 'absolute', bottom: 0, left: 0,
          width: '80%', height: '50%',
          background: 'rgba(0,200,80,0.18)',
          borderRadius: '50%', filter: 'blur(80px)', zIndex: -1
        }} />
      </div>

      {/* ── Bear — Right ── */}
      <div style={{
        position: 'absolute',
        right: -60,
        top: 0,
        bottom: 0,
        width: '58%',
        maxWidth: 820,
        pointerEvents: 'none',
        userSelect: 'none',
        zIndex: 2,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'flex-end',
      }}>
        <img
          src="/bear.png.png"
          alt="Bear"
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'contain',
            objectPosition: 'left center',
            opacity: 0.95,
            filter: 'hue-rotate(10deg) saturate(1.5) brightness(1.1) drop-shadow(0 0 60px rgba(220,40,40,0.6))',
          }}
        />
        <div style={{
          position: 'absolute', bottom: 0, right: 0,
          width: '80%', height: '50%',
          background: 'rgba(210,30,30,0.18)',
          borderRadius: '50%', filter: 'blur(80px)', zIndex: -1
        }} />
      </div>

      {/* ── Centered Content ── */}
      <div style={{
        position: 'relative',
        zIndex: 10,
        textAlign: 'center',
        maxWidth: 720,
        width: '100%',
      }}>
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          style={{
            fontSize: 'clamp(40px, 6vw, 78px)',
            fontWeight: 900,
            color: 'white',
            lineHeight: 1.08,
            letterSpacing: '-0.02em',
            textShadow: '0 2px 40px rgba(0,0,0,0.9)',
          }}
        >
          Smart Analysis.
        </motion.h1>

        <motion.h2
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.18, ease: 'easeOut' }}
          style={{
            fontSize: 'clamp(40px, 6vw, 78px)',
            fontWeight: 900,
            marginTop: 4,
            lineHeight: 1.08,
            letterSpacing: '-0.02em',
            background: 'linear-gradient(135deg, #00ffcc 0%, #00e6c8 50%, #00b4d8 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}
        >
          Smarter Decisions.
        </motion.h2>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.32, ease: 'easeOut' }}
          style={{
            color: '#94a3b8',
            fontSize: 17,
            marginTop: 18,
            fontWeight: 400,
            lineHeight: 1.6,
          }}
        >
          AI-powered multi-agent research on any Indian stock — in seconds.
        </motion.p>

        {/* Search Bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.46 }}
          style={{ marginTop: 32 }}
        >
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8,
            background: 'rgba(8,14,26,0.88)',
            border: '1px solid rgba(255,255,255,0.13)',
            borderRadius: 12,
            padding: '4px 4px 4px 16px',
            backdropFilter: 'blur(12px)',
          }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#64748b"
              strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleAnalyze()}
              placeholder="e.g. IRCTC, TCS, RELIANCE, HDFCBANK"
              style={{
                flex: 1, background: 'transparent', color: 'white',
                fontSize: 14, outline: 'none', border: 'none',
                fontFamily: 'inherit', padding: '11px 0',
              }}
            />
            <button style={{
              padding: '11px 28px',
              borderRadius: 9,
              background: 'linear-gradient(135deg, #06b6d4, #22d3ee)',
              color: 'black', fontWeight: 700, fontSize: 14,
              border: 'none', cursor: 'pointer',
              fontFamily: 'inherit', whiteSpace: 'nowrap',
              transition: 'transform 0.15s',
            }}
              onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.04)'}
              onClick={handleAnalyze}
            >
              Analyze →
            </button>
          </div>

          {/* Stock Tags */}
          <div style={{
            display: 'flex', flexWrap: 'wrap', justifyContent: 'center',
            gap: 8, marginTop: 14,
          }}>
            {popularStocks.map((s) => (
              <button
                key={s}
                onClick={() => setQuery(s)}
                style={{
                  padding: '5px 15px', borderRadius: 7,
                  border: '1px solid rgba(255,255,255,0.1)',
                  background: 'rgba(255,255,255,0.04)',
                  fontSize: 12, fontWeight: 500, color: '#94a3b8',
                  cursor: 'pointer', transition: 'all 0.18s', fontFamily: 'inherit',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.color = 'white';
                  e.currentTarget.style.borderColor = 'rgba(34,211,238,0.45)';
                  e.currentTarget.style.background = 'rgba(34,211,238,0.07)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.color = '#94a3b8';
                  e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)';
                  e.currentTarget.style.background = 'rgba(255,255,255,0.04)';
                }}
              >
                {s}
              </button>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}