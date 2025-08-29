// webapp/src/main.jsx
import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'   // App.jsx को ऑटो-रिज़ॉल्व कर लेगा

// Telegram WebApp init (optional)
const tg = window.Telegram?.WebApp
if (tg) {
  tg.expand()
  tg.ready()
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)

