export default function Navbar() {
  return (
    <nav style={{
      position: 'fixed', top: 0, left: 0, right: 0, zIndex: 50,
      borderBottom: '1px solid rgba(255,255,255,0.05)',
      backdropFilter: 'blur(20px)',
      background: 'rgba(5,10,14,0.85)',
    }}>
      <div style={{
        maxWidth: 1280,
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px 48px',
      }}>
        {/* Centered Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ color: '#22d3ee', fontWeight: 900, fontSize: 26, letterSpacing: '-0.02em' }}>X</span>
          <span style={{ color: 'white', fontWeight: 700, fontSize: 18, letterSpacing: '0.14em' }}>VERDICTX</span>
        </div>
      </div>
    </nav>
  );
}