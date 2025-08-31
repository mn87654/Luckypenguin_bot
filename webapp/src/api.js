const API = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '');

export async function post(path, body) {
  const res = await fetch(API + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    credentials: 'include',
  });

  const text = await res.text();
  try {
    return JSON.parse(text);
  } catch {
    return { ok: false, error: 'bad-json', raw: text };
  }
}

export function getTgUser() {
  const w = window.Telegram?.WebApp;
  const u = w?.initDataUnsafe?.user;
  if (!u) return null;
  return {
    tg_id: u.id,
    username: u.username || '',
    first_name: u.first_name || '',
    last_name: u.last_name || '',
    init_data: w?.initData || '' // backend verify के लिए
  };
}
