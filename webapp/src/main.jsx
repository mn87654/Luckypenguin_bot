import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';

const tg = window.Telegram?.WebApp;
if (tg) {
  try { tg.expand(); tg.ready(); } catch {}
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
