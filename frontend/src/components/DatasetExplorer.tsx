import { useState } from 'react'
import { ApiError } from '../lib/api'
import {
  searchDatasets, getDatasetDetail, SOURCE_COLOR,
  type SearchHit, type DatasetDetail,
} from '../lib/datasets'
import { ConfidenceBar } from './ConfidenceBar'
import { Button } from './ui/Button'
import { Input } from './ui/Input'

const ALL_SOURCES = ['openml', 'hf', 'kaggle'] as const

export default function DatasetExplorer({ onUse }: { onUse?: (ref: string) => void }) {
  const [q, setQ] = useState('')
  const [sources, setSources] = useState<string[]>(['openml'])
  const [hits, setHits] = useState<SearchHit[] | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [selected, setSelected] = useState<string | null>(null)
  const [detail, setDetail] = useState<DatasetDetail | null>(null)
  const [detailBusy, setDetailBusy] = useState(false)

  const toggle = (s: string) =>
    setSources((cur) => (cur.includes(s) ? cur.filter((x) => x !== s) : [...cur, s]))

  async function search(e: React.FormEvent) {
    e.preventDefault()
    if (!q.trim()) return
    setBusy(true); setError(null); setHits(null); setDetail(null); setSelected(null)
    try {
      setHits(await searchDatasets(q.trim(), sources.length ? sources : ['openml']))
    } catch (err) {
      setError(authOr(err, 'Search failed. Try again.'))
    } finally {
      setBusy(false)
    }
  }

  async function select(ref: string) {
    setSelected(ref); setDetail(null); setDetailBusy(true); setError(null)
    try {
      setDetail(await getDatasetDetail(ref))
    } catch (err) {
      setError(authOr(err, 'Could not load dataset detail.'))
    } finally {
      setDetailBusy(false)
    }
  }

  return (
    <section id="datasets" className="mx-auto max-w-6xl scroll-mt-24 px-6 py-24">
      <div className="mb-10 text-center">
        <span className="data text-xs uppercase tracking-[0.3em] text-muted">Step 01 — Discover</span>
        <h2 className="mt-3 text-3xl font-semibold sm:text-4xl">
          Search datasets across <span className="holo-text">every source</span>
        </h2>
        <p className="mx-auto mt-3 max-w-lg text-sm text-muted">
          Ranked by relevance. Pick one to see its columns and what each means — no full download.
        </p>
      </div>

      <form onSubmit={search} className="mx-auto flex max-w-2xl flex-col gap-3 sm:flex-row">
        <Input
          placeholder="e.g. house prices, credit risk, iris…"
          value={q} onChange={(e) => setQ(e.target.value)}
        />
        <Button type="submit" variant="primary" disabled={busy} className="shrink-0">
          {busy ? 'Searching…' : 'Search'}
        </Button>
      </form>

      <div className="mx-auto mt-4 flex max-w-2xl flex-wrap items-center gap-2">
        <span className="data text-xs text-muted">sources:</span>
        {ALL_SOURCES.map((s) => {
          const on = sources.includes(s)
          return (
            <button
              key={s}
              onClick={() => toggle(s)}
              className={`data rounded-full border px-3 py-1 text-xs transition ${
                on ? `border-transparent holo-border ${SOURCE_COLOR[s]}` : 'border-edge text-muted hover:text-ink'
              }`}
            >
              {s}
            </button>
          )
        })}
      </div>

      {error && <p className="mt-6 text-center data text-sm text-plasma-magenta">{error}</p>}

      <div className="mt-10 grid gap-6 lg:grid-cols-[1.1fr_1fr]">
        {/* results */}
        <div className="space-y-3">
          {busy && <SkeletonList />}
          {hits && hits.length === 0 && (
            <p className="data text-sm text-muted">No datasets matched. Try another query or source.</p>
          )}
          {hits?.map((h) => (
            <button
              key={h.ref}
              onClick={() => select(h.ref)}
              className={`holo-border block w-full rounded-2xl p-4 text-left transition duration-200 hover:-translate-y-0.5 hover:shadow-[0_10px_40px_-15px_var(--color-plasma-violet)] ${
                selected === h.ref ? 'ring-1 ring-plasma-cyan' : ''
              }`}
            >
              <div className="flex items-center justify-between">
                <span className={`data text-[11px] uppercase tracking-widest ${SOURCE_COLOR[h.source] ?? 'text-muted'}`}>
                  {h.source}
                </span>
                <span className="data text-xs text-muted">{(h.confidence * 100).toFixed(0)}% match</span>
              </div>
              <div className="mt-2 truncate font-display text-lg text-ink">{h.name}</div>
              <div className="mt-3"><ConfidenceBar value={h.confidence} /></div>
              <div className="mt-3 data text-xs text-muted">
                {h.rows ? `${h.rows.toLocaleString()} rows` : '— rows'} ·{' '}
                {h.features ? `${h.features} features` : '— features'}
              </div>
            </button>
          ))}
          {!hits && !busy && (
            <p className="data text-sm text-muted/70">Run a search to see ranked datasets here.</p>
          )}
        </div>

        {/* detail */}
        <div className="glass sticky top-24 h-fit rounded-2xl p-6">
          {!selected && <p className="data text-sm text-muted/70">Select a dataset to inspect its columns.</p>}
          {detailBusy && <p className="data text-sm text-muted">Loading detail…</p>}
          {detail && (
            <div>
              <div className="flex items-center justify-between">
                <span className={`data text-[11px] uppercase tracking-widest ${SOURCE_COLOR[detail.source] ?? 'text-muted'}`}>
                  {detail.source}
                </span>
                {detail.target && (
                  <span className="data rounded-full bg-mint/10 px-2 py-0.5 text-[11px] text-mint">
                    target: {detail.target}
                  </span>
                )}
              </div>
              <h3 className="mt-2 font-display text-xl">{detail.name}</h3>
              {detail.description && (
                <p className="mt-2 line-clamp-4 text-sm text-muted">{detail.description}</p>
              )}

              <div className="mt-5 space-y-2">
                <span className="data text-xs uppercase tracking-widest text-muted">
                  {detail.columns.length} columns
                </span>
                <div className="max-h-64 space-y-2 overflow-y-auto pr-1">
                  {detail.columns.map((c) => (
                    <div key={c.name} className="rounded-lg border border-edge bg-abyss/50 p-2.5">
                      <div className="flex items-center justify-between gap-2">
                        <span className="data truncate text-sm text-ink">{c.name}</span>
                        {c.type && <span className="data shrink-0 text-[11px] text-plasma-cyan">{c.type}</span>}
                      </div>
                      {c.explanation && <p className="mt-1 text-xs text-muted">{c.explanation}</p>}
                    </div>
                  ))}
                </div>
              </div>

              <Button variant="primary" className="mt-6 w-full" onClick={() => onUse?.(detail.ref)}>
                Use this dataset →
              </Button>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}

function authOr(err: unknown, fallback: string) {
  if (err instanceof ApiError && err.status === 401) return 'Sign in to search datasets.'
  return err instanceof ApiError ? err.message : fallback
}

function SkeletonList() {
  return (
    <>
      {[0, 1, 2].map((i) => (
        <div key={i} className="holo-border animate-pulse rounded-2xl p-4">
          <div className="h-3 w-24 rounded bg-edge/60" />
          <div className="mt-3 h-5 w-2/3 rounded bg-edge/60" />
          <div className="mt-3 h-1.5 w-full rounded bg-edge/40" />
        </div>
      ))}
    </>
  )
}
