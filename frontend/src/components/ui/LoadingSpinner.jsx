export function Skeleton({ className = '' }) {
  return <div className={`skeleton ${className}`} />
}

export function KPISkeleton() {
  return (
    <div className="card border border-border flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-8 w-8 rounded-lg" />
      </div>
      <Skeleton className="h-8 w-20" />
      <Skeleton className="h-3 w-32" />
    </div>
  )
}

export function ChartSkeleton({ height = 'h-64' }) {
  return (
    <div className={`card border border-border ${height} flex items-center justify-center`}>
      <div className="text-text-muted text-sm animate-pulse">Loading chart data…</div>
    </div>
  )
}

export function ErrorCard({ message, onRetry }) {
  return (
    <div className="card border border-accent-red/30 flex flex-col items-center gap-3 py-8 text-center">
      <span className="text-2xl">⚠️</span>
      <p className="text-sm text-text-secondary">{message || 'Failed to load data'}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn btn-ghost text-xs">
          Try again
        </button>
      )}
    </div>
  )
}

