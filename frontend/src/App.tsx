import Nav from './components/Nav'
import Hero from './components/Hero'

export default function App() {
  return (
    <div className="relative">
      <Nav />
      <main>
        <Hero />
      </main>
      <footer className="border-t border-edge py-8 text-center data text-xs text-muted">
        jantrikota.ai — natural-language AutoML · built with an agentic workflow
      </footer>
    </div>
  )
}
