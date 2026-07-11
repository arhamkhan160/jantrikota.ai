// Shell placeholder — real hero/dashboard land in later components.
export default function App() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-6 px-6 text-center">
      <span className="data text-xs tracking-[0.35em] text-muted uppercase">jantrikota.ai</span>
      <h1 className="text-5xl md:text-7xl font-bold leading-[1.05]">
        Describe it. <span className="holo-text">The agent builds the model.</span>
      </h1>
      <p className="max-w-xl text-muted">
        Natural-language AutoML — search datasets, validate with a human in the loop, train, and serve.
      </p>
      <div className="flex gap-4 data text-sm">
        <span className="holo-border rounded-full px-4 py-2">cyan</span>
        <span className="holo-border rounded-full px-4 py-2 text-mint">mint</span>
        <span className="glass rounded-full px-4 py-2">glass</span>
      </div>
    </main>
  )
}
