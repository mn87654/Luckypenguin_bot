import React, { useEffect, useState } from 'react'
import { post, getTgUser } from './api'


export default function App(){
const [user, setUser] = useState(null)
const [coins, setCoins] = useState(0)
const [tasks, setTasks] = useState([])
const [loading, setLoading] = useState(true)
const tg = window.Telegram?.WebApp


async function load(){
const u = getTgUser()
if(!u){
setLoading(false)
return
}
const res = await post('/api/me', u)
if(res.ok){
setUser(res.user)
setCoins(res.user.coins)
setTasks(res.tasks)
}
setLoading(false)
}


useEffect(()=>{ load() },[])


async function claimDaily(){
const res = await post('/api/daily/claim', getTgUser())
if(res.ok){
setCoins(res.new_balance)
tg?.HapticFeedback?.notificationOccurred('success')
} else if(res.reason==='already'){
tg?.HapticFeedback?.impactOccurred('light')
alert('Already claimed today!')
}
}


async function checkTask(id){
const res = await post('/api/tasks/check', { ...getTgUser(), task_id:id })
if(res.ok){ setCoins(res.new_balance); alert('Reward added!') }
else { alert('Not verified yet. Join/Open first then press Check.') }
}


if(loading) return <div style={{padding:16}}>Loading…</div>
if(!user) return <div style={{padding:16}}>Open from Telegram to continue.</div>


return (
<div style={{padding:16, maxWidth:560, margin:'0 auto'}}>
<header style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:12}}>
<div>
<div style={{opacity:.8,fontSize:14}}>Welcome</div>
<div style={{fontSize:20,fontWeight:700}}>@{user.username||user.tg_id}</div>
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
{tasks.map(t=> (
<div key={t.id} style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'12px 0',borderTop:'1px solid rgba(255,255,255,.08)'}}>
<div>
<div style={{fontWeight:￼Enter
