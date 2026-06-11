import clsx from 'clsx'

const STATUS_COLORS = {
  'done':        'bg-accent-green/15 text-accent-green border-accent-green/30',
  'in progress': 'bg-accent-blue/15 text-accent-blue border-accent-blue/30',
  'in review':   'bg-accent-purple/15 text-accent-purple border-accent-purple/30',
  'blocked':     'bg-accent-red/15 text-accent-red border-accent-red/30',
  'to do':       'bg-bg-primary text-text-secondary border-border',
}

const PRIORITY_COLORS = {
  highest: 'bg-accent-red/15 text-accent-red border-accent-red/30',
  high:    'bg-accent-yellow/15 text-accent-yellow border-accent-yellow/30',
  medium:  'bg-accent-blue/15 text-accent-blue border-accent-blue/30',
  low:     'bg-text-muted/15 text-text-muted border-border',
  lowest:  'bg-text-muted/10 text-text-muted border-border',
}

export function StatusBadge({ status }) {
  const key = status?.toLowerCase() || ''
  const color = STATUS_COLORS[key] || 'bg-bg-primary text-text-secondary border-border'
  return (
    <span className={clsx('inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border', color)}>
      {status}
    </span>
  )
}

export function PriorityBadge({ priority }) {
  const key = priority?.toLowerCase() || ''
  const color = PRIORITY_COLORS[key] || 'bg-bg-primary text-text-secondary border-border'
  return (
    <span className={clsx('inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border', color)}>
      {priority}
    </span>
  )
}

export function TypeBadge({ type }) {
  const colors = {
    epic:    'text-accent-purple',
    story:   'text-accent-blue',
    bug:     'text-accent-red',
    task:    'text-accent-green',
    historia:'text-accent-blue',
    error:   'text-accent-red',
    tarea:   'text-accent-green',
  }
  const icons = {
    epic: '⬡', story: '◈', bug: '⬤', task: '◻',
    historia: '◈', error: '⬤', tarea: '◻',
  }
  const key = type?.toLowerCase() || ''
  const color = colors[key] || 'text-text-secondary'
  const icon = icons[key] || '·'
  return (
    <span className={clsx('font-mono text-xs', color)} title={type}>
      {icon} {type}
    </span>
  )
}
