import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

import { GoogleOAuthProvider } from '@react-oauth/google'

const GOOGLE_CLIENT_ID = "889565597256-ja3mm4qn1hje2f2ojekfa6eqmjivhtfp.apps.googleusercontent.com" // Placeholder

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <GoogleOAuthProvider clientId={"889565597256-ja3mm4qn1hje2f2ojekfa6eqmjivhtfp.apps.googleusercontent.com"}>
      <App />
    </GoogleOAuthProvider>
  </StrictMode>,
)
