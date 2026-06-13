import clsx from 'clsx'

const COLOR_MAP = {
  blue:   { text: 'text-accent-blue',   bg: 'bg-accent-blue/10',   border: 'border-accent-blue/20' },
  green:  { text: 'text-accent-green',  bg: 'bg-accent-green/10',  border: 'border-accent-green/20' },
  yellow: { text: 'text-accent-yellow', bg: 'bg-accent-yellow/10', border: 'border-accent-yellow/20' },
  red:    { text: 'text-accent-red',    bg: 'bg-accent-red/10',    border: 'border-accent-red/20' },
  purple: { text: 'text-accent-purple', bg: 'bg-accent-purple/10', border: 'border-accent-purple/20' },
}

export default function KPICard({ label, value, icon: Icon, color = 'blue', subtitle, note }) {
  const c = COLOR_MAP[color] || COLOR_MAP.blue

  return (
    <div className={clsx('card border', c.border, 'flex flex-col gap-3')}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-widest text-text-secondary">{label}</span>
        {Icon && (
          <div className={clsx('w-8 h-8 rounded-lg flex items-center justify-center', c.bg)}>
            <Icon size={16} className={c.text} />
          </div>
        )}
      </div>
      <div>
        <div className={clsx('text-3xl font-bold tabular-nums', c.text)}>
          {typeof value === 'number' ? value.toLocaleString() : value ?? '—'}
        </div>
        {subtitle && <p className="text-xs text-text-muted mt-1">{subtitle}</p>}
        {note && (
          <p className="text-xs mt-2 text-text-muted italic border-t border-border/40 pt-1.5">
            {note}
          </p>
        )}
      </div>
    </div>
  )
}
