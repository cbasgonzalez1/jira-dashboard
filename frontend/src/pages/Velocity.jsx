import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { TrendingUp, TrendingDown, Minus, Zap, Target } from 'lucide-react'
import { getVelocity, getSprintBoards } from '../api/jiraApi.js'
import { useProject } from '../App.jsx'
import VelocityChart from '../components/charts/VelocityChart.jsx'
import KPICard from '../components/ui/KPICard.jsx'
import Select from '../components/ui/Select.jsx'
import { ChartSkeleton, KPISkeleton, ErrorCard } from '../components/ui/LoadingSpinner.jsx'
import { StatusBadge } from '../components/ui/StatusBadge.jsx'
import clsx from 'clsx'

export default function Velocity() {
  const { project } = useProject()
  const [boardId, setBoardId] = useState(null)

  const boardsQ = useQuery({
    queryKey: ['velocity-boards', project],
    queryFn: () => getSprintBoards(project).then(r => r.data),
    enabled: !!project,
  })

  // Reset board selection when the project changes, and default to the
  // first board once its list loads (most projects only have one).
  useEffect(() => { setBoardId(null) }, [project])
  useEffect(() => {
    if (!boardId && boardsQ.data?.length) setBoardId(boardsQ.data[0].id)
  }, [boardsQ.data])

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['velocity', project, boardId],
    queryFn: () => getVelocity(project, boardId).then(r => r.data),
    enabled: !!project,
    refetchInterval: 60_000,
  })

  const sprints = data?.sprints ?? []
  const closed = sprints.filter(s => s.state === 'closed')
  const lastTwo = closed.slice(-2)
  const trend = lastTwo.length === 2
    ? lastTwo[1].completed - lastTwo[0].completed
    : null

  const bestSprint = [...sprints].sort((a, b) => b.completed - a.completed)[0]
  const predictability = closed.length > 0
    ? Math.round(closed.reduce((s, sp) => s + (sp.committed > 0 ? sp.completed / sp.committed : 0), 0) / closed.length * 100)
    : 0

  if (isError) return <ErrorCard message="Error al cargar datos de velocidad." onRetry={refetch} />

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Board selector */}
      <div className="card border border-border">
        <Select
          label="Tablero"
          value={boardId ?? ''}
          minW="min-w-56"
          disabled={boardsQ.isLoading}
          onChange={e => setBoardId(Number(e.target.value) || null)}
        >
          <option value="">Seleccionar tablero…</option>
          {(boardsQ.data ?? []).map(b => (
            <option key={b.id} value={b.id}>{b.name}</option>
          ))}
        </Select>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {isLoading ? Array(4).fill(0).map((_, i) => <KPISkeleton key={i} />) : (
          <>
            <KPICard
              label="Velocidad media"
              value={`${data?.avg_velocity ?? 0}h`}
              icon={Zap}
              color="green"
              subtitle={`últimos 3 sprints cerrados${data?.avg_velocity_sp ? ` · ${data.avg_velocity_sp} pts` : ''}`}
            />
            <KPICard
              label="Mejor sprint"
              value={`${bestSprint?.completed ?? 0}h`}
              icon={Target}
              color="blue"
              subtitle={bestSprint?.name?.replace(/^(SCRUM|CRM|INF)\s/, '') || '—'}
            />
            <KPICard
              label="Tendencia"
              value={trend === null ? '—' : trend > 0 ? `+${trend}` : `${trend}`}
              icon={trend === null ? Minus : trend > 0 ? TrendingUp : TrendingDown}
              color={trend === null ? 'blue' : trend > 0 ? 'green' : 'red'}
              subtitle="vs sprint anterior"
            />
            <KPICard
              label="Predictibilidad"
              value={`${predictability}%`}
              icon={Target}
              color={predictability >= 80 ? 'green' : predictability >= 60 ? 'yellow' : 'red'}
              subtitle="comprometido vs completado"
            />
          </>
        )}
      </div>

      {/* Chart */}
      {isLoading ? <ChartSkeleton height="h-80" /> : (
        <div className="card border border-border">
          <p className="card-title">Velocidad del sprint — {project}</p>
          <VelocityChart sprints={sprints} avgVelocity={data?.avg_velocity} />
        </div>
      )}

      {/* Table */}
      {!isLoading && sprints.length > 0 && (
        <div className="card border border-border">
          <p className="card-title">Detalle de sprints</p>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  {['Sprint', 'Estado', 'Comprometido (h)', 'Completado (h)', 'Completitud'].map(h => (
                    <th key={h} className="text-left py-2 px-3 text-xs font-semibold uppercase tracking-wider text-text-muted">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sprints.map(s => {
                  const pct = s.committed > 0 ? Math.round(s.completed / s.committed * 100) : 0
                  const barColor = pct >= 80 ? 'bg-accent-green' : pct >= 60 ? 'bg-accent-yellow' : 'bg-accent-red'
                  return (
                    <tr key={s.name} className="border-b border-border/50 hover:bg-bg-secondary/50 transition-colors">
                      <td className="py-3 px-3 text-sm font-medium text-text-primary">
                        {s.name.replace(/^(SCRUM|CRM|INF)\s/, '')}
                      </td>
                      <td className="py-3 px-3">
                        <StatusBadge status={s.state === 'closed' ? 'Done' : 'In Progress'} />
                      </td>
                      <td className="py-3 px-3 text-sm tabular-nums text-text-secondary">{s.committed}</td>
                      <td className="py-3 px-3 text-sm tabular-nums text-text-primary font-medium">{s.completed}</td>
                      <td className="py-3 px-3">
                        <div className="flex items-center gap-3">
                          <div className="w-24 h-1.5 bg-bg-primary rounded-full overflow-hidden">
                            <div className={clsx('h-full rounded-full', barColor)} style={{ width: `${Math.min(pct, 100)}%` }} />
                          </div>
                          <span className="text-xs text-text-secondary tabular-nums">{pct}%</span>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
