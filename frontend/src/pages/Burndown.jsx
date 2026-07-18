import { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Calendar, CheckCircle, Clock, AlertCircle } from 'lucide-react'
import { getBurndown, getSprintBoards, getSprintSprints } from '../api/jiraApi.js'
import { useProject } from '../App.jsx'
import BurndownChart from '../components/charts/BurndownChart.jsx'
import KPICard from '../components/ui/KPICard.jsx'
import Select from '../components/ui/Select.jsx'
import { ChartSkeleton, KPISkeleton, ErrorCard } from '../components/ui/LoadingSpinner.jsx'
import { differenceInDays, parseISO } from 'date-fns'
import clsx from 'clsx'

function ProjectionBadge({ data }) {
  if (!data?.sprint_end || !data?.remaining_h) return null

  const daysLeft = differenceInDays(parseISO(data.sprint_end), new Date())
  const onTrack = daysLeft > 0 && data.remaining_h < data.total_h * 0.5

  return (
    <div className={clsx(
      'card border flex flex-col gap-3',
      onTrack ? 'border-accent-green/30' : 'border-accent-red/30'
    )}>
      <p className="card-title">Proyección</p>
      <div className="flex items-center gap-3">
        {onTrack
          ? <CheckCircle size={24} className="text-accent-green flex-shrink-0" />
          : <AlertCircle size={24} className="text-accent-red flex-shrink-0" />
        }
        <div>
          <p className={clsx('text-sm font-semibold', onTrack ? 'text-accent-green' : 'text-accent-red')}>
            {onTrack ? 'En plazo' : 'En riesgo'}
          </p>
          <p className="text-xs text-text-muted">
            {daysLeft > 0 ? `${daysLeft} días restantes` : 'Sprint finalizado'}
          </p>
        </div>
      </div>
      <div className="text-xs text-text-muted">
        {data.remaining_h}h restantes de {data.total_h}h total
      </div>
    </div>
  )
}

export default function Burndown() {
  const { project } = useProject()
  const [boardId, setBoardId] = useState(null)
  const [sprintId, setSprintId] = useState(null)

  const boardsQ = useQuery({
    queryKey: ['burndown-boards', project],
    queryFn: () => getSprintBoards(project).then(r => r.data),
    enabled: !!project,
  })

  const sprintsQ = useQuery({
    queryKey: ['burndown-sprints', boardId],
    queryFn: () => getSprintSprints(boardId).then(r => r.data),
    enabled: !!boardId,
  })

  // Reset selection when the project changes; default to the first board.
  useEffect(() => { setBoardId(null); setSprintId(null) }, [project])
  useEffect(() => {
    if (!boardId && boardsQ.data?.length) setBoardId(boardsQ.data[0].id)
  }, [boardsQ.data])

  // Default to the active sprint once the board's sprint list loads.
  const boardJustChanged = useRef(true)
  useEffect(() => {
    if (!sprintsQ.data?.length || !boardJustChanged.current) return
    boardJustChanged.current = false
    const active = sprintsQ.data.find(s => s.state === 'active')
    setSprintId(active ? active.id : sprintsQ.data[0].id)
  }, [sprintsQ.data])

  function handleBoardChange(e) {
    setBoardId(Number(e.target.value) || null)
    setSprintId(null)
    boardJustChanged.current = true
  }

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['burndown', project, boardId, sprintId],
    queryFn: () => getBurndown(project, boardId, sprintId).then(r => r.data),
    enabled: !!project,
    refetchInterval: 60_000,
  })

  if (isError) return <ErrorCard message="Error al cargar datos del burndown." onRetry={refetch} />

  const selectors = (
    <div className="card border border-border flex flex-wrap gap-4">
      <Select
        label="Tablero"
        value={boardId ?? ''}
        minW="min-w-56"
        disabled={boardsQ.isLoading}
        onChange={handleBoardChange}
      >
        <option value="">Seleccionar tablero…</option>
        {(boardsQ.data ?? []).map(b => (
          <option key={b.id} value={b.id}>{b.name}</option>
        ))}
      </Select>
      <Select
        label="Sprint"
        value={sprintId ?? ''}
        minW="min-w-64"
        disabled={!boardId || sprintsQ.isLoading}
        onChange={e => setSprintId(Number(e.target.value) || null)}
      >
        <option value="">Seleccionar sprint…</option>
        {(sprintsQ.data ?? []).slice().sort((a, b) => b.id - a.id).map(s => (
          <option key={s.id} value={s.id}>{s.name} — {s.state}</option>
        ))}
      </Select>
    </div>
  )

  if (!isLoading && !data?.sprint) {
    return (
      <div className="space-y-6 animate-fade-in">
        {selectors}
        <div className="card border border-border flex flex-col items-center gap-3 py-16 text-center">
          <span className="text-4xl">🏁</span>
          <h3 className="text-text-primary font-semibold">Sin sprint activo</h3>
          <p className="text-text-muted text-sm">Inicia un sprint en Jira para ver el burndown.</p>
        </div>
      </div>
    )
  }

  const completionPct = data?.total_h > 0
    ? Math.round(data.done_h / data.total_h * 100)
    : 0

  return (
    <div className="space-y-6 animate-fade-in">
      {selectors}

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {isLoading ? Array(4).fill(0).map((_, i) => <KPISkeleton key={i} />) : (
          <>
            <KPICard label="Horas totales"   value={`${data?.total_h}h`} icon={Clock}        color="blue"   subtitle={data?.sprint} />
            <KPICard label="Completadas"     value={`${data?.done_h}h`}  icon={CheckCircle}  color="green"  subtitle={`${completionPct}% completado`} />
            <KPICard label="Restantes"       value={`${data?.remaining_h}h`} icon={AlertCircle}  color={completionPct < 50 ? 'red' : 'yellow'} subtitle={data?.total_sp ? `${data.total_sp} pts (secundario)` : 'horas'} />
            <KPICard label="Fin del sprint"  value={data?.sprint_end}    icon={Calendar}     color="purple" subtitle="fecha objetivo" />
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
                Real
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
            <p className="card-title">Progreso de completitud</p>
            <div className="flex items-end gap-3">
              <span className="text-4xl font-bold text-text-primary tabular-nums">{completionPct}%</span>
              <span className="text-text-muted text-sm mb-1">completado</span>
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
              <span>{data?.done_h}h completadas</span>
              <span>{data?.remaining_h}h restantes</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
