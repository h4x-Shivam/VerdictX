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
    <section className="relative w-full min-h-[82vh] mt-14 overflow-hidden bg-slate-950 flex flex-col items-center justify-center px-6 py-24 md:py-32">
      
      {/* Subtle Ambient Glows - Professional, not overwhelming */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[20%] w-[600px] h-[600px] bg-teal-500/5 rounded-full blur-[120px]" />
        <div className="absolute top-[-10%] right-[15%] w-[500px] h-[500px] bg-blue-500/5 rounded-full blur-[120px]" />
      </div>

      {/* ── Bull — Left ── */}
      <div className="absolute left-[-150px] top-0 bottom-0 w-[55%] max-w-[700px] pointer-events-none select-none z-[2] flex items-center justify-start opacity-70">
        <motion.img
          src="/bull.png.png"
          alt="Bull"
          animate={{ y: [0, -10, 0] }}
          transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
          className="w-full h-full object-contain object-right opacity-80 saturate-50"
          style={{ filter: 'drop-shadow(0 0 40px rgba(0,0,0,0.5))' }}
        />
      </div>

      {/* ── Bear — Right ── */}
      <div className="absolute right-[-100px] top-0 bottom-0 w-[55%] max-w-[700px] pointer-events-none select-none z-[2] flex items-center justify-end opacity-70">
        <motion.img
          src="/bear.png.png"
          alt="Bear"
          animate={{ y: [0, -10, 0] }}
          transition={{ duration: 5, repeat: Infinity, ease: "easeInOut", delay: 1 }}
          className="w-full h-full object-contain object-left opacity-80 saturate-50"
          style={{ filter: 'drop-shadow(0 0 40px rgba(0,0,0,0.5))' }}
        />
      </div>

      {/* ── Centered Content ── */}
      <div className="relative z-10 text-center max-w-3xl w-full mx-auto">
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className="font-['Plus_Jakarta_Sans'] text-5xl md:text-7xl font-bold text-white tracking-tight leading-tight"
        >
          Smart Analysis.
        </motion.h1>

        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1, ease: 'easeOut' }}
          className="font-['Plus_Jakarta_Sans'] text-5xl md:text-7xl font-bold tracking-tight leading-tight mt-2 bg-gradient-to-br from-slate-200 to-slate-500 bg-clip-text text-transparent"
        >
          Smarter Decisions.
        </motion.h2>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2, ease: 'easeOut' }}
          className="font-['Plus_Jakarta_Sans'] text-lg md:text-xl text-slate-400 mt-6 max-w-xl mx-auto"
        >
          AI-powered multi-agent research on any Indian stock — in seconds.
        </motion.p>

        {/* Search Bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mt-10"
        >
          <div className="flex items-center gap-2 p-2 bg-slate-900/60 border border-slate-800 rounded-2xl backdrop-blur-xl max-w-xl mx-auto shadow-2xl">
            <Search className="w-5 h-5 text-slate-500 ml-3 shrink-0" />
            <Input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleAnalyze()}
              placeholder="e.g. IRCTC, TCS, RELIANCE..."
              className="border-0 bg-transparent text-white text-base focus-visible:ring-0 focus-visible:ring-offset-0 px-2 h-12 font-['Plus_Jakarta_Sans']"
            />
            <Button 
              onClick={handleAnalyze}
              className="h-12 px-8 rounded-xl bg-white text-slate-950 hover:bg-slate-200 font-bold text-sm transition-all hover:scale-105"
            >
              Analyze &rarr;
            </Button>
          </div>

          {/* Stock Tags */}
          <div className="flex flex-wrap justify-center gap-2 mt-6">
            {popularStocks.map((s) => (
              <button
                key={s}
                onClick={() => setQuery(s)}
                className="px-4 py-1.5 rounded-full border border-slate-800 bg-slate-900/30 text-xs font-medium text-slate-400 hover:text-white hover:border-slate-600 hover:bg-slate-800 transition-all font-['Plus_Jakarta_Sans']"
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