import { motion } from 'framer-motion';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';

const popularStocks = ['IRCTC', 'TCS', 'RELIANCE', 'INFY', 'HDFCBANK', 'WIPRO', 'ITC', 'SBIN'];

export default function Hero() {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  const handleAnalyze = () => {
    const ticker = query.trim().toUpperCase() || 'IRCTC';
    navigate(`/analyze/${ticker}`);
  };

  return (
    <section className="relative w-full min-h-[82vh] mt-14 overflow-hidden bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-black flex flex-col items-center justify-center px-6 py-24 md:py-32">
      
      {/* Subtle Ambient Glows */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-[10%] left-[10%] w-[600px] h-[600px] bg-teal-500/10 rounded-full blur-[140px]" />
        <div className="absolute top-[10%] right-[10%] w-[600px] h-[600px] bg-rose-500/10 rounded-full blur-[140px]" />
        <div className="absolute top-[-20%] left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-slate-700/20 rounded-full blur-[120px]" />
      </div>

      {/* ── Bull — Left ── */}
      <div 
        className="absolute left-[-150px] top-0 bottom-0 w-[55%] max-w-[700px] pointer-events-none select-none z-[2] flex items-center justify-start opacity-80"
        style={{ WebkitMaskImage: 'linear-gradient(to bottom, black 50%, transparent 100%)', maskImage: 'linear-gradient(to bottom, black 50%, transparent 100%)' }}
      >
        <motion.img
          src="/bull.png.png"
          alt="Bull"
          animate={{ y: [0, -10, 0] }}
          transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
          className="w-full h-full object-contain object-right saturate-[0.6] mix-blend-lighten"
          style={{ filter: 'drop-shadow(0 0 60px rgba(20,184,166,0.15))' }}
        />
      </div>

      {/* ── Bear — Right ── */}
      <div 
        className="absolute right-[-100px] top-0 bottom-0 w-[55%] max-w-[700px] pointer-events-none select-none z-[2] flex items-center justify-end opacity-80"
        style={{ WebkitMaskImage: 'linear-gradient(to bottom, black 50%, transparent 100%)', maskImage: 'linear-gradient(to bottom, black 50%, transparent 100%)' }}
      >
        <motion.img
          src="/bear.png.png"
          alt="Bear"
          animate={{ y: [0, -10, 0] }}
          transition={{ duration: 5, repeat: Infinity, ease: "easeInOut", delay: 1 }}
          className="w-full h-full object-contain object-left saturate-[0.6] mix-blend-lighten"
          style={{ filter: 'drop-shadow(0 0 60px rgba(225,29,72,0.15))' }}
        />
      </div>

      {/* ── Centered Content ── */}
      <div className="relative z-10 text-center max-w-4xl w-full mx-auto">
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className="font-['Plus_Jakarta_Sans'] text-5xl md:text-7xl lg:text-[5.5rem] font-bold text-white tracking-tight leading-tight"
        >
          Smart Analysis.
        </motion.h1>

        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1, ease: 'easeOut' }}
          className="font-['Plus_Jakarta_Sans'] text-5xl md:text-7xl lg:text-[5.5rem] font-bold tracking-tight leading-tight mt-1 bg-gradient-to-br from-slate-200 to-slate-500 bg-clip-text text-transparent"
        >
          Smarter Decisions.
        </motion.h2>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2, ease: 'easeOut' }}
          className="font-['Plus_Jakarta_Sans'] text-lg md:text-xl text-slate-400 mt-6 max-w-2xl mx-auto leading-relaxed"
        >
          AI-powered multi-agent research on any Indian stock — in seconds.
        </motion.p>

        {/* Search Bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mt-12"
        >
          <div className="flex items-center gap-2 p-2.5 bg-slate-900/40 border border-slate-700/50 rounded-2xl backdrop-blur-2xl max-w-2xl mx-auto shadow-[0_0_40px_rgba(0,0,0,0.4)] ring-1 ring-white/5 transition-all hover:border-slate-600/50">
            <Search className="w-5 h-5 text-slate-400 ml-4 shrink-0" />
            <Input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleAnalyze()}
              placeholder="e.g. IRCTC, TCS, RELIANCE..."
              className="border-0 bg-transparent text-white placeholder:text-slate-500 text-lg focus-visible:ring-0 focus-visible:ring-offset-0 px-3 h-14 font-['Plus_Jakarta_Sans'] w-full"
            />
            <Button 
              onClick={handleAnalyze}
              className="h-14 px-8 rounded-xl bg-white text-slate-950 hover:bg-slate-200 font-bold text-[15px] transition-all hover:scale-105 shadow-md shadow-white/10"
            >
              Analyze &rarr;
            </Button>
          </div>

          {/* Stock Tags */}
          <div className="flex flex-wrap justify-center gap-2 mt-8">
            {popularStocks.map((s) => (
              <button
                key={s}
                onClick={() => setQuery(s)}
                className="px-4 py-1.5 rounded-full border border-slate-800 bg-slate-900/30 text-xs font-semibold text-slate-400 hover:text-white hover:border-slate-600 hover:bg-slate-800 transition-all font-['Plus_Jakarta_Sans'] tracking-wide"
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