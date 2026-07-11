import { useState } from 'react'
import { useAuth } from '../lib/auth'
import { ApiError } from '../lib/api'
import { Button } from './ui/Button'
import { Input } from './ui/Input'

export default function AuthModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { login, signup } = useAuth()
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  if (!open) return null

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true); setError(null); setNotice(null)
    try {
      if (mode === 'login') {
        await login(email, password)
        onClose()
      } else {
        const { needsConfirm } = await signup(email, password)
        if (needsConfirm) setNotice('Account created. Check your email to confirm, then sign in.')
        else onClose()
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-void/70 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="holo-border w-full max-w-sm rounded-2xl p-7"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-6 text-center">
          <h2 className="text-2xl font-semibold">
            {mode === 'login' ? 'Welcome back' : 'Create account'}
          </h2>
          <p className="mt-1 text-sm text-muted">
            {mode === 'login' ? 'Sign in to run the agent.' : 'Sign up to start building models.'}
          </p>
        </div>

        <form onSubmit={submit} className="space-y-3">
          <Input
            type="email" required placeholder="you@example.com" value={email}
            autoComplete="email" onChange={(e) => setEmail(e.target.value)}
          />
          <Input
            type="password" required placeholder="Password" value={password}
            minLength={6} autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            onChange={(e) => setPassword(e.target.value)}
          />

          {error && <p className="data text-xs text-plasma-magenta">{error}</p>}
          {notice && <p className="data text-xs text-mint">{notice}</p>}

          <Button type="submit" variant="primary" disabled={busy} className="w-full">
            {busy ? 'Working…' : mode === 'login' ? 'Sign in' : 'Sign up'}
          </Button>
        </form>

        <button
          className="mt-5 w-full text-center text-sm text-muted transition hover:text-ink"
          onClick={() => { setMode(mode === 'login' ? 'signup' : 'login'); setError(null); setNotice(null) }}
        >
          {mode === 'login' ? "No account? Sign up" : 'Have an account? Sign in'}
        </button>
      </div>
    </div>
  )
}
