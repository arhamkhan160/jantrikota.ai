import { Button } from './ui/Button'

type User = { email?: string } | null

export default function Nav({
  user,
  onSignIn,
  onSignOut,
}: {
  user?: User
  onSignIn?: () => void
  onSignOut?: () => void
}) {
  return (
    <header className="fixed inset-x-0 top-0 z-50">
      <nav className="glass mx-auto mt-4 flex max-w-6xl items-center justify-between rounded-full px-5 py-3">
        <a href="#top" className="flex items-center gap-2.5">
          <span className="relative flex h-2.5 w-2.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-plasma-cyan opacity-60" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full [background:var(--holo)]" />
          </span>
          <span className="font-display text-lg font-semibold tracking-tight holo-text">jantrikota</span>
        </a>

        <div className="hidden items-center gap-7 text-sm text-muted md:flex">
          <a href="#datasets" className="transition hover:text-ink">Datasets</a>
          <a href="#workflow" className="transition hover:text-ink">Run agent</a>
        </div>

        {user ? (
          <div className="flex items-center gap-3">
            <span className="hidden data text-xs text-muted sm:inline">{user.email}</span>
            <Button variant="ghost" onClick={onSignOut}>Sign out</Button>
          </div>
        ) : (
          <Button variant="ghost" onClick={onSignIn}>Sign in</Button>
        )}
      </nav>
    </header>
  )
}
