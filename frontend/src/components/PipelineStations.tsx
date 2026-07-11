import { Fragment } from 'react'

const STAGES = ['Search', 'Select', 'Fetch', 'Target', 'Train', 'Report']

/** Live map of the agent run. `active` = index of the current stage. */
export function PipelineStations({ active, error }: { active: number; error?: boolean }) {
  return (
    <div className="flex items-center">
      {STAGES.map((s, i) => {
        const state = error && i === active ? 'error' : i < active ? 'done' : i === active ? 'active' : 'todo'
        return (
          <Fragment key={s}>
            <div className="flex flex-1 flex-col items-center gap-2">
              <span className="relative flex h-4 w-4 items-center justify-center">
                {state === 'active' && (
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-plasma-cyan opacity-70" />
                )}
                <span
                  className={
                    'relative h-3 w-3 rounded-full transition ' +
                    (state === 'done'
                      ? 'bg-mint shadow-[0_0_12px_var(--color-mint)]'
                      : state === 'active'
                        ? '[background:var(--holo)] shadow-[0_0_14px_var(--color-plasma-violet)]'
                        : state === 'error'
                          ? 'bg-plasma-magenta shadow-[0_0_12px_var(--color-plasma-magenta)]'
                          : 'bg-edge')
                  }
                />
              </span>
              <span
                className={
                  'data text-[10px] uppercase tracking-widest ' +
                  (state === 'todo' ? 'text-muted/50' : 'text-ink')
                }
              >
                {s}
              </span>
            </div>
            {i < STAGES.length - 1 && (
              <div className="mb-5 h-px flex-1">
                <div
                  className={'h-px w-full transition-all duration-500 ' + (i < active ? '[background:var(--holo)]' : 'bg-edge')}
                />
              </div>
            )}
          </Fragment>
        )
      })}
    </div>
  )
}
