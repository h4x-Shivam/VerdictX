import { useLocation, useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useEffect, useRef } from 'react';

const VC = {
  'STRONG BUY':  { color: '#00ffb3', bg: 'rgba(0,255,179,0.10)', border: 'rgba(0,255,179,0.3)', label: 'Exceptional Opportunity' },
  'BUY':         { color: '#4ade80', bg: 'rgba(74,222,128,0.08)', border: 'rgba(74,222,128,0.25)', label: 'Positive Signal — Consider Buying' },
  'HOLD':        { color: '#fbbf24', bg: 'rgba(251,191,36,0.08)', border: 'rgba(251,191,36,0.22)', label: 'Neutral Outlook' },
  'SELL':        { color: '#f87171', bg: 'rgba(248,113,113,0.08)', border: 'rgba(248,113,113,0.22)', label: 'Weak Signal — Consider Exiting' },
  'STRONG SELL': { color: '#ff1744', bg: 'rgba(255,23,68,0.12)', border: 'rgba(255,23,68,0.3)', label: 'High Risk — Strong Exit Signal' },
};
const RC = { LOW: '#4ade80', MEDIUM: '#fbbf24', HIGH: '#f87171' };
const SC = { POSITIVE: '#4ade80', NEGATIVE: '#f87171', NEUTRAL: '#fbbf24', MIXED: '#fbbf24' };

const fp = v => v == null ? 'N/A' : `₹${parseFloat(v).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const fmtCr = v => { if (!v) return 'N/A'; const c = parseFloat(v)/1e7; return c>=1e5?`₹${(c/1e5).toFixed(2)} Lakh Cr`:c>=1e3?`₹${(c/1e3).toFixed(1)}K Cr`:`₹${c.toFixed(1)} Cr`; };
const fmtPct = v => v == null ? 'N/A' : `${(parseFloat(v)*100).toFixed(2)}%`;

function Card({ children, style }) {
  return <div style={{ background:'rgba(8,14,24,0.9)', border:'1px solid rgba(255,255,255,0.07)', borderRadius:16, padding:'20px 24px', ...style }}>{children}</div>;
}
function Lbl({ children }) {
  return <div style={{ fontSize:10, fontWeight:700, color:'#475569', textTransform:'uppercase', letterSpacing:'0.1em', marginBottom:12 }}>{children}</div>;
}
function Bar({ label, val, weight, color }) {
  const p = Math.max(0, Math.min(100, val||0));
  return (
    <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:7 }}>
      <div style={{ width:110, fontSize:12, color:'#64748b', flexShrink:0 }}>{label} <span style={{color:'#334155',fontSize:10}}>({weight})</span></div>
      <div style={{ flex:1, height:6, background:'rgba(255,255,255,0.05)', borderRadius:3, overflow:'hidden' }}>
        <motion.div initial={{width:0}} animate={{width:`${p}%`}} transition={{duration:0.8}} style={{height:'100%',background:color,borderRadius:3}} />
      </div>
      <div style={{ width:30, textAlign:'right', fontSize:12, fontWeight:600, color:'white' }}>{Math.round(p)}</div>
    </div>
  );
}

function Ring({ pct=0, color='#22d3ee', size=88 }) {
  const r=28, c=size/2, circ=2*Math.PI*r, fill=circ*(Math.max(0,Math.min(100,pct))/100), gap=circ-fill;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={c} cy={c} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="5"/>
      <circle cx={c} cy={c} r={r} fill="none" stroke={color} strokeWidth="5" strokeLinecap="round"
        strokeDasharray={`${fill.toFixed(1)} ${gap.toFixed(1)}`} transform={`rotate(-90 ${c} ${c})`}/>
      <text x={c} y={c-2} textAnchor="middle" fill="white" fontSize="13" fontWeight="800">{pct}%</text>
      <text x={c} y={c+11} textAnchor="middle" fill="#64748b" fontSize="8">confidence</text>
    </svg>
  );
}

function TvChart({ ticker }) {
  const ref = useRef(null);
  const sym = ticker.replace(/\.NS|\.BO/g,'');
  useEffect(() => {
    if (!ref.current) return;
    ref.current.innerHTML = '';
    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/tv.js';
    script.async = true;
    script.onload = () => {
      if (window.TradingView) {
        new window.TradingView.widget({
          autosize: true, symbol: `BSE:${sym.toUpperCase()}`, interval: 'D',
          timezone: 'Asia/Kolkata', theme: 'dark', style: '1', locale: 'en',
          enable_publishing: false, backgroundColor: 'rgba(8,14,24,1)',
          gridColor: 'rgba(255,255,255,0.04)', hide_top_toolbar: true,
          hide_legend: true, save_image: false, container_id: 'tv_chart',
        });
      }
    };
    ref.current.appendChild(script);
  }, [sym]);
  return (
    <div style={{ borderRadius:12, overflow:'hidden', background:'rgba(8,14,24,0.9)', border:'1px solid rgba(255,255,255,0.07)' }}>
      <div id="tv_chart" ref={ref} style={{ height:240 }} />
    </div>
  );
}

export default function ResultsPage() {
  const { ticker } = useParams();
  const { state } = useLocation();
  const navigate = useNavigate();
  const r = state?.result;

  if (!r) return (
    <div style={{ minHeight:'100vh', background:'#050a0e', color:'white', display:'flex', alignItems:'center', justifyContent:'center', flexDirection:'column', gap:16 }}>
      <div style={{ fontSize:48 }}>⚠️</div>
      <div style={{ fontSize:18, fontWeight:700 }}>No data — run an analysis first</div>
      <button onClick={() => navigate('/')} style={{ padding:'10px 24px', borderRadius:10, background:'rgba(34,211,238,0.1)', border:'1px solid rgba(34,211,238,0.3)', color:'#22d3ee', cursor:'pointer', fontFamily:'inherit' }}>Go Home</button>
    </div>
  );

  const { info={}, raw={}, fv={}, news_items=[], sent={}, bull={}, bear={}, verdict={}, fund_data={}, validated={} } = r;
  const fvP = fv?.primary||{};
  const vv = verdict.verdict||'HOLD'; const vc = VC[vv]||VC.HOLD;
  const cf = verdict.confidence||50; const rsk = verdict.risk||'MEDIUM';
  const scores = validated.scores||verdict.scores||{};
  const composite = validated.composite||verdict.composite||0;
  const bullPts = bull.bull_points||[]; const bearPts = bear.bear_points||[];
  const validation = verdict.validation_applied||[];
  const company = info.company_name||ticker;
  const cur = raw.currentPrice; const pch = raw.pchange||0; const ch_ = raw.change||0;
  const isUp = pch>=0;

  const metrics = [
    ['Market Cap', fmtCr(info.market_cap)],
    ['P/E (TTM)', info.trailing_pe ? info.trailing_pe.toFixed(2) : 'N/A'],
    ['P/B Ratio', info.pb_ratio ? info.pb_ratio.toFixed(2) : 'N/A'],
    ['EPS (TTM)', fp(info.trailing_eps)],
    ['Revenue', fmtCr(info.total_revenue)],
    ['VWAP', raw.vwap ? fp(raw.vwap) : 'Market closed'],
    ['Delivery %', info.delivery_pct ? `${info.delivery_pct}%` : 'N/A'],
    ['Div Yield', fmtPct(info.dividend_yield)],
    ['ROE', info.return_on_equity ? `${(info.return_on_equity*100).toFixed(1)}%` : 'N/A'],
    ['Debt/Equity', info.debt_to_equity ? info.debt_to_equity.toFixed(2) : 'N/A'],
    ['52W High', fp(raw.week52High)],
    ['52W Low', fp(raw.week52Low)],
  ];

  return (
    <div style={{ minHeight:'100vh', background:'#050a0e', color:'white', fontFamily:'inherit' }}>
      <div style={{ position:'fixed', inset:0, pointerEvents:'none', zIndex:0,
        background:'radial-gradient(ellipse 70% 50% at 15% 30%, rgba(0,200,100,0.04) 0%, transparent 60%), radial-gradient(ellipse 60% 40% at 85% 60%, rgba(200,30,30,0.04) 0%, transparent 60%)' }} />

      <div style={{ position:'relative', zIndex:10, maxWidth:1536, margin:'0 auto', padding:'0 32px 80px' }}>

        {/* Navbar */}
        <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'18px 0 26px', borderBottom:'1px solid rgba(255,255,255,0.06)', marginBottom:28 }}>
          <button onClick={() => navigate('/')} style={{ background:'transparent', border:'none', color:'#64748b', cursor:'pointer', fontFamily:'inherit', fontSize:13, padding:'8px 12px', borderRadius:8, transition:'color 0.2s' }}
            onMouseEnter={e=>e.currentTarget.style.color='white'} onMouseLeave={e=>e.currentTarget.style.color='#64748b'}>← Back</button>
          <div style={{ display:'flex', alignItems:'center', gap:8 }}>
            <span style={{ color:'#22d3ee', fontWeight:900, fontSize:18 }}>X</span>
            <span style={{ fontWeight:700, fontSize:14, letterSpacing:'0.14em' }}>VERDICTX</span>
          </div>
          <button onClick={() => navigate(`/analyze/${ticker}`)} style={{ padding:'8px 18px', borderRadius:8, fontSize:12, fontWeight:600, background:'rgba(34,211,238,0.08)', border:'1px solid rgba(34,211,238,0.2)', color:'#22d3ee', cursor:'pointer', fontFamily:'inherit' }}>Re-analyze</button>
        </div>

        {/* Row 1: Company + Verdict */}
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:18, marginBottom:18 }}>
          <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{duration:0.5}}>
            <Card>
              <div style={{ display:'flex', alignItems:'flex-start', gap:14, marginBottom:14 }}>
                <div style={{ width:48, height:48, borderRadius:12, background:'rgba(34,211,238,0.08)', border:'1px solid rgba(34,211,238,0.15)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:22, flexShrink:0 }}>🏢</div>
                <div>
                  <h1 style={{ fontSize:22, fontWeight:900, letterSpacing:'-0.02em', margin:'0 0 3px' }}>{company}</h1>
                  <div style={{ fontSize:12, color:'#64748b' }}>NSE: {info.nse_symbol||ticker}</div>
                  {info.sector && <span style={{ display:'inline-block', marginTop:6, padding:'2px 10px', borderRadius:999, background:'rgba(99,102,241,0.1)', border:'1px solid rgba(99,102,241,0.2)', color:'#a5b4fc', fontSize:11, fontWeight:600 }}>{info.sector}</span>}
                </div>
              </div>
              <div style={{ marginBottom:4 }}><Lbl>CURRENT PRICE</Lbl></div>
              <div style={{ fontSize:34, fontWeight:900, letterSpacing:'-0.02em' }}>{fp(cur)}</div>
              <div style={{ fontSize:14, color:isUp?'#4ade80':'#f87171', fontWeight:600, marginTop:4 }}>
                {isUp?'+':''}{(ch_||0).toFixed(2)} ({isUp?'+':''}{(pch||0).toFixed(2)}%) Today
              </div>
            </Card>
          </motion.div>

          <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{duration:0.5,delay:0.1}}>
            <Card style={{ background:vc.bg, border:`1px solid ${vc.border}`, display:'flex', alignItems:'center', justifyContent:'space-between' }}>
              <div>
                <Lbl>AI VERDICT</Lbl>
                <div style={{ fontSize:42, fontWeight:900, color:vc.color, letterSpacing:'-0.02em', lineHeight:1, marginBottom:8 }}>{vv}</div>
                <div style={{ fontSize:13, color:vc.color, opacity:0.85, marginBottom:10 }}>{vc.label}</div>
                <div style={{ display:'flex', gap:14 }}>
                  <div style={{ fontSize:12, color:'#64748b' }}>Risk: <span style={{ color:RC[rsk], fontWeight:600 }}>{rsk}</span></div>
                  <div style={{ fontSize:12, color:'#64748b' }}>Timeframe: <span style={{ color:'white', fontWeight:600 }}>{verdict.timeframe||'short-term'}</span></div>
                </div>
                {verdict.target_upside_pct && <div style={{ fontSize:12, color:vc.color, marginTop:6 }}>Target: +{verdict.target_upside_pct.toFixed(1)}%</div>}
              </div>
              <Ring pct={cf} color={vc.color} size={90} />
            </Card>
          </motion.div>
        </div>

        {/* Row 2: 4 tiles */}
        <motion.div initial={{opacity:0,y:16}} animate={{opacity:1,y:0}} transition={{duration:0.5,delay:0.15}}
          style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:14, marginBottom:18 }}>
          {[
            { label:'FAIR VALUE (EST.)', val:fvP.value?fp(fvP.value):'N/A', sub:fvP.upside!=null?`${fvP.upside>=0?'↑':'↓'} ${Math.abs(fvP.upside).toFixed(1)}% ${fvP.upside>=0?'Upside':'Downside'}`:'', color:fvP.upside>=0?'#4ade80':'#f87171', hint:fvP.method },
            { label:'MARKET SENTIMENT', val:(sent.sentiment||'N/A').charAt(0)+(sent.sentiment||'N/A').slice(1).toLowerCase(), sub:`Score: ${sent.score>=0?'+':''}${sent.score||0}`, color:SC[sent.sentiment]||'#fbbf24', hint:'' },
            { label:'RISK LEVEL', val:rsk, sub:{LOW:'Low Risk',MEDIUM:'Moderate Risk',HIGH:'High Risk'}[rsk]||'', color:RC[rsk]||'#fbbf24', hint:'' },
            { label:'FINANCIAL HEALTH', val:`${((fund_data.score||50)/10).toFixed(1)}/10`, sub:(fund_data.score||50)>=70?'Strong':(fund_data.score||50)>=50?'Moderate':'Weak', color:(fund_data.score||50)>=70?'#4ade80':(fund_data.score||50)>=50?'#fbbf24':'#f87171', hint:`${fund_data.metrics_available||0}/${fund_data.metrics_total||8} metrics` },
          ].map((t,i) => (
            <Card key={i} style={{ padding:'16px 18px' }}>
              <Lbl>{t.label}</Lbl>
              <div style={{ fontSize:22, fontWeight:800, letterSpacing:'-0.01em', marginBottom:4 }}>{t.val}</div>
              <div style={{ fontSize:12, color:t.color, fontWeight:600 }}>{t.sub}</div>
              {t.hint && <div style={{ fontSize:10, color:'#334155', marginTop:4 }}>{t.hint}</div>}
            </Card>
          ))}
        </motion.div>

        {/* Row 3: Metrics + Chart */}
        <div style={{ display:'grid', gridTemplateColumns:'5fr 7fr', gap:18, marginBottom:18 }}>
          <motion.div initial={{opacity:0,y:16}} animate={{opacity:1,y:0}} transition={{duration:0.5,delay:0.2}}>
            <Card>
              <Lbl>KEY METRICS</Lbl>
              {metrics.map(([k,v]) => (
                <div key={k} style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'7px 0', borderBottom:'1px solid rgba(255,255,255,0.04)' }}>
                  <span style={{ fontSize:12.5, color:'#64748b' }}>{k}</span>
                  <span style={{ fontSize:13, fontWeight:600, color:'white', fontFamily:'monospace' }}>{v}</span>
                </div>
              ))}
            </Card>
          </motion.div>

          <motion.div initial={{opacity:0,y:16}} animate={{opacity:1,y:0}} transition={{duration:0.5,delay:0.25}} style={{ display:'flex', flexDirection:'column', gap:18 }}>
            <TvChart ticker={ticker} />

            {/* Decision Engine */}
            <Card>
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:14 }}>
                <Lbl>🧮 DECISION ENGINE SCORES</Lbl>
                <span style={{ fontSize:11, padding:'3px 10px', borderRadius:999, background:'rgba(255,255,255,0.05)', color:'#64748b' }}>Composite: {composite}</span>
              </div>
              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:10, marginBottom:16 }}>
                {[['🟢 Bull Score', bull.overall_bull_score||50, '#4ade80'], ['🔴 Bear Score', bear.overall_bear_score||50, '#f87171']].map(([lbl,val,col]) => (
                  <div key={lbl} style={{ background:'rgba(255,255,255,0.03)', borderRadius:10, padding:'10px 12px', border:`1px solid ${col}20` }}>
                    <div style={{ fontSize:10, color:'#475569', marginBottom:5 }}>{lbl}</div>
                    <div style={{ fontSize:22, fontWeight:800, color:col }}>{val}</div>
                    <div style={{ marginTop:6, height:4, background:'rgba(255,255,255,0.06)', borderRadius:2, overflow:'hidden' }}>
                      <motion.div initial={{width:0}} animate={{width:`${val}%`}} transition={{duration:0.8,delay:0.5}} style={{height:'100%',background:col,borderRadius:2}} />
                    </div>
                  </div>
                ))}
              </div>
              <Bar label="Fundamentals" val={scores.fundamentals} weight="35%" color="#22d3ee" />
              <Bar label="Bull Agent" val={scores.bull} weight="20%" color="#4ade80" />
              <Bar label="Bear Agent" val={scores.bear} weight="20%" color="#f87171" />
              <Bar label="Sentiment" val={scores.sentiment} weight="15%" color="#fbbf24" />
              <Bar label="Fair Value" val={scores.fair_value} weight="10%" color="#a78bfa" />
              <div style={{ marginTop:12, paddingTop:10, borderTop:'1px solid rgba(255,255,255,0.05)', display:'flex', justifyContent:'space-between', fontSize:11, color:'#475569' }}>
                <span>Data completeness</span>
                <span style={{ color:(scores.data_completeness||0)>=0.7?'#4ade80':'#fbbf24', fontWeight:600 }}>{Math.round((scores.data_completeness||0)*100)}%</span>
              </div>
              {validation.length>0 && (
                <div style={{ marginTop:10, paddingTop:10, borderTop:'1px solid rgba(255,255,255,0.05)' }}>
                  {validation.map((v,i) => <div key={i} style={{ fontSize:11, color:'#fbbf24', marginTop:3 }}>⚠ {v}</div>)}
                </div>
              )}
            </Card>
          </motion.div>
        </div>

        {/* Row 4: AI Analysis + Highlights */}
        <motion.div initial={{opacity:0,y:16}} animate={{opacity:1,y:0}} transition={{duration:0.5,delay:0.3}}
          style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:18, marginBottom:18 }}>

          {/* Left: Reasoning */}
          <Card>
            <Lbl>AI ANALYSIS SUMMARY</Lbl>
            <p style={{ color:'#94a3b8', fontSize:14, lineHeight:1.75, margin:'0 0 16px' }}>{verdict.final_reasoning}</p>
            {verdict.key_catalyst && (
              <div style={{ padding:'12px 14px', borderRadius:10, background:'rgba(74,222,128,0.06)', border:'1px solid rgba(74,222,128,0.15)', marginBottom:10 }}>
                <div style={{ fontSize:10, color:'#4ade80', fontWeight:700, marginBottom:5 }}>KEY CATALYST</div>
                <div style={{ fontSize:13, color:'#94a3b8', lineHeight:1.6 }}>{verdict.key_catalyst}</div>
              </div>
            )}
            {verdict.key_risk && (
              <div style={{ padding:'12px 14px', borderRadius:10, background:'rgba(248,113,113,0.06)', border:'1px solid rgba(248,113,113,0.15)' }}>
                <div style={{ fontSize:10, color:'#f87171', fontWeight:700, marginBottom:5 }}>KEY RISK</div>
                <div style={{ fontSize:13, color:'#94a3b8', lineHeight:1.6 }}>{verdict.key_risk}</div>
              </div>
            )}
            {verdict.signal_breakdown && (
              <div style={{ marginTop:12, fontSize:10, color:'#334155', fontFamily:'monospace', lineHeight:1.7, wordBreak:'break-all' }}>
                {verdict.signal_breakdown}
              </div>
            )}
          </Card>

          {/* Right: Highlights */}
          <Card>
            <Lbl>HIGHLIGHTS</Lbl>
            <div style={{ marginBottom:8 }}>
              {bullPts.slice(0,4).map((p,i) => (
                <div key={i} style={{ display:'flex', gap:8, marginBottom:10, alignItems:'flex-start' }}>
                  <span style={{ color:'#4ade80', fontSize:16, lineHeight:1.2, flexShrink:0 }}>✓</span>
                  <div>
                    <div style={{ fontSize:13, color:'#cbd5e1', lineHeight:1.5 }}>{p.point}</div>
                    {p.metric_cited && <div style={{ fontSize:11, color:'#475569', marginTop:2 }}>{p.metric_cited}</div>}
                  </div>
                </div>
              ))}
            </div>
            <div style={{ borderTop:'1px solid rgba(255,255,255,0.05)', paddingTop:10 }}>
              {bearPts.slice(0,3).map((p,i) => (
                <div key={i} style={{ display:'flex', gap:8, marginBottom:10, alignItems:'flex-start' }}>
                  <span style={{ color:'#f87171', fontSize:14, lineHeight:1.2, flexShrink:0 }}>▲</span>
                  <div>
                    <div style={{ fontSize:13, color:'#cbd5e1', lineHeight:1.5 }}>{p.point}</div>
                    {p.metric_cited && <div style={{ fontSize:11, color:'#475569', marginTop:2 }}>{p.metric_cited}</div>}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </motion.div>

        {/* Row 5: News 2-col grid */}
        {news_items.length>0 && (
          <motion.div initial={{opacity:0,y:16}} animate={{opacity:1,y:0}} transition={{duration:0.5,delay:0.4}}>
            <Card>
              <Lbl>LATEST NEWS ({news_items.length} relevant articles)</Lbl>
              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:10 }}>
                {news_items.slice(0,8).map((item,i) => (
                  <a key={i} href={item.link||'#'} target="_blank" rel="noopener noreferrer" style={{ textDecoration:'none' }}>
                    <div style={{ padding:'12px 14px', borderRadius:10, background:'rgba(255,255,255,0.02)', border:'1px solid rgba(255,255,255,0.05)', height:'100%', transition:'border-color 0.2s, background 0.2s', cursor:'pointer' }}
                      onMouseEnter={e=>{e.currentTarget.style.borderColor='rgba(34,211,238,0.2)';e.currentTarget.style.background='rgba(34,211,238,0.03)';}}
                      onMouseLeave={e=>{e.currentTarget.style.borderColor='rgba(255,255,255,0.05)';e.currentTarget.style.background='rgba(255,255,255,0.02)';}}>
                      <div style={{ fontSize:11, color:'#22d3ee', fontWeight:600, marginBottom:5 }}>{item.source||'News'}</div>
                      <div style={{ fontSize:13, fontWeight:500, color:'white', lineHeight:1.4, marginBottom:5 }}>{item.title||'Article'}</div>
                      {item.summary && <div style={{ fontSize:11, color:'#475569', lineHeight:1.5 }}>{item.summary.slice(0,100)}…</div>}
                      <div style={{ fontSize:10, color:'#334155', marginTop:6 }}>{item.age_label||item.published||''}</div>
                    </div>
                  </a>
                ))}
              </div>
            </Card>
          </motion.div>
        )}

        <div style={{ textAlign:'center', marginTop:28, fontSize:11, color:'#334155' }}>
          ⚠️ For informational purposes only. Not financial advice. Always do your own research.
        </div>
      </div>
    </div>
  );
}
