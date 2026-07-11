import { useState } from 'react'
import Nav from './components/Nav'
import Hero from './components/Hero'
import AuthModal from './components/AuthModal'
import DatasetExplorer from './components/DatasetExplorer'
import { useAuth } from './lib/auth'

export default function App() {
  const { user, logout } = useAuth()
  const [authOpen, setAuthOpen] = useState(false)

  // "Start a run" requires a session — open auth if signed out.
  const start = () => {
    if (!user) setAuthOpen(true)
    else document.getElementById('workflow')?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="relative">
      <Nav user={user} onSignIn={() => setAuthOpen(true)} onSignOut={logout} />
      <main>
        <Hero onStart={start} />
        <DatasetExplorer onUse={(ref) => console.log('use dataset', ref)} />
      </main>
      <footer className="border-t border-edge py-8 text-center data text-xs text-muted">
        jantrikota.ai — natural-language AutoML · built with an agentic workflow
      </footer>
      <AuthModal open={authOpen} onClose={() => setAuthOpen(false)} />
    </div>
  )
}
