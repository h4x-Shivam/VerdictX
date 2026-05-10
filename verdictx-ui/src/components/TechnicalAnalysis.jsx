import { motion } from 'framer-motion';

/* ─── Status Colors ─────────────────────────────────────────── */
const STATUS_STYLES = {
  bullish:       { emoji: '✅', color: '#4ade80', label: 'Bullish' },
  confirming:    { emoji: '✅', color: '#4ade80', label: 'Confirming' },
  outperforming: { emoji: '✅', color: '#4ade80', label: 'Outperforming' },
  weakening:     { emoji: '⚠️', color: '#fbbf24', label: 'Weakening' },
  watch:         { emoji: '⚠️', color: '#fbbf24', label: 'Watch' },
  caution:       { emoji: '⚠️', color: '#fbbf24', label: 'Caution' },
  neutral:       { emoji: '➖', color: '#64748b', label: 'Neutral' },
  bearish:       { emoji: '🔴', color: '#f87171', label: 'Bearish' },
  diverging:     { emoji: '🔴', color: '#f87171', label: 'Diverging' },
};

const BIAS_COLORS = {
  bullish:              '#4ade80',
  'cautiously bullish': '#4ade80',
  'strongly bullish':   '#00ffb3',
  bearish:              '#f87171',
  'cautiously bearish': '#f87171',
  'strongly bearish':   '#ff1744',
  neutral:              '#fbbf24',
};

const REGIME_BG = {
  trending:    'rgba(74,222,128,0.07)',
  bullish:     'rgba(74,222,128,0.07)',
  bearish:     'rgba(248,113,113,0.07)',
  ranging:     'rgba(251,191,36,0.07)',
  neutral:     'rgba(251,191,36,0.07)',
  consolidating: 'rgba(251,191,36,0.07)',
};

const REGIME_BORDER = {
  trending:    'rgba(74,222,128,0.18)',
  bullish:     'rgba(74,222,128,0.18)',
  bearish:     'rgba(248,113,113,0.18)',
  ranging:     'rgba(251,191,36,0.18)',
  neutral:     'rgba(251,191,36,0.18)',
  consolidating: 'rgba(251,191,36,0.18)',
};

/* ─── Sub-components ────────────────────────────────────────── */

function DimensionCard({ label, status, dataLines, delay = 0 }) {
  const s = STATUS_STYLES[status] || STATUS_STYLES.neutral;
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      style={{
        background: 'rgba(8,14,24,0.9)',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 14,
        padding: '16px 18px',
        transition: 'border-color 0.25s, background 0.25s',
        cursor: 'default',
      }}
      onMouseEnter={e => {
        e.currentTarget.style.borderColor = `${s.color}33`;
        e.currentTarget.style.background = 'rgba(8,14,24,1)';
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)';
        e.currentTarget.style.background = 'rgba(8,14,24,0.9)';
      }}
    >
      {/* Header row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          {label}
        </div>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 5,
          padding: '2px 9px', borderRadius: 999,
          background: `${s.color}14`, border: `1px solid ${s.color}28`,
          fontSize: 11, fontWeight: 600, color: s.color,
        }}>
          <span style={{ fontSize: 12 }}>{s.emoji}</span>
          {s.label}
        </div>
      </div>

      {/* Data lines */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {dataLines.map((line, i) => (
          <div key={i} style={{ fontSize: 12, color: '#64748b', lineHeight: 1.55 }}>
            {line}
          </div>
        ))}
      </div>
    </motion.div>
  );
}

/* ─── Main Component ────────────────────────────────────────── */

export default function TechnicalAnalysis({ data }) {
  if (!data) return (
    <div style={{ background:'rgba(248,113,113,0.1)', border:'1px solid rgba(248,113,113,0.3)', borderRadius:16, padding:'20px', marginBottom:18, color:'#f87171', textAlign:'center', fontWeight:600 }}>
      ⚠️ Technical Analysis data is missing for this ticker.
    </div>
  );

  const {
    regime = {},
    dimensions = {},
    technical_score = 50,
    bias = 'Neutral',
    key_insight = '',
  } = data;

  const regimeType = (regime.type || 'neutral').toLowerCase();
  const regimeBg = REGIME_BG[regimeType] || REGIME_BG.neutral;
  const regimeBorder = REGIME_BORDER[regimeType] || REGIME_BORDER.neutral;
  const biasColor = BIAS_COLORS[bias.toLowerCase()] || '#fbbf24';
  const scoreP = Math.max(0, Math.min(100, technical_score));

  /* Build dimension cards from data */
  const dimCards = [
    { key: 'trend',          label: 'TREND' },
    { key: 'momentum',       label: 'MOMENTUM' },
    { key: 'volume',         label: 'VOLUME' },
    { key: 'volatility',     label: 'VOLATILITY' },
    { key: 'structure',      label: 'STRUCTURE' },
    { key: 'market_context', label: 'MARKET CONTEXT' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.28 }}
      style={{
        background: 'rgba(8,14,24,0.9)',
        border: '1px solid rgba(255,255,255,0.07)',
        borderRadius: 16,
        padding: '20px 24px',
        marginBottom: 18,
      }}
    >
      {/* Block Title */}
      <div style={{
        fontSize: 10, fontWeight: 700, color: '#475569',
        textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 16,
      }}>
        📈 TECHNICAL ANALYSIS
      </div>

      {/* ───── Section 1: Regime Banner ───── */}
      <div style={{
        display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 0,
        padding: '12px 18px', borderRadius: 10,
        background: regimeBg, border: `1px solid ${regimeBorder}`,
        marginBottom: 18,
      }}>
        {[
          { lbl: 'Market Regime', val: regime.type || 'N/A' },
          { lbl: 'ADX', val: regime.adx != null ? regime.adx : 'N/A' },
          { lbl: 'Supertrend', val: regime.supertrend || 'N/A' },
        ].map((item, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center' }}>
            {i > 0 && (
              <div style={{
                width: 1, height: 18,
                background: 'rgba(255,255,255,0.12)',
                margin: '0 16px',
              }} />
            )}
            <span style={{ fontSize: 11, color: '#64748b', marginRight: 6, fontWeight: 600, textTransform: 'uppercase' }}>
              {item.lbl}:
            </span>
            <span style={{
              fontSize: 12, fontWeight: 700,
              color: regimeType === 'bearish' ? '#f87171' : (regimeType === 'ranging' || regimeType === 'consolidating' || regimeType === 'neutral' ? '#fbbf24' : '#4ade80'),
              textTransform: 'capitalize',
            }}>
              {item.val}
            </span>
          </div>
        ))}

        {/* Bias — pushed to far right */}
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center' }}>
          <div style={{
            width: 1, height: 18,
            background: 'rgba(255,255,255,0.12)',
            margin: '0 16px',
          }} />
          <span style={{ fontSize: 11, color: '#64748b', marginRight: 6, fontWeight: 600, textTransform: 'uppercase' }}>
            Bias:
          </span>
          <span style={{ fontSize: 12, fontWeight: 700, color: biasColor }}>
            {bias}
          </span>
        </div>
      </div>

      {/* ───── Section 2: Six Dimension Cards ───── */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: 14,
        marginBottom: 20,
      }}
        className="ta-dimension-grid"
      >
        {dimCards.map((d, i) => {
          const dim = dimensions[d.key] || {};
          return (
            <DimensionCard
              key={d.key}
              label={d.label}
              status={(dim.status || 'neutral').toLowerCase()}
              dataLines={dim.data || ['No data available']}
              delay={0.3 + i * 0.05}
            />
          );
        })}
      </div>

      {/* ───── Section 3: Technical Score Bar ───── */}
      <div style={{ marginBottom: 6 }}>
        {/* Score bar — matches existing Bar component style */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
          <div style={{ width: 110, fontSize: 12, color: '#64748b', flexShrink: 0 }}>
            Technical <span style={{ color: '#334155', fontSize: 10 }}>(15%)</span>
          </div>
          <div style={{ flex: 1, height: 6, background: 'rgba(255,255,255,0.05)', borderRadius: 3, overflow: 'hidden' }}>
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${scoreP}%` }}
              transition={{ duration: 1, delay: 0.6 }}
              style={{ height: '100%', background: '#22d3ee', borderRadius: 3 }}
            />
          </div>
          <div style={{ width: 30, textAlign: 'right', fontSize: 12, fontWeight: 600, color: 'white' }}>
            {Math.round(scoreP)}
          </div>
        </div>

        {/* Bias label */}
        <div style={{ textAlign: 'center', fontSize: 11, color: biasColor, fontWeight: 600, marginBottom: 10 }}>
          Bias: {bias}
        </div>

        {/* Key Insight callout */}
        {key_insight && (
          <div style={{
            padding: '12px 16px',
            borderRadius: 10,
            background: 'rgba(34,211,238,0.04)',
            borderLeft: '3px solid rgba(34,211,238,0.4)',
            fontSize: 12.5,
            color: '#94a3b8',
            lineHeight: 1.7,
          }}>
            <span style={{ marginRight: 6 }}>💡</span>
            {key_insight}
          </div>
        )}
      </div>
    </motion.div>
  );
}
