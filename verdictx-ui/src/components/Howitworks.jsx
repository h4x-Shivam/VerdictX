import { motion } from 'framer-motion';

const steps = [
  {
    icon: (
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
    ),
    number: '01',
    title: 'Search Stock',
    subtitle: 'Enter any NSE-listed ticker symbol',
    color: '#22d3ee',
    glow: 'rgba(34,211,238,0.2)',
    bg: 'rgba(34,211,238,0.08)',
    border: 'rgba(34,211,238,0.3)',
  },
  {
    icon: (
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2a7 7 0 0 1 7 7c0 2.38-1.19 4.47-3 5.74V17a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 0 1 7-7z"/>
        <line x1="9" y1="22" x2="15" y2="22"/>
      </svg>
    ),
    number: '02',
    title: 'AI Research',
    subtitle: 'Agents pull live data & news in seconds',
    color: '#a78bfa',
    glow: 'rgba(167,139,250,0.2)',
    bg: 'rgba(167,139,250,0.08)',
    border: 'rgba(167,139,250,0.3)',
  },
  {
    icon: (
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
      </svg>
    ),
    number: '03',
    title: 'Debate & Score',
    subtitle: 'Bull vs Bear argue; Judge scores both',
    color: '#f97316',
    glow: 'rgba(249,115,22,0.2)',
    bg: 'rgba(249,115,22,0.08)',
    border: 'rgba(249,115,22,0.3)',
  },
  {
    icon: (
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
        <polyline points="22 4 12 14.01 9 11.01"/>
      </svg>
    ),
    number: '04',
    title: 'Final Verdict',
    subtitle: 'Clear BUY / HOLD / SELL with reasoning',
    color: '#4ade80',
    glow: 'rgba(74,222,128,0.2)',
    bg: 'rgba(74,222,128,0.08)',
    border: 'rgba(74,222,128,0.3)',
  },
];

const ConnectorArrow = ({ color }) => (
  <div style={{ display: 'flex', alignItems: 'center', padding: '0 4px', marginTop: -20 }}>
    <svg width="40" height="16" viewBox="0 0 40 16" fill="none">
      <path d="M0 8H34M34 8L27 2M34 8L27 14"
        stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" opacity="0.45"/>
    </svg>
  </div>
);

export default function HowItWorks() {
  return (
    <section style={{ position: 'relative', zIndex: 10, paddingBottom: 16 }}>

      {/* Section header */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5 }}
        style={{ textAlign: 'center', marginBottom: 48 }}
      >
        <span style={{
          display: 'inline-block',
          padding: '5px 16px',
          borderRadius: 999,
          border: '1px solid rgba(167,139,250,0.2)',
          background: 'rgba(167,139,250,0.06)',
          color: '#a78bfa',
          fontSize: 12,
          fontWeight: 700,
          letterSpacing: '0.08em',
          marginBottom: 14,
        }}>HOW IT WORKS</span>
        <h2 style={{
          fontSize: 32, fontWeight: 800, color: 'white',
          letterSpacing: '-0.02em', lineHeight: 1.2, margin: 0,
        }}>
          From ticker to verdict in seconds
        </h2>
        <p style={{ color: '#64748b', fontSize: 15, marginTop: 10 }}>
          Four simple steps. Zero guesswork.
        </p>
      </motion.div>

      {/* Steps row */}
      <div style={{
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        gap: 0,
        flexWrap: 'wrap',
      }}>
        {steps.map((step, i) => (
          <div key={step.title} style={{ display: 'flex', alignItems: 'center' }}>

            <motion.div
              initial={{ opacity: 0, y: 28 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.45, delay: i * 0.12 }}
              style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center',
                textAlign: 'center', width: 168,
              }}
            >
              {/* Step number */}
              <div style={{
                fontSize: 11, fontWeight: 800, letterSpacing: '0.1em',
                color: step.color, marginBottom: 12, opacity: 0.7,
              }}>{step.number}</div>

              {/* Icon circle */}
              <div style={{
                width: 64, height: 64, borderRadius: '50%',
                background: step.bg,
                border: `1.5px solid ${step.border}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: step.color,
                marginBottom: 16,
                boxShadow: `0 0 24px ${step.glow}`,
                position: 'relative',
              }}>
                {step.icon}
                {/* Outer pulse ring */}
                <div style={{
                  position: 'absolute', inset: -6, borderRadius: '50%',
                  border: `1px solid ${step.color}`,
                  opacity: 0.15,
                }} />
              </div>

              {/* Text */}
              <h3 style={{
                color: 'white', fontWeight: 700, fontSize: 15,
                margin: '0 0 6px 0',
              }}>{step.title}</h3>
              <p style={{
                color: '#64748b', fontSize: 13, lineHeight: 1.55,
                margin: 0, maxWidth: 140,
              }}>{step.subtitle}</p>
            </motion.div>

            {/* Arrow connector */}
            {i < steps.length - 1 && <ConnectorArrow color={steps[i + 1].color} />}
          </div>
        ))}
      </div>

      {/* Bottom CTA strip */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5, delay: 0.5 }}
        style={{
          marginTop: 56,
          padding: '20px 32px',
          borderRadius: 16,
          background: 'linear-gradient(135deg, rgba(0,200,200,0.05), rgba(167,139,250,0.05))',
          border: '1px solid rgba(255,255,255,0.06)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 16,
        }}
      >
        <div>
          <div style={{ color: 'white', fontWeight: 700, fontSize: 16 }}>
            Ready to get your first verdict?
          </div>
          <div style={{ color: '#64748b', fontSize: 13, marginTop: 4 }}>
            Enter any NSE stock ticker above and hit Analyze.
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          {['BUY', 'HOLD', 'SELL'].map((v, i) => (
            <span key={v} style={{
              padding: '6px 16px', borderRadius: 8, fontSize: 12, fontWeight: 800,
              background: ['rgba(74,222,128,0.12)', 'rgba(250,204,21,0.1)', 'rgba(248,113,113,0.12)'][i],
              border: `1px solid ${['rgba(74,222,128,0.3)','rgba(250,204,21,0.25)','rgba(248,113,113,0.3)'][i]}`,
              color: ['#4ade80','#facc15','#f87171'][i],
            }}>{v}</span>
          ))}
        </div>
      </motion.div>
    </section>
  );
}
