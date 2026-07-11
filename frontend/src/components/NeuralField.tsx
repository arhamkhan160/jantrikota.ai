import { useEffect, useRef } from 'react'

/**
 * NeuralField — the signature element.
 * A live force-directed neural network on <canvas>: nodes drift, nearby nodes
 * link, energy pulses travel along edges, and the cursor perturbs the field.
 * Used as the hero backdrop and (later) as a live map of the agent pipeline.
 */

const PALETTE = ['#4de5ff', '#9b7cff', '#ff5cf4'] // cyan, violet, magenta

type Node = { x: number; y: number; vx: number; vy: number; c: string; r: number }
type Pulse = { a: number; b: number; t: number; speed: number }

export default function NeuralField({
  className = '',
  density = 0.00012,
  linkDist = 150,
}: {
  className?: string
  density?: number
  linkDist?: number
}) {
  const ref = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = ref.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')!
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    let w = 0, h = 0, dpr = Math.min(window.devicePixelRatio || 1, 2)
    let nodes: Node[] = []
    let pulses: Pulse[] = []
    const mouse = { x: -9999, y: -9999, active: false }

    function build() {
      const rect = canvas!.getBoundingClientRect()
      w = rect.width; h = rect.height
      canvas!.width = w * dpr; canvas!.height = h * dpr
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      const count = Math.max(24, Math.min(90, Math.round(w * h * density)))
      nodes = Array.from({ length: count }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.25,
        vy: (Math.random() - 0.5) * 0.25,
        c: PALETTE[(Math.random() * PALETTE.length) | 0],
        r: 1.2 + Math.random() * 1.8,
      }))
      pulses = []
    }

    function step() {
      ctx.clearRect(0, 0, w, h)

      // edges + links
      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i]
        for (let j = i + 1; j < nodes.length; j++) {
          const b = nodes[j]
          const dx = a.x - b.x, dy = a.y - b.y
          const d2 = dx * dx + dy * dy
          if (d2 < linkDist * linkDist) {
            const d = Math.sqrt(d2)
            let alpha = (1 - d / linkDist) * 0.5
            // brighten links near the cursor
            const mx = (a.x + b.x) / 2 - mouse.x, my = (a.y + b.y) / 2 - mouse.y
            if (mouse.active && mx * mx + my * my < 160 * 160) alpha = Math.min(1, alpha + 0.35)
            ctx.strokeStyle = a.c
            ctx.globalAlpha = alpha
            ctx.lineWidth = 0.6
            ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke()
            // occasionally launch an energy pulse along this edge
            if (!reduced && Math.random() < 0.0006 && pulses.length < 40)
              pulses.push({ a: i, b: j, t: 0, speed: 0.01 + Math.random() * 0.02 })
          }
        }
      }
      ctx.globalAlpha = 1

      // pulses (data flowing through the net)
      pulses = pulses.filter((p) => {
        p.t += p.speed
        if (p.t >= 1) return false
        const a = nodes[p.a], b = nodes[p.b]
        const x = a.x + (b.x - a.x) * p.t, y = a.y + (b.y - a.y) * p.t
        ctx.fillStyle = '#7cffcb'
        ctx.globalAlpha = Math.sin(p.t * Math.PI)
        ctx.beginPath(); ctx.arc(x, y, 2, 0, Math.PI * 2); ctx.fill()
        return true
      })
      ctx.globalAlpha = 1

      // nodes (glowing)
      for (const n of nodes) {
        if (!reduced) {
          // cursor repulsion
          if (mouse.active) {
            const dx = n.x - mouse.x, dy = n.y - mouse.y
            const d2 = dx * dx + dy * dy
            if (d2 < 130 * 130 && d2 > 1) {
              const f = (1 - Math.sqrt(d2) / 130) * 0.6
              n.vx += (dx / Math.sqrt(d2)) * f
              n.vy += (dy / Math.sqrt(d2)) * f
            }
          }
          n.x += n.vx; n.y += n.vy
          n.vx *= 0.98; n.vy *= 0.98
          // gentle drift floor
          n.vx += (Math.random() - 0.5) * 0.01
          n.vy += (Math.random() - 0.5) * 0.01
          if (n.x < 0 || n.x > w) n.vx *= -1
          if (n.y < 0 || n.y > h) n.vy *= -1
          n.x = Math.max(0, Math.min(w, n.x))
          n.y = Math.max(0, Math.min(h, n.y))
        }
        const g = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, n.r * 5)
        g.addColorStop(0, n.c)
        g.addColorStop(1, 'transparent')
        ctx.fillStyle = g
        ctx.globalAlpha = 0.9
        ctx.beginPath(); ctx.arc(n.x, n.y, n.r * 5, 0, Math.PI * 2); ctx.fill()
        ctx.globalAlpha = 1
        ctx.fillStyle = n.c
        ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2); ctx.fill()
      }

      if (!reduced) raf = requestAnimationFrame(step)
    }

    let raf = 0
    const onMove = (e: PointerEvent) => {
      const rect = canvas!.getBoundingClientRect()
      mouse.x = e.clientX - rect.left; mouse.y = e.clientY - rect.top; mouse.active = true
    }
    const onLeave = () => { mouse.active = false; mouse.x = mouse.y = -9999 }
    const onResize = () => { build() }

    build()
    step() // single frame when reduced-motion; animates otherwise
    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerleave', onLeave)
    window.addEventListener('resize', onResize)

    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerleave', onLeave)
      window.removeEventListener('resize', onResize)
    }
  }, [density, linkDist])

  return <canvas ref={ref} className={className} aria-hidden="true" />
}
