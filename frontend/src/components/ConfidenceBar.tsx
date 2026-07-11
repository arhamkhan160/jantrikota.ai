export function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100)
  return (
    <div
      className="h-1.5 w-full overflow-hidden rounded-full bg-edge/50"
      role="meter"
      aria-valuenow={pct}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div
        className="h-full rounded-full transition-[width] duration-700 [background:var(--holo)]"
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}
