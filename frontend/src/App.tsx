import NeuralField from './components/NeuralField'

// Shell placeholder — real hero/dashboard land in later components.
export default function App() {
  return (
    <main className="relative min-h-screen overflow-hidden">
      <NeuralField className="absolute inset-0 h-full w-full" />
      <div className="relative z-10 flex min-h-screen flex-col items-center justify-center gap-6 px-6 text-center">
        <span className="data text-xs tracking-[0.35em] text-muted uppercase">jantrikota.ai</span>
        <h1 className="text-5xl md:text-7xl font-bold leading-[1.05]">
          Describe it. <span className="holo-text">The agent builds the model.</span>
        </h1>
        <p className="max-w-xl text-muted">
          Natural-language AutoML — search datasets, validate with a human in the loop, train, and serve.
        </p>
      </div>
    </main>
  )
}
