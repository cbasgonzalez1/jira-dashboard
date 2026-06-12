import { useQuery } from '@tanstack/react-query'
import { AlertTriangle } from 'lucide-react'
import { getBacklog } from '../api/jiraApi.js'
import { useProject } from '../App.jsx'
import DonutChart from '../components/charts/DonutChart.jsx'
import KPICard from '../components/ui/KPICard.jsx'
import { KPISkeleton, ErrorCard } from '../components/ui/LoadingSpinner.jsx'
import clsx from 'clsx'

function StatsTable({ title, data = {}, colorFn }) {
  const entries = Object.entries(data).sort(([, a], [, b]) => b - a)
  const total = entries.reduce((s, [, v]) => s + v, 0)
  if (!entries.length) return null

  return (
    <div className="card border border-border">
      <p className="card-title">{title}</p>
      <div className="space-y-2">
        {entries.map(([name, count]) => {
          const pct = total > 0 ? Math.round(count / total * 100) : 0
          const color = colorFn?.(name) || 'bg-accent-blue'
          return (
            <div key={name} className="flex items-center gap-3">
              <div className="w-20 text-xs text-text-secondary truncate">{name}</div>
              <div className="flex-1 h-1.5 bg-bg-primary rounded-full overflow-hidden">
                <div className={clsx('h-full rounded-full', color)} style={{ width: `${pct}%` }} />
              </div>
              <div className="text-xs text-text-muted tabular-nums w-8 text-right">{count}</div>
              <div className="text-xs text-text-muted tabular-nums w-8 text-right">{pct}%</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

const TYPE_COLOR = { Story: 'bg-accent-blue', Bug: 'bg-accent-red', Task: 'bg-accent-green', Epic: 'bg-accent-purple', Historia: 'bg-accent-blue', Error: 'bg-accent-red', Tarea: 'bg-accent-green' }
const PRIORITY_COLOR = { Highest: 'bg-accent-red', High: 'bg-accent-yellow', Medium: 'bg-accent-blue', Low: 'bg-text-muted' }
const STATUS_COLOR = { 'To Do': 'bg-bg-primary', 'In Progress': 'bg-accent-blue', 'In Review': 'bg-accent-purple', Done: 'bg-accent-green', Blocked: 'bg-accent-red' }

export default function Backlog() {
  const { project } = useProject()

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['backlog', project],
    queryFn: () => getBacklog(project).then(r => r.data),
    refetchInterval: 60_000,
  })

  if (isError) return <ErrorCard message="Failed to load backlog data." onRetry={refetch} />

  const estimatedPct = data?.total > 0
    ? Math.round((data.total - data.unestimated) / data.total * 100)
    : 0

  return (
    <div className="space-y-6 animate-fade-in">
      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {isLoading ? Array(4).fill(0).map((_, i) => <KPISkeleton key={i} />) : (
          <>
            <KPICard label="Backlog Size"    value={data?.total}        icon={AlertTriangle} color="blue"   subtitle="unplanned issues" />
            <KPICard label="Unestimated"     value={data?.unestimated}  icon={AlertTriangle} color={data?.unestimated > data?.total * 0.3 ? 'red' : 'yellow'} subtitle="no story points" />
            <KPICard label="Estimated"       value={data?.total - (data?.unestimated ?? 0)} icon={AlertTriangle} color="green" subtitle={`${estimatedPct}% have points`} />
            <KPICard label="Types"           value={Object.keys(data?.by_type ?? {}).length} icon={AlertTriangle} color="purple" subtitle="issue categories" />
          </>
        )}
      </div>

      {/* Donut charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {isLoading ? (
          Array(3).fill(0).map((_, i) => (
            <div key={i} className="card border border-border h-64 skeleton" />
          ))
        ) : (
          <>
            <DonutChart title="By Issue Type"    data={data?.by_type     ?? {}} />
            <DonutChart title="By Priority"      data={data?.by_priority ?? {}} />
            <DonutChart title="By Status"        data={data?.by_status   ?? {}} />
          </>
        )}
      </div>

      {/* Bar breakdown tables */}
      {!isLoading && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <StatsTable title="Issue Types"  data={data?.by_type}     colorFn={n => TYPE_COLOR[n]     || 'bg-accent-blue'} />
          <StatsTable title="Priorities"   data={data?.by_priority} colorFn={n => PRIORITY_COLOR[n] || 'bg-accent-blue'} />
          <StatsTable title="Statuses"     data={data?.by_status}   colorFn={n => STATUS_COLOR[n]   || 'bg-accent-blue'} />
        </div>
      )}

      {/* Estimation health */}
      {!isLoading && (
        <div className="card border border-border">
          <p className="card-title">Estimation Health</p>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="flex justify-between text-xs text-text-muted mb-2">
                <span>Estimated ({data?.total - data?.unestimated} issues)</span>
                <span>Unestimated ({data?.unestimated} issues)</span>
              </div>
              <div className="h-4 bg-bg-primary rounded-full overflow-hidden flex">
                <div
                  className="h-full bg-accent-green transition-all"
                  style={{ width: `${estimatedPct}%` }}
                />
                <div
                  className="h-full bg-accent-red/50"
                  style={{ width: `${100 - estimatedPct}%` }}
                />
              </div>
            </div>
            <div className={clsx(
              'text-2xl font-bold tabular-nums',
              estimatedPct >= 80 ? 'text-accent-green' : estimatedPct >= 60 ? 'text-accent-yellow' : 'text-accent-red'
            )}>
              {estimatedPct}%
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
