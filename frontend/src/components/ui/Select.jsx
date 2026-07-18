import { ChevronDown } from 'lucide-react'
import clsx from 'clsx'

export default function Select({ label, value, onChange, disabled, children, minW = 'min-w-48' }) {
  return (
    <div className={clsx('flex flex-col gap-1.5', minW)}>
      <label className="text-xs font-semibold text-text-muted uppercase tracking-wider">{label}</label>
      <div className="relative">
        <select
          className={clsx(
            'w-full appearance-none bg-bg-card border border-border text-text-primary',
            'rounded-lg px-3 py-2 pr-8 text-sm focus:outline-none focus:border-accent-blue',
            'cursor-pointer transition-colors',
            disabled && 'opacity-40 cursor-not-allowed',
          )}
          value={value ?? ''}
          onChange={onChange}
          disabled={disabled}
        >
          {children}
        </select>
        <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none" />
      </div>
    </div>
  )
}
