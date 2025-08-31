import React, { useEffect, useState } from 'react';
import { post, getTgUser } from './api';

export default function App(){
  const [user, setUser] = useState(null);
  const [coins, setCoins] = useState(0);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');
  const tg = window.Telegram?.WebApp;

  async function load(){
    try {
      const u = getTgUser();
      if (!u) { setLoading(false); return; }
      const res = await post('/api/me', u);
      if (res?.ok) {
        setUser(res.user);
        setCoins(res.user?.coins ?? 0);
        setTasks(res.tasks ?? []);
      } else {
        setErr(res?.error || 'Failed to load /api/me');
      }
    } catch (e) {
      setErr(e?.message || 'Network/CORS error');
    } finally {
      setLoading(false);
    }
  }

  useEffect(()=>{ load(); },[]);

  async function claimDaily(){
    try{
      const res = await post('/api/daily/claim', getTgUser());
      if(res.ok){
        setCoins(res.new_balance);
        tg?.HapticFeedback?.notificationOccurred('success');
      } else if(res.reason==='already'){
        tg?.HapticFeedback?.impactOccurred('light');
        alert('Already claimed today!');
      } else {
        alert(res.error || 'Failed');
      }
    } catch { alert('Network error'); }
  }

  async function checkTask(id){
    try{
      const res = await post('/api/tasks/check', { ...getTgUser(), task_id:id });
      if(res.ok){ setCoins(res.new_balance); alert('Reward added!'); }
      else { alert(res.error || 'Not verified yet. Join/Open first then press Check.'); }
    } catch { alert('Network error'); }
  }

  if (loading) return <div style={{padding:16}}>Loading… (waking server?)</div>;
  if (err)     return <div style={{padding:16, color:'#f77'}}>Error: {String(err)}</div>;
  if (!user)   return <div style={{padding:16}}>Open from Telegram to continue.</div>;

  return (
    <div style={{padding:16, maxWidth:560, margin:'0 auto'}}>
      <header style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:12}}>
        <div>
          <div style={{opacity:.8,fontSize:14}}>Welcome</div>
          <div style={{fontSize:20,fontWeight:700}}>@{user.username || user.tg_id}</div>
        </div>
        <div style={{fontSize:18,fontWeight:700}}>💰 {coins}</div>
      </header>

      <div style={{background:'rgba(255,255,255,.06)',padding:16,borderRadius:16,marginBottom:12}}>
        <div style={{fontSize:16,fontWeight:700,marginBottom:8}}>Daily Reward</div>
        <button onClick={claimDaily} style={btn()}>Claim</button>
      </div>

      <div style={{background:'rgba(255,255,255,.06)',padding:16,borderRadius:16}}>
        <div style={{fontSize:16,fontWeight:700,marginBottom:8}}>Tasks</div>
        {tasks.length===0 && <div>No tasks yet.</div>}
        {tasks.map(t=>(
          <div key={t.id} style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'12px 0',borderTop:'1px solid rgba(255,255,255,.08)'}}>
            <div>
              <div style={{fontWeight:700}}>{t.title}</div>
              <div style={{opacity:.7,fontSize:13}}>{t.desc}</div>
            </div>
            <div style={{display:'flex',gap:8}}>
              <a href={t.url} target="_blank" rel="noreferrer" style={btn('outline')}>Open</a>
              <button onClick={()=>checkTask(t.id)} style={btn()}>Check</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function btn(variant){
  return {
    padding:'10px 14px',
    borderRadius:12,
    fontWeight:600,
    border: variant==='outline' ? '1px solid rgba(255,255,255,.2)' : 'none',
    background: variant==='outline' ? 'transparent' : '#2ea043',
    color: variant==='outline' ? 'inherit' : '#fff',
  };
}
