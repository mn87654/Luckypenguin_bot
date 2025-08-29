export async function post(path, payload){
const res = await fetch(path, {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify(payload)
})
return res.json()
}


export function getTgUser(){
const tg = window.Telegram?.WebApp
const u = tg?.initDataUnsafe?.user
return u ? { user_id: u.id, username: u.username || '' } : null
}
