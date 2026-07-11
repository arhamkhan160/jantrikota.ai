// Holographic bar chart for a trained model's metrics.
// 0–1 metrics (accuracy/f1/roc_auc) fill by their value; open-scale metrics
// (rmse/mae) fill relative to the largest value in the set.

function fmt(v: number) {
  return Number.isInteger(v) ? String(v) : v.toFixed(4)
}

export function MetricChart({ metrics }: { metrics: Record<string, number> }) {
  const entries = Object.entries(metrics)
  if (entries.length === 0) return null
  const openMax = Math.max(...entries.map(([, v]) => Math.abs(v)), 1e-9)

  return (
    <div className="space-y-4">
      {entries.map(([k, v]) => {
        const bounded = v >= 0 && v <= 1
        const width = Math.min(100, (bounded ? v : Math.abs(v) / openMax) * 100)
        return (
          <div key={k} className="group">
            <div className="flex items-baseline justify-between">
              <span className="data text-xs uppercase tracking-widest text-muted">{k}</span>
              <span className="data text-sm text-ink">{fmt(v)}</span>
            </div>
            <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-edge/50">
              <div
                className="h-full rounded-full transition-[width] duration-1000 ease-out [background:var(--holo)] group-hover:brightness-125"
                style={{ width: `${width}%` }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}
