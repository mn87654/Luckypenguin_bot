import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'


const tg = window.Telegram?.WebApp
if (tg) {
tg.expand()
tg.ready()
}


createRoot(document.getElementById('root')).render(<App />)
