import type { ButtonHTMLAttributes } from 'react'

type Variant = 'primary' | 'ghost' | 'subtle'

const styles: Record<Variant, string> = {
  primary:
    'text-void font-semibold [background:var(--holo)] hover:brightness-110 ' +
    'shadow-[0_0_36px_-10px_var(--color-plasma-violet)]',
  ghost: 'holo-border text-ink hover:text-white',
  subtle: 'glass text-ink hover:border-plasma-cyan',
}

export function Button({
  variant = 'primary',
  className = '',
  ...props
}: { variant?: Variant } & ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={
        'inline-flex items-center justify-center gap-2 rounded-full px-5 py-2.5 text-sm ' +
        'font-medium transition duration-200 active:scale-[0.98] ' +
        'disabled:opacity-50 disabled:pointer-events-none ' +
        `${styles[variant]} ${className}`
      }
      {...props}
    />
  )
}
