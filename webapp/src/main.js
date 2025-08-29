// webapp/src/main.js
import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'

// Telegram WebApp init
const tg = window.Telegram?.WebApp
if (tg) {
  tg.expand()
  tg.ready()
}

// Render React App
createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
