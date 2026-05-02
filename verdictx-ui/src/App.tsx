import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import Features from './components/Features';
import HowItWorks from './components/Howitworks';
import TrustBar from './components/TrustBar';
import AnalyzePage from './pages/AnalyzePage';
import ResultsPage from './pages/ResultsPage';

// ── Landing Page (home) ──────────────────────────────────────────
function HomePage() {
  return (
    <div style={{ position: 'relative', minHeight: '100vh', background: '#050a0e', color: 'white', overflowX: 'hidden' }}>
      {/* Background Ambient Glow */}
      <div style={{ pointerEvents: 'none', position: 'fixed', inset: 0, zIndex: 0 }}>
        <div style={{
          position: 'absolute', top: 0, left: '50%', transform: 'translateX(-50%)',
          width: 1000, height: 800,
          background: 'rgba(0,200,200,0.05)', borderRadius: '50%', filter: 'blur(180px)'
        }} />
        <div style={{
          position: 'absolute', bottom: -100, left: '50%', transform: 'translateX(-50%)',
          width: 800, height: 600,
          background: 'rgba(16,185,129,0.03)', borderRadius: '50%', filter: 'blur(150px)'
        }} />
      </div>

      {/* Content */}
      <div style={{ position: 'relative', zIndex: 10, display: 'flex', flexDirection: 'column' }}>
        <Navbar />
        <main style={{ flexGrow: 1 }}>
          {/* Hero — full viewport width */}
          <Hero />
          {/* Rest — centered container */}
          <div className="page-container">
            <div style={{ marginBottom: 96 }}>
              <Features />
            </div>
            <div style={{ marginBottom: 96 }}>
              <HowItWorks />
            </div>
          </div>
        </main>
        <TrustBar />
      </div>
    </div>
  );
}

// ── App with Router ──────────────────────────────────────────────
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/analyze/:ticker" element={<AnalyzePage />} />
        <Route path="/results/:ticker" element={<ResultsPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;