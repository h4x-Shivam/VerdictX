import { motion } from 'framer-motion';

const popularStocks = ['IRCTC', 'TCS', 'RELIANCE', 'INFY', 'HDFCBANK', 'WIPRO', 'ITC', 'SBIN'];

export default function SearchBar() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.4 }}
      style={{
        position: 'relative', zIndex: 10,
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        marginTop: 32, padding: '0 16px',
      }}
    >
      {/* Search Input Row */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12,
        width: '100%', maxWidth: 600,
      }}>
        <div style={{
          flex: 1, display: 'flex', alignItems: 'center', gap: 12,
          padding: '14px 20px',
          borderRadius: 12,
          background: '#0c1220',
          border: '1px solid rgba(255,255,255,0.1)',
          transition: 'border-color 0.2s',
        }}>
          {/* Search Icon */}
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#64748b"
            strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
            style={{ flexShrink: 0 }}>
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            placeholder="e.g. IRCTC, TCS, RELIANCE, HDFCBANK"
            style={{
              width: '100%', background: 'transparent', color: 'white',
              fontSize: 14, outline: 'none', border: 'none',
              fontFamily: 'inherit',
            }}
          />
        </div>

        <button style={{
          padding: '14px 28px',
          borderRadius: 12,
          background: 'linear-gradient(135deg, #06b6d4, #22d3ee)',
          color: 'black',
          fontWeight: 700, fontSize: 14,
          border: 'none', cursor: 'pointer',
          whiteSpace: 'nowrap',
          transition: 'all 0.2s',
          fontFamily: 'inherit',
        }}
          onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.03)'}
          onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
        >
          Analyze →
        </button>
      </div>

      {/* Popular Tags */}
      <div style={{
        display: 'flex', flexWrap: 'wrap', justifyContent: 'center',
        gap: 10, marginTop: 20,
      }}>
        {popularStocks.map((stock) => (
          <button
            key={stock}
            style={{
              padding: '6px 16px',
              borderRadius: 8,
              border: '1px solid rgba(255,255,255,0.1)',
              background: 'rgba(255,255,255,0.03)',
              fontSize: 12, fontWeight: 500, color: '#94a3b8',
              cursor: 'pointer', transition: 'all 0.2s',
              fontFamily: 'inherit',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.color = 'white';
              e.currentTarget.style.borderColor = 'rgba(34,211,238,0.4)';
              e.currentTarget.style.background = 'rgba(34,211,238,0.05)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.color = '#94a3b8';
              e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)';
              e.currentTarget.style.background = 'rgba(255,255,255,0.03)';
            }}
          >
            {stock}
          </button>
        ))}
      </div>
    </motion.div>
  );
}