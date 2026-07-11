import { useState } from 'react'
import { ApiError } from '../lib/api'
import { useAuth } from '../lib/auth'
import { startAgent, answerAgent, type AgentResponse } from '../lib/agent'
import { SOURCE_COLOR, type SearchHit } from '../lib/datasets'
import { PipelineStations } from './PipelineStations'
import { MetricChart } from './MetricChart'
import { Button } from './ui/Button'
import { Input } from './ui/Input'

type Phase = 'idle' | 'running' | 'awaiting' | 'done' | 'error'

export default function AgentRunner({ onSignIn }: { onSignIn?: () => void }) {
  const { user } = useAuth()
  const [query, setQuery] = useState('')
  const [phase, setPhase] = useState<Phase>('idle')
  const [stage, setStage] = useState(0)
  const [res, setRes] = useState<AgentResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  function apply(r: AgentResponse) {
    setRes(r)
    if (r.status === 'awaiting') {
      setStage(r.question?.type === 'confirm_target' ? 3 : 1)
      setPhase('awaiting')
    } else if (r.status === 'done') {
      setStage(6); setPhase('done')
    } else if (r.status === 'no_datasets') {
      setError('No datasets matched that request. Try rephrasing.'); setPhase('error')
    }
  }

  function fail(err: unknown) {
    setPhase('error')
    setError(err instanceof ApiError && err.status === 401 ? 'Sign in to run the agent.'
      : err instanceof ApiError ? err.message : 'The run failed. Try again.')
  }

  async function run(e: React.FormEvent) {
    e.preventDefault()
    if (!query.trim()) return
    if (!user) { onSignIn?.(); return }
    setPhase('running'); setStage(0); setError(null); setRes(null)
    try { apply(await startAgent(query.trim(), ['openml'])) } catch (err) { fail(err) }
  }

  async function answer(value: Record<string, unknown>, nextStage: number) {
    if (!res) return
    setPhase('running'); setStage(nextStage)
    try { apply(await answerAgent(res.agent_id, value)) } catch (err) { fail(err) }
  }

  const q = res?.question
  const report = res?.report

  return (
    <section id="workflow" className="mx-auto max-w-4xl scroll-mt-24 px-6 py-24">
      <div className="mb-10 text-center">
        <span className="data text-xs uppercase tracking-[0.3em] text-muted">Step 02 — Run the agent</span>
        <h2 className="mt-3 text-3xl font-semibold sm:text-4xl">
          One request. <span className="holo-text">A trained model.</span>
        </h2>
        <p className="mx-auto mt-3 max-w-lg text-sm text-muted">
          The agent searches, asks you to confirm the important calls, then trains and reports back.
        </p>
      </div>

      <form onSubmit={run} className="flex flex-col gap-3 sm:flex-row">
        <Input
          placeholder="e.g. predict wine quality from these features"
          value={query} onChange={(e) => setQuery(e.target.value)}
        />
        <Button type="submit" variant="primary" disabled={phase === 'running'} className="shrink-0">
          {phase === 'running' ? 'Working…' : user ? 'Run agent →' : 'Sign in to run'}
        </Button>
      </form>

      {phase !== 'idle' && (
        <div className="holo-border mt-8 rounded-2xl p-6">
          <PipelineStations active={stage} error={phase === 'error'} />

          <div className="mt-8">
            {phase === 'running' && (
              <p className="data animate-pulse text-center text-sm text-muted">
                {stage >= 4 ? 'Training models…' : 'Thinking…'}
              </p>
            )}

            {error && <p className="data text-center text-sm text-plasma-magenta">{error}</p>}

            {/* Interrupt: choose a dataset */}
            {phase === 'awaiting' && q?.type === 'choose_dataset' && (
              <div>
                <p className="mb-4 text-center text-sm text-muted">{q.message}</p>
                <div className="grid gap-3 sm:grid-cols-2">
                  {(q.candidates as SearchHit[]).slice(0, 6).map((c) => (
                    <button
                      key={c.ref}
                      onClick={() => answer({ ref: c.ref }, 2)}
                      className="holo-border rounded-xl p-3 text-left transition hover:-translate-y-0.5"
                    >
                      <span className={`data text-[10px] uppercase tracking-widest ${SOURCE_COLOR[c.source] ?? 'text-muted'}`}>
                        {c.source}
                      </span>
                      <div className="mt-1 truncate font-display">{c.name}</div>
                      {typeof c.confidence === 'number' && (
                        <div className="data mt-1 text-xs text-muted">{(c.confidence * 100).toFixed(0)}% match</div>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Interrupt: confirm the target column */}
            {phase === 'awaiting' && q?.type === 'confirm_target' && (
              <div className="text-center">
                <p className="mb-4 text-sm text-muted">{q.message}</p>
                <div className="flex flex-wrap justify-center gap-2">
                  {(q.candidates as string[]).map((col) => (
                    <button
                      key={col}
                      onClick={() => answer({ target: col }, 4)}
                      className="data holo-border rounded-full px-4 py-2 text-sm transition hover:text-white"
                    >
                      {col}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Final report */}
            {phase === 'done' && report && (
              <div className="grid gap-6 md:grid-cols-2">
                <div>
                  <span className="data text-xs uppercase tracking-widest text-muted">Best model</span>
                  <div className="mt-1 font-display text-2xl holo-text">{report.best_model}</div>
                  <dl className="mt-4 space-y-2 data text-sm">
                    <Row k="task" v={report.task} />
                    <Row k="target" v={report.target} />
                    <Row k="job id" v={report.job_id?.slice(0, 8)} />
                  </dl>
                  {report.leakage_flags && report.leakage_flags.length > 0 && (
                    <div className="mt-4 rounded-lg border border-plasma-magenta/40 bg-plasma-magenta/5 p-3">
                      <span className="data text-xs text-plasma-magenta">
                        leakage flagged: {report.leakage_flags.join(', ')}
                      </span>
                    </div>
                  )}
                </div>
                <div>
                  <span className="data text-xs uppercase tracking-widest text-muted">Metrics</span>
                  <div className="mt-3">
                    {report.best_metrics && <MetricChart metrics={report.best_metrics} />}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  )
}

function Row({ k, v }: { k: string; v?: string }) {
  if (!v) return null
  return (
    <div className="flex justify-between border-b border-edge/60 pb-1">
      <dt className="uppercase tracking-widest text-muted">{k}</dt>
      <dd className="text-ink">{v}</dd>
    </div>
  )
}
