import { motion } from 'framer-motion';

/* ── Inline chart visual for Real NSE Data ── */
const ChartVisual = () => (
  <svg viewBox="0 0 180 90" width="180" height="90" style={{ display: 'block' }}>
    {/* Grid lines */}
    {[0, 1, 2, 3].map(i => (
      <line key={i} x1="0" y1={i * 22 + 8} x2="180" y2={i * 22 + 8}
        stroke="rgba(255,255,255,0.04)" strokeWidth="1" />
    ))}
    {/* Candlesticks */}
    {[
      { x: 10, open: 65, close: 50, high: 42, low: 72 },
      { x: 28, open: 52, close: 38, high: 30, low: 60 },
      { x: 46, open: 40, close: 55, high: 32, low: 62 },
      { x: 64, open: 54, close: 45, high: 38, low: 65 },
      { x: 82, open: 46, close: 30, high: 22, low: 54 },
      { x: 100, open: 32, close: 20, high: 14, low: 40 },
      { x: 118, open: 22, close: 35, high: 15, low: 42 },
      { x: 136, open: 34, close: 18, high: 10, low: 42 },
      { x: 154, open: 20, close: 8,  high: 2,  low: 28 },
    ].map((c, i) => {
      const bull = c.close < c.open;
      const color = bull ? '#00e6c8' : '#ff5555';
      return (
        <g key={i}>
          <line x1={c.x + 6} y1={c.high} x2={c.x + 6} y2={c.low}
            stroke={color} strokeWidth="1.5" opacity="0.7" />
          <rect x={c.x} y={Math.min(c.open, c.close)} width="12"
            height={Math.max(2, Math.abs(c.open - c.close))}
            fill={color} rx="1" opacity="0.85" />
        </g>
      );
    })}
    {/* Trend line */}
    <polyline
      points="10,62 28,55 46,48 64,50 82,38 100,28 118,32 136,22 154,10"
      fill="none" stroke="#00e6c8" strokeWidth="2" opacity="0.5"
      strokeDasharray="4 2" />
  </svg>
);

/* ── Agent network visual for Multi-Agent AI ── */
const AgentVisual = () => (
  <svg viewBox="0 0 180 90" width="180" height="90" style={{ display: 'block' }}>
    {/* Connection lines */}
    <line x1="40" y1="45" x2="90" y2="25" stroke="rgba(139,92,246,0.4)" strokeWidth="1.5" />
    <line x1="40" y1="45" x2="90" y2="65" stroke="rgba(139,92,246,0.4)" strokeWidth="1.5" />
    <line x1="90" y1="25" x2="145" y2="45" stroke="rgba(250,204,21,0.4)" strokeWidth="1.5" />
    <line x1="90" y1="65" x2="145" y2="45" stroke="rgba(250,204,21,0.4)" strokeWidth="1.5" />
    <line x1="90" y1="25" x2="90" y2="65" stroke="rgba(255,255,255,0.1)" strokeWidth="1" />
    {/* Bull node */}
    <circle cx="40" cy="45" r="18" fill="rgba(0,200,100,0.12)" stroke="rgba(0,200,100,0.5)" strokeWidth="1.5" />
    <text x="40" y="50" textAnchor="middle" fill="#4ade80" fontSize="11" fontWeight="700">B</text>
    {/* Bear node */}
    <circle cx="90" cy="25" r="14" fill="rgba(248,113,113,0.12)" stroke="rgba(248,113,113,0.5)" strokeWidth="1.5" />
    <text x="90" y="30" textAnchor="middle" fill="#f87171" fontSize="10" fontWeight="700">B</text>
    {/* Judge node */}
    <circle cx="145" cy="45" r="18" fill="rgba(250,204,21,0.12)" stroke="rgba(250,204,21,0.5)" strokeWidth="1.5" />
    <text x="145" y="50" textAnchor="middle" fill="#facc15" fontSize="11" fontWeight="700">J</text>
    {/* Score pulse */}
    <circle cx="90" cy="65" r="14" fill="rgba(139,92,246,0.12)" stroke="rgba(139,92,246,0.4)" strokeWidth="1.5" />
    <text x="90" y="70" textAnchor="middle" fill="#a78bfa" fontSize="9" fontWeight="700">AI</text>
    {/* Glow dots */}
    {[[40,45],[90,25],[145,45],[90,65]].map(([cx,cy],i) => (
      <circle key={i} cx={cx} cy={cy} r="3" fill="white" opacity="0.3" />
    ))}
  </svg>
);

/* ── News feed visual for Filtered News ── */
const NewsVisual = () => (
  <svg viewBox="0 0 180 90" width="180" height="90" style={{ display: 'block' }}>
    {/* Card bg */}
    <rect x="2" y="4" width="176" height="82" rx="8" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
    {/* Tag */}
    <rect x="12" y="14" width="34" height="14" rx="4" fill="rgba(239,68,68,0.25)" />
    <text x="29" y="24.5" textAnchor="middle" fill="#f87171" fontSize="8" fontWeight="700">NEWS</text>
    {/* Source line */}
    <rect x="52" y="16" width="80" height="8" rx="3" fill="rgba(255,255,255,0.06)" />
    <rect x="136" y="16" width="30" height="8" rx="3" fill="rgba(255,255,255,0.03)" />
    {/* Headline bars */}
    <rect x="12" y="36" width="155" height="7" rx="3" fill="rgba(255,255,255,0.09)" />
    <rect x="12" y="48" width="120" height="6" rx="3" fill="rgba(255,255,255,0.06)" />
    <rect x="12" y="59" width="90" height="5" rx="3" fill="rgba(255,255,255,0.04)" />
    {/* Mini cards */}
    <rect x="12" y="70" width="50" height="12" rx="4" fill="rgba(239,68,68,0.1)" stroke="rgba(239,68,68,0.2)" strokeWidth="1" />
    <rect x="68" y="70" width="50" height="12" rx="4" fill="rgba(245,158,11,0.1)" stroke="rgba(245,158,11,0.2)" strokeWidth="1" />
    <rect x="124" y="70" width="44" height="12" rx="4" fill="rgba(34,211,238,0.1)" stroke="rgba(34,211,238,0.2)" strokeWidth="1" />
  </svg>
);

const features = [
  {
    title: 'Real NSE Data',
    description: 'Live prices, VWAP, delivery %, 52-week range — straight from NSE.',
    badge: 'LIVE',
    badgeColor: '#00e6c8',
    badgeBg: 'rgba(0,230,200,0.12)',
    border: 'rgba(0,200,200,0.3)',
    glow: 'rgba(0,200,200,0.08)',
    iconBg: 'rgba(0,200,200,0.12)',
    iconColor: '#22d3ee',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
        <rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>
      </svg>
    ),
    visual: <ChartVisual />,
  },
  {
    title: 'Multi-Agent AI',
    description: 'Bull, Bear, and Judge agents debate using real data, not guesses.',
    badge: 'AI',
    badgeColor: '#a78bfa',
    badgeBg: 'rgba(139,92,246,0.12)',
    border: 'rgba(139,92,246,0.3)',
    glow: 'rgba(139,92,246,0.08)',
    iconBg: 'rgba(139,92,246,0.12)',
    iconColor: '#a78bfa',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
        <circle cx="9" cy="7" r="4"/>
        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
      </svg>
    ),
    visual: <AgentVisual />,
  },
  {
    title: 'Filtered News',
    description: 'MoneyControl, Economic Times, Mint — filtered to show only relevant news.',
    badge: 'SMART',
    badgeColor: '#fbbf24',
    badgeBg: 'rgba(245,158,11,0.12)',
    border: 'rgba(245,158,11,0.3)',
    glow: 'rgba(245,158,11,0.08)',
    iconBg: 'rgba(245,158,11,0.12)',
    iconColor: '#fbbf24',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
      </svg>
    ),
    visual: <NewsVisual />,
  },
];

export default function Features() {
  return (
    <section style={{ position: 'relative', zIndex: 10, marginTop: 20 }}>

      {/* Section label */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5 }}
        style={{ textAlign: 'center', marginBottom: 40 }}
      >
        <span style={{
          display: 'inline-block',
          padding: '5px 16px',
          borderRadius: 999,
          border: '1px solid rgba(34,211,238,0.2)',
          background: 'rgba(34,211,238,0.06)',
          color: '#22d3ee',
          fontSize: 12,
          fontWeight: 700,
          letterSpacing: '0.08em',
          marginBottom: 14,
        }}>FEATURES</span>
        <h2 style={{
          fontSize: 32, fontWeight: 800, color: 'white',
          letterSpacing: '-0.02em', lineHeight: 1.2,
        }}>
          Everything you need to trade smarter
        </h2>
        <p style={{ color: '#64748b', fontSize: 15, marginTop: 10 }}>
          Built on real data. Powered by AI. Designed for Indian markets.
        </p>
      </motion.div>

      {/* Cards grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: 20,
      }}>
        {features.map((feat, i) => (
          <motion.div
            key={feat.title}
            initial={{ opacity: 0, y: 36 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.5, delay: i * 0.1, ease: 'easeOut' }}
            style={{
              position: 'relative',
              borderRadius: 18,
              border: `1px solid ${feat.border}`,
              background: 'rgba(8,14,24,0.9)',
              backdropFilter: 'blur(10px)',
              overflow: 'hidden',
              cursor: 'default',
              transition: 'transform 0.25s, box-shadow 0.25s',
              boxShadow: `0 0 0px ${feat.glow}`,
            }}
            whileHover={{
              y: -4,
              boxShadow: `0 12px 40px ${feat.glow}, 0 0 0 1px ${feat.border}`,
            }}
          >
            {/* Subtle top glow line */}
            <div style={{
              position: 'absolute', top: 0, left: '20%', right: '20%', height: 1,
              background: `linear-gradient(90deg, transparent, ${feat.iconColor}, transparent)`,
              opacity: 0.6,
            }} />

            {/* Card content */}
            <div style={{ padding: '22px 22px 0 22px' }}>
              {/* Header row */}
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 14 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{
                    width: 38, height: 38, borderRadius: 10,
                    background: feat.iconBg,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: feat.iconColor, flexShrink: 0,
                  }}>
                    {feat.icon}
                  </div>
                  <h3 style={{ color: 'white', fontWeight: 700, fontSize: 16, margin: 0 }}>{feat.title}</h3>
                </div>
                <span style={{
                  padding: '3px 10px', borderRadius: 999,
                  background: feat.badgeBg,
                  color: feat.badgeColor,
                  fontSize: 10, fontWeight: 800,
                  letterSpacing: '0.08em',
                  flexShrink: 0,
                }}>{feat.badge}</span>
              </div>

              {/* Description */}
              <p style={{
                color: '#64748b', fontSize: 13.5, lineHeight: 1.65,
                margin: 0, marginBottom: 18,
              }}>{feat.description}</p>
            </div>

            {/* Visual area — full bleed bottom */}
            <div style={{
              margin: '0 22px 22px',
              borderRadius: 12,
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.05)',
              padding: '14px 10px 10px',
              overflow: 'hidden',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              {feat.visual}
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}