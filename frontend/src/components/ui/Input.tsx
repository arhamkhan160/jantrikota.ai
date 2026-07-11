import type { InputHTMLAttributes } from 'react'

export function Input({ className = '', ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={
        'w-full rounded-xl border border-edge bg-abyss/70 px-4 py-2.5 text-ink ' +
        'placeholder:text-muted/60 outline-none transition focus:border-plasma-cyan ' +
        `focus:shadow-[0_0_0_3px_color-mix(in_oklab,var(--color-plasma-cyan)_20%,transparent)] ${className}`
      }
      {...props}
    />
  )
}
