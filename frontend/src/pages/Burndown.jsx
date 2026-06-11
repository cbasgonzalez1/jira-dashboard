import { useQuery } from '@tanstack/react-query'
import { Calendar, CheckCircle, Clock, AlertCircle } from 'lucide-react'
import { getBurndown } from '../api/jiraApi.js'
import { useProject } from '../App.jsx'
import BurndownChart from '../components/charts/BurndownChart.jsx'
import KPICard from '../components/ui/KPICard.jsx'
import { ChartSkeleton, KPISkeleton, ErrorCard } from '../components/ui/LoadingSpinner.jsx'
import { differenceInDays, parseISO, isAfter } from 'date-fns'
import clsx from 'clsx'

function ProjectionBadge({ data }) {
  if (!data?.sprint_end || !data?.remaining_pts) return null

  const daysLeft = differenceInDays(parseISO(data.sprint_end), new Date())
  const onTrack = daysLeft > 0 && data.remaining_pts < data.total_pts * 0.5

  return (
    <div className={clsx(
      'card border flex flex-col gap-3',
      onTrack ? 'border-accent-green/30' : 'border-accent-red/30'
    )}>
      <p className="card-title">Projection</p>
      <div className="flex items-center gap-3">
        {onTrack
          ? <CheckCircle size={24} className="text-accent-green flex-shrink-0" />
          : <AlertCircle size={24} className="text-accent-red flex-shrink-0" />
        }
        <div>
          <p className={clsx('text-sm font-semibold', onTrack ? 'text-accent-green' : 'text-accent-red')}>
            {onTrack ? 'On Track' : 'At Risk'}
          </p>
          <p className="text-xs text-text-muted">
            {daysLeft > 0 ? `${daysLeft} days remaining` : 'Sprint ended'}
          </p>
        </div>
      </div>
      <div className="text-xs text-text-muted">
        {data.remaining_pts} pts remaining of {data.total_pts} total
      </div>
    </div>
  )
}

export default function Burndown() {
  const { project } = useProject()

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['burndown', project],
    queryFn: () => getBurndown(project).then(r => r.data),
    refetchInterval: 60_000,
  })

  if (isError) return <ErrorCard message="Failed to load burndown data." onRetry={refetch} />

  if (!isLoading && !data?.sprint) {
    return (
      <div className="card border border-border flex flex-col items-center gap-3 py-16 text-center">
        <span className="text-4xl">🏁</span>
        <h3 className="text-text-primary font-semibold">No active sprint</h3>
        <p className="text-text-muted text-sm">Start a sprint in Jira to see the burndown chart.</p>
      </div>
    )
  }

  const completionPct = data?.total_pts > 0
    ? Math.round(data.done_pts / data.total_pts * 100)
    : 0

  return (
    <div className="space-y-6 animate-fade-in">
      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {isLoading ? Array(4).fill(0).map((_, i) => <KPISkeleton key={i} />) : (
          <>
            <KPICard label="Total Points"     value={data?.total_pts}     icon={Clock}        color="blue"   subtitle={data?.sprint} />
            <KPICard label="Done"             value={data?.done_pts}      icon={CheckCircle}  color="green"  subtitle={`${completionPct}% complete`} />
            <KPICard label="Remaining"        value={data?.remaining_pts} icon={AlertCircle}  color={completionPct < 50 ? 'red' : 'yellow'} subtitle="story points" />
            <KPICard label="Sprint Ends"      value={data?.sprint_end}    icon={Calendar}     color="purple" subtitle="target date" />
          </>
        )}
      </div>

      {/* Chart */}
      {isLoading ? <ChartSkeleton height="h-96" /> : (
        <div className="card border border-border">
          <div className="flex items-center justify-between mb-4">
            <p className="card-title mb-0">{data?.sprint}</p>
            <div className="flex items-center gap-4 text-xs text-text-muted">
              <span className="flex items-center gap-1.5">
                <span className="w-6 border-t-2 border-dashed border-text-muted inline-block" />
                Ideal
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-6 border-t-2 border-accent-blue inline-block" />
                Actual
              </span>
            </div>
          </div>
          <BurndownChart days={data?.days} ideal={data?.ideal} actual={data?.actual} />
        </div>
      )}

      {/* Projection + progress */}
      {!isLoading && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <ProjectionBadge data={data} />
          <div className="card border border-border flex flex-col gap-3">
            <p className="card-title">Completion Progress</p>
            <div className="flex items-end gap-3">
              <span className="text-4xl font-bold text-text-primary tabular-nums">{completionPct}%</span>
              <span className="text-text-muted text-sm mb-1">done</span>
            </div>
            <div className="h-2 bg-bg-primary rounded-full overflow-hidden">
              <div
                className={clsx(
                  'h-full rounded-full transition-all',
                  completionPct >= 70 ? 'bg-accent-green' : completionPct >= 40 ? 'bg-accent-yellow' : 'bg-accent-red'
                )}
                style={{ width: `${completionPct}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-text-muted">
              <span>{data?.done_pts} pts done</span>
              <span>{data?.remaining_pts} pts left</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
