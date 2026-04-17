import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'

// Handle SPA redirect from 404.html (GitHub Pages routing fix)
const redirect = sessionStorage.getItem('spa_redirect')
if (redirect) {
  sessionStorage.removeItem('spa_redirect')
  window.history.replaceState(null, '', '/kartsiing.github.io' + redirect)
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
)
