import NeuralField from './NeuralField'
import { Button } from './ui/Button'

const CHIPS = ['4 dataset sources', 'human-in-the-loop', 'JWT-secured', 'LangGraph agent']

export default function Hero({ onStart }: { onStart?: () => void }) {
  return (
    <section id="top" className="relative flex min-h-screen items-center overflow-hidden">
      <NeuralField className="absolute inset-0 h-full w-full" />
      {/* fade the field into the page bottom */}
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-40 bg-gradient-to-b from-transparent to-void" />

      <div className="relative z-10 mx-auto w-full max-w-4xl px-6 text-center">
        <span className="data inline-block rounded-full border border-edge px-3 py-1 text-[11px] uppercase tracking-[0.3em] text-muted">
          Natural-language AutoML
        </span>

        <h1 className="mt-6 text-5xl font-bold leading-[1.02] sm:text-6xl md:text-7xl">
          Describe the problem.
          <br />
          <span className="holo-text">The agent builds the model.</span>
        </h1>

        <p className="mx-auto mt-6 max-w-xl text-balance text-muted">
          Search datasets across OpenML, HuggingFace, Kaggle and the open web. Validate the data
          with a human in the loop, train, and get a live prediction endpoint — driven by one request.
        </p>

        <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
          <Button variant="primary" onClick={onStart}>Start a run →</Button>
          <a href="#datasets"><Button variant="subtle">Explore datasets</Button></a>
        </div>

        <div className="mt-12 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 data text-xs text-muted">
          {CHIPS.map((c, i) => (
            <span key={c} className="flex items-center gap-2">
              {i > 0 && <span className="text-edge">/</span>}
              {c}
            </span>
          ))}
        </div>
      </div>
    </section>
  )
}
