import { useState, useMemo, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell,
} from 'recharts'
import {
  Clock, Timer, Users, TrendingUp, CheckCircle, AlertTriangle,
  Zap, BarChart2, User, ChevronDown,
} from 'lucide-react'
import clsx from 'clsx'
import { getSprintBoards, getSprintSprints, getSprintData } from '../api/jiraApi.js'
import KPICard from '../components/ui/KPICard.jsx'
import { ChartSkeleton, ErrorCard } from '../components/ui/LoadingSpinner.jsx'

// ── Constants ──────────────────────────────────────────────────────────────────
const CHART_STYLE = {
  bg: '#1e2130',
  border: '#2a2d3e',
  tick: '#94a3b8',
  grid: '#2a2d3e',
}

const STATUS_COLORS = {
  Backlog:      '#3b82f6',
  'En Progreso': '#f59e0b',
  Validación:   '#8b5cf6',
  Done:         '#10b981',
}

const tooltipStyle = {
  contentStyle: { background: CHART_STYLE.bg, border: `1px solid ${CHART_STYLE.border}`, borderRadius: 8 },
  labelStyle: { color: '#e2e8f0', fontWeight: 600 },
  itemStyle: { color: '#94a3b8' },
}

// ── Demo / preview data shown before any sprint is selected ───────────────────
const DEMO_DATA = {
  kpis: {
    days_remaining: 6, days_elapsed: 8, days_total: 14,
    work_remaining_h: 134, work_remaining_pct: 42,
    capacity_remaining_h: 230, team_size: 5,
    deviation_pct: 18, achievable: true, achievable_delta_h: 96,
    overcost_h: 11, velocity_today_sp: 4.6, done_sp: 37,
    time_logged_per_day_h: 6.2, remaining_per_person_h: 26.8,
    total_issues: 52, done_issues: 19,
  },
  sprint: { name: 'Sprint 4 - Ejemplo', state: 'active', start_date: '2026-06-04', end_date: '2026-06-18' },
  by_person: [
    { account_id: 'u1', name: 'Ana García',      todo: 8,  in_progress: 18, validation: 6,  done: 32, todo_count: 2, in_progress_count: 4, validation_count: 2, done_count: 7,  remaining_h: 32, velocity_today: 4.1, n_projects: 3 },
    { account_id: 'u2', name: 'Carlos López',    todo: 12, in_progress: 10, validation: 0,  done: 20, todo_count: 3, in_progress_count: 3, validation_count: 0, done_count: 4,  remaining_h: 22, velocity_today: 2.5, n_projects: 2 },
    { account_id: 'u3', name: 'Marta Ruiz',      todo: 0,  in_progress: 14, validation: 4,  done: 40, todo_count: 0, in_progress_count: 3, validation_count: 1, done_count: 9,  remaining_h: 18, velocity_today: 5.6, n_projects: 2 },
    { account_id: 'u4', name: 'David Sánchez',   todo: 16, in_progress: 6,  validation: 2,  done: 16, todo_count: 4, in_progress_count: 2, validation_count: 1, done_count: 4,  remaining_h: 24, velocity_today: 2.0, n_projects: 1 },
    { account_id: 'u5', name: 'Lucía Fernández', todo: 4,  in_progress: 8,  validation: 10, done: 24, todo_count: 1, in_progress_count: 2, validation_count: 3, done_count: 5,  remaining_h: 22, velocity_today: 3.1, n_projects: 3 },
  ],
  by_project: [
    { key: 'SCRUM', name: 'MDA Portal',         todo: 14, in_progress: 22, validation: 8,  done: 48, todo_count: 4, in_progress_count: 6, validation_count: 2, done_count: 11, remaining_h: 44, deviation_pct: 22,  velocity_today: 6.2, mandatory_incomplete: 2, completion_pct: 48 },
    { key: 'CRM',   name: 'CRM & Admissions',   todo: 18, in_progress: 14, validation: 8,  done: 36, todo_count: 5, in_progress_count: 4, validation_count: 2, done_count: 8,  remaining_h: 40, deviation_pct: -8,  velocity_today: 3.4, mandatory_incomplete: 0, completion_pct: 42 },
    { key: 'INF',   name: 'Infrastructure',     todo: 8,  in_progress: 20, validation: 6,  done: 28, todo_count: 2, in_progress_count: 4, validation_count: 2, done_count: 6,  remaining_h: 34, deviation_pct: 5,   velocity_today: 3.2, mandatory_incomplete: 1, completion_pct: 38 },
    { key: 'SEC',   name: 'Security & Compliance', todo: 0, in_progress: 0, validation: 0, done: 20, todo_count: 0, in_progress_count: 0, validation_count: 0, done_count: 4,  remaining_h: 0,  deviation_pct: -12, velocity_today: 2.5, mandatory_incomplete: 0, completion_pct: 100 },
  ],
  deviations: [
    { key: 'SCRUM-42', summary: 'Implementar autenticación SSO',          original_h: 8,  spent_h: 19, deviation_pct: 137.5 },
    { key: 'CRM-31',   summary: 'Migración de datos legacy a PostgreSQL',  original_h: 16, spent_h: 26, deviation_pct: 62.5 },
    { key: 'INF-14',   summary: 'Configurar Kubernetes HPA en producción', original_h: 5,  spent_h: 8,  deviation_pct: 60.0 },
    { key: 'SCRUM-58', summary: 'Dashboard de métricas de rendimiento',    original_h: 10, spent_h: 15, deviation_pct: 50.0 },
  ],
}

// ── Empty state for charts ─────────────────────────────────────────────────────
function EmptyChart({ message, height = 260 }) {
  return (
    <div
      className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border/50 bg-bg-primary/20"
      style={{ height }}
    >
      <BarChart2 size={32} className="text-text-muted opacity-25" />
      <p className="text-xs text-text-muted text-center max-w-xs px-4 leading-relaxed">{message}</p>
    </div>
  )
}

// ── Sub-components ─────────────────────────────────────────────────────────────
function Select({ label, value, onChange, disabled, children, minW = 'min-w-48' }) {
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

function SprintBadge({ state }) {
  const colors = {
    active: 'bg-accent-green/10 text-accent-green border-accent-green/20',
    closed: 'bg-bg-primary text-text-muted border-border',
    future: 'bg-accent-blue/10 text-accent-blue border-accent-blue/20',
  }
  return (
    <span className={clsx('text-xs px-2 py-0.5 rounded border', colors[state] || colors.closed)}>
      {state}
    </span>
  )
}

function SectionTitle({ children }) {
  return (
    <h2 className="text-xs font-semibold uppercase tracking-widest text-text-secondary mb-4 flex items-center gap-2">
      <span className="w-1 h-4 rounded-full bg-accent-blue inline-block" />
      {children}
    </h2>
  )
}

function DeviationSign({ v }) {
  if (v === 0) return <span className="text-text-muted">0%</span>
  return (
    <span className={v > 0 ? 'text-accent-red' : 'text-accent-green'}>
      {v > 0 ? '+' : ''}{v}%
    </span>
  )
}

// ── Chart tooltips ─────────────────────────────────────────────────────────────
function HoursTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const total = payload.reduce((s, p) => s + (p.value || 0), 0)
  return (
    <div className="rounded-lg border border-border bg-bg-card p-3 text-xs space-y-1 shadow-xl">
      <p className="font-semibold text-text-primary mb-1">{label}</p>
      {payload.map(p => (
        <div key={p.name} className="flex items-center gap-2 justify-between">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full" style={{ background: p.fill }} />
            <span className="text-text-secondary">{p.name}</span>
          </span>
          <span className="tabular-nums text-text-primary font-medium">{p.value}h</span>
        </div>
      ))}
      <div className="border-t border-border pt-1 flex justify-between font-semibold">
        <span className="text-text-muted">Total</span>
        <span className="text-text-primary">{total.toFixed(1)}h</span>
      </div>
    </div>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────────
export default function SprintDashboard() {
  const [projectKey, setProjectKey] = useState(null)
  const [boardId, setBoardId] = useState(null)
  const [sprintId, setSprintId] = useState(null)

  // ── Queries ────────────────────────────────────────────────────────────
  const boardsQ = useQuery({
    queryKey: ['sd-boards'],
    queryFn: () => getSprintBoards().then(r => r.data),
  })

  // ── Cascading filter derived values ────────────────────────────────────
  const allBoards = boardsQ.data ?? []

  const uniqueProjects = useMemo(() => {
    const seen = new Map()
    for (const b of allBoards) {
      if (b.project_key && !seen.has(b.project_key)) {
        seen.set(b.project_key, b.project_name || b.project_key)
      }
    }
    return [...seen.entries()].map(([key, name]) => ({ key, name }))
  }, [allBoards])

  // Boards available after project filter
  const filteredBoards = useMemo(
    () => projectKey ? allBoards.filter(b => b.project_key === projectKey) : allBoards,
    [allBoards, projectKey],
  )

  // ── Track board changes to trigger sprint auto-select ─────────────────
  const boardJustChanged = useRef(false)

  // Auto-select the active sprint when sprints load after a board change
  useEffect(() => {
    if (!sprintsQ.data?.length || !boardJustChanged.current) return
    boardJustChanged.current = false
    const active = sprintsQ.data.find(s => s.state === 'active')
    if (active) setSprintId(active.id)
  }, [sprintsQ.data])

  // ── Bidirectional handlers ─────────────────────────────────────────────

  function handleProjectChange(e) {
    const key = e.target.value || null
    setProjectKey(key)
    setSprintId(null)
    boardJustChanged.current = false
    const boards = key ? allBoards.filter(b => b.project_key === key) : allBoards
    const currentBoardValid = !key || boards.some(b => b.id === boardId)
    if (!currentBoardValid) {
      setBoardId(boards.length === 1 ? boards[0].id : null)
    } else if (key && boards.length === 1 && boardId == null) {
      setBoardId(boards[0].id)
    }
  }

  function handleBoardChange(e) {
    const id = Number(e.target.value) || null
    setBoardId(id)
    setSprintId(null)
    boardJustChanged.current = true
    if (id) {
      const board = allBoards.find(b => b.id === id)
      if (board?.project_key) setProjectKey(board.project_key)
    }
  }

  const sprintsQ = useQuery({
    queryKey: ['sd-sprints', boardId],
    queryFn: () => getSprintSprints(boardId).then(r => r.data),
    enabled: !!boardId,
  })

  const dataQ = useQuery({
    queryKey: ['sd-data', boardId, sprintId],
    queryFn: () => getSprintData(boardId, sprintId).then(r => r.data),
    enabled: !!(boardId && sprintId),
    staleTime: 60_000,
  })

  // ── Derived data ───────────────────────────────────────────────────────
  const data = dataQ.data

  // When no sprint is selected yet, fall back to demo data so the UI is populated
  const isDemo = !data && !dataQ.isFetching && !dataQ.isError
  const displayData = data ?? (isDemo ? DEMO_DATA : null)

  const kpis = displayData?.kpis ?? {}
  const sprint = displayData?.sprint ?? {}

  const isFuture = !isDemo && !!data && sprint.state === 'future'
  const isEmpty = !isDemo && !!data && (data.kpis?.total_issues ?? 0) === 0 && sprint.state !== 'future'
  const kpiNote = isFuture ? 'Sprint futuro — sin datos aún'
    : isEmpty ? 'Sin issues registradas'
    : null

  const emptyChartMsg = isFuture
    ? 'Este sprint aún no ha comenzado — los datos aparecerán cuando empiece'
    : 'No hay issues en este sprint — añade issues para ver el análisis'

  const allByPerson = (displayData?.by_person ?? []).filter(p => p.account_id !== '_unassigned')
  const allByProject = displayData?.by_project ?? []
  const deviations = displayData?.deviations ?? []
  const byProject = allByProject

  // ── Chart data ─────────────────────────────────────────────────────────
  const personChartData = allByPerson.map(p => ({
    name: p.name.split(' ')[0],
    fullName: p.name,
    Backlog: p.todo,
    'En Progreso': p.in_progress,
    Validación: p.validation,
    Done: p.done,
  }))

  const projectChartData = byProject.map(p => ({
    name: p.key,
    Backlog: p.todo,
    'En Progreso': p.in_progress,
    Validación: p.validation,
    Done: p.done,
  }))

  const completionChartData = byProject.map(p => ({
    name: p.key,
    pct: p.completion_pct,
  }))

  // ── KPI helpers ────────────────────────────────────────────────────────
  const devColor = Math.abs(kpis.deviation_pct) < 10 ? 'green'
    : kpis.deviation_pct > 0 ? 'red' : 'yellow'

  const sprintBarH = Math.max(allByPerson.length * 48, 180)

  // ── Render ─────────────────────────────────────────────────────────────
  return (
    <div className="space-y-8 animate-fade-in">

      {/* ── SECTION 1: Selectors ─────────────────────────────────────────── */}
      <section className="card border border-border">
        <SectionTitle>Filtros</SectionTitle>
        <div className="flex flex-wrap gap-4 items-end">

          {/* 1 — Proyecto */}
          <Select
            label="Proyecto"
            value={projectKey ?? ''}
            minW="min-w-52"
            onChange={handleProjectChange}
          >
            <option value="">Seleccionar proyecto…</option>
            {uniqueProjects.map(p => (
              <option key={p.key} value={p.key}>{p.name} ({p.key})</option>
            ))}
          </Select>

          {/* 2 — Board: filtrado por proyecto seleccionado */}
          <Select
            label="Board"
            value={boardId ?? ''}
            minW="min-w-56"
            onChange={handleBoardChange}
          >
            <option value="">Seleccionar board…</option>
            {filteredBoards.map(b => (
              <option key={b.id} value={b.id}>{b.name} ({b.type})</option>
            ))}
          </Select>

          {/* 3 — Sprint: filtrado por board seleccionado */}
          <Select
            label="Sprint"
            value={sprintId ?? ''}
            minW="min-w-72"
            disabled={!boardId || sprintsQ.isLoading}
            onChange={e => setSprintId(Number(e.target.value) || null)}
          >
            <option value="">Seleccionar sprint…</option>
            {(sprintsQ.data ?? [])
              .slice()
              .sort((a, b) => b.id - a.id)
              .map(s => (
                <option key={s.id} value={s.id}>
                  {s.name} — {s.state}
                </option>
              ))}
          </Select>

          {sprint.name && (
            <div className="flex flex-col gap-1.5 justify-end pb-0.5">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-text-primary">{sprint.name}</span>
                <SprintBadge state={sprint.state} />
              </div>
              {sprint.start_date && (
                <p className="text-xs text-text-muted">
                  {sprint.start_date?.slice(0, 10)} → {sprint.end_date?.slice(0, 10)}
                </p>
              )}
            </div>
          )}
        </div>
      </section>

      {/* Loading */}
      {dataQ.isFetching && (
        <div className="space-y-4">
          <ChartSkeleton height="h-32" />
          <ChartSkeleton height="h-64" />
        </div>
      )}

      {/* Error */}
      {dataQ.isError && (
        <ErrorCard message="Error cargando datos del sprint." onRetry={dataQ.refetch} />
      )}

      {displayData && !dataQ.isFetching && (
        <>
          {/* Demo banner */}
          {isDemo && (
            <div className="rounded-lg border border-accent-yellow/30 bg-accent-yellow/5 flex items-center gap-3 px-4 py-3 text-xs text-accent-yellow">
              <AlertTriangle size={14} className="flex-shrink-0" />
              <span>Vista previa con datos de ejemplo — selecciona un board y sprint para ver datos reales</span>
            </div>
          )}

          {/* ── SECTION 2: KPIs ────────────────────────────────────────────── */}
          <section>
            <SectionTitle>Métricas del sprint</SectionTitle>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">

              <KPICard
                label="Días restantes"
                value={kpis.days_remaining}
                icon={Clock}
                color="blue"
                subtitle={`${kpis.days_elapsed} transcurridos de ${kpis.days_total}`}
                note={kpiNote}
              />

              <KPICard
                label="Trabajo restante"
                value={`${kpis.work_remaining_h}h`}
                icon={Timer}
                color="yellow"
                subtitle={`${kpis.work_remaining_pct}% del total estimado`}
                note={kpiNote}
              />

              <KPICard
                label="Capacidad restante"
                value={`${kpis.capacity_remaining_h}h`}
                icon={Users}
                color="green"
                subtitle={`${kpis.team_size} personas × 8h/d × ${kpis.days_remaining}d × 80%`}
                note={kpiNote}
              />

              <KPICard
                label="Desviación vs inicio"
                value={`${kpis.deviation_pct > 0 ? '+' : ''}${kpis.deviation_pct}%`}
                icon={TrendingUp}
                color={devColor}
                subtitle="vs estimación original del sprint"
                note={kpiNote}
              />

              <KPICard
                label={kpis.achievable ? 'Alcanzable ✓' : 'No alcanzable ✗'}
                value={`${kpis.achievable_delta_h > 0 ? '+' : ''}${kpis.achievable_delta_h}h`}
                icon={CheckCircle}
                color={kpis.achievable ? 'green' : 'red'}
                subtitle="capacidad restante − trabajo restante"
                note={kpiNote}
              />

              <KPICard
                label="Sobrecoste total"
                value={`${kpis.overcost_h}h`}
                icon={AlertTriangle}
                color={kpis.overcost_h > 0 ? 'red' : 'green'}
                subtitle="exceso en issues completadas"
                note={kpiNote}
              />

              <KPICard
                label="Velocidad hoy"
                value={`${kpis.velocity_today_sp} SP/d`}
                icon={Zap}
                color="purple"
                subtitle={`${kpis.done_sp} SP completados en ${kpis.days_elapsed}d`}
                note={kpiNote}
              />

              <KPICard
                label="Tiempo registrado"
                value={`${kpis.time_logged_per_day_h}h/d`}
                icon={BarChart2}
                color="blue"
                subtitle="promedio registrado por día"
                note={kpiNote}
              />

              <KPICard
                label="Restante por persona"
                value={`${kpis.remaining_per_person_h}h`}
                icon={User}
                color="yellow"
                subtitle={`distribuido entre ${kpis.team_size} personas`}
                note={kpiNote}
              />

            </div>
          </section>

          {/* ── SECTION 3: Charts ──────────────────────────────────────────── */}
          <section>
            <SectionTitle>Gráficas</SectionTitle>
            <div className="space-y-4">

              {/* Chart 1: Horizontal stacked — work per person */}
              <div className="card border border-border">
                <p className="card-title">Trabajo por persona (horas)</p>
                {personChartData.length === 0 ? (
                  <EmptyChart message={emptyChartMsg} height={sprintBarH} />
                ) : (
                  <ResponsiveContainer width="100%" height={sprintBarH}>
                    <BarChart
                      data={personChartData}
                      layout="vertical"
                      margin={{ top: 4, right: 24, bottom: 4, left: 100 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke={CHART_STYLE.grid} horizontal={false} />
                      <XAxis
                        type="number"
                        tick={{ fill: CHART_STYLE.tick, fontSize: 11 }}
                        axisLine={{ stroke: CHART_STYLE.border }}
                        tickLine={false}
                        unit="h"
                      />
                      <YAxis
                        type="category"
                        dataKey="name"
                        tick={{ fill: CHART_STYLE.tick, fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                        width={96}
                      />
                      <Tooltip content={<HoursTooltip />} />
                      <Legend
                        wrapperStyle={{ fontSize: 11, color: CHART_STYLE.tick, paddingTop: 8 }}
                      />
                      <Bar dataKey="Backlog"       stackId="a" fill={STATUS_COLORS.Backlog} />
                      <Bar dataKey="En Progreso"   stackId="a" fill={STATUS_COLORS['En Progreso']} />
                      <Bar dataKey="Validación"    stackId="a" fill={STATUS_COLORS.Validación} />
                      <Bar dataKey="Done"          stackId="a" fill={STATUS_COLORS.Done} radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>

              {/* Charts 2 & 3 side by side */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

                {/* Chart 2: Vertical stacked — work per project */}
                <div className="card border border-border">
                  <p className="card-title">Trabajo restante por proyecto (horas)</p>
                  {projectChartData.length === 0 ? (
                    <EmptyChart message={emptyChartMsg} />
                  ) : (
                    <ResponsiveContainer width="100%" height={260}>
                      <BarChart data={projectChartData} margin={{ top: 4, right: 12, bottom: 4, left: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke={CHART_STYLE.grid} vertical={false} />
                        <XAxis
                          dataKey="name"
                          tick={{ fill: CHART_STYLE.tick, fontSize: 11 }}
                          axisLine={{ stroke: CHART_STYLE.border }}
                          tickLine={false}
                        />
                        <YAxis
                          tick={{ fill: CHART_STYLE.tick, fontSize: 11 }}
                          axisLine={false}
                          tickLine={false}
                          unit="h"
                        />
                        <Tooltip content={<HoursTooltip />} />
                        <Legend wrapperStyle={{ fontSize: 11, color: CHART_STYLE.tick, paddingTop: 8 }} />
                        <Bar dataKey="Backlog"       stackId="a" fill={STATUS_COLORS.Backlog} />
                        <Bar dataKey="En Progreso"   stackId="a" fill={STATUS_COLORS['En Progreso']} />
                        <Bar dataKey="Validación"    stackId="a" fill={STATUS_COLORS.Validación} />
                        <Bar dataKey="Done"          stackId="a" fill={STATUS_COLORS.Done} radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </div>

                {/* Chart 3: Vertical — completion % per project */}
                <div className="card border border-border">
                  <p className="card-title">Completitud por proyecto (%)</p>
                  {completionChartData.length === 0 ? (
                    <EmptyChart message={emptyChartMsg} />
                  ) : (
                    <ResponsiveContainer width="100%" height={260}>
                      <BarChart data={completionChartData} margin={{ top: 4, right: 12, bottom: 4, left: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke={CHART_STYLE.grid} vertical={false} />
                        <XAxis
                          dataKey="name"
                          tick={{ fill: CHART_STYLE.tick, fontSize: 11 }}
                          axisLine={{ stroke: CHART_STYLE.border }}
                          tickLine={false}
                        />
                        <YAxis
                          domain={[0, 100]}
                          tick={{ fill: CHART_STYLE.tick, fontSize: 11 }}
                          axisLine={false}
                          tickLine={false}
                          unit="%"
                        />
                        <Tooltip
                          {...tooltipStyle}
                          formatter={v => [`${v}%`, 'Completado']}
                        />
                        <Bar dataKey="pct" name="Completado %" radius={[4, 4, 0, 0]}>
                          {completionChartData.map((entry, i) => (
                            <Cell
                              key={`c-${i}`}
                              fill={
                                entry.pct >= 75 ? '#10b981'
                                  : entry.pct >= 50 ? '#f59e0b'
                                  : '#ef4444'
                              }
                            />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </div>

              </div>
            </div>
          </section>

          {/* ── SECTION 4: Tables ──────────────────────────────────────────── */}
          <section>
            <SectionTitle>Tablas de estado</SectionTitle>
            <div className="space-y-4">

              {/* Table 1: By person */}
              <div className="card border border-border">
                <p className="card-title">Estado por persona</p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm min-w-[640px]">
                    <thead>
                      <tr className="text-left border-b border-border">
                        <th className="pb-2 pr-4 text-xs text-text-muted font-semibold">Persona</th>
                        <th className="pb-2 pr-4 text-xs text-accent-blue font-semibold text-right">To Do</th>
                        <th className="pb-2 pr-4 text-xs text-accent-yellow font-semibold text-right">En Progreso</th>
                        <th className="pb-2 pr-4 text-xs text-accent-purple font-semibold text-right">Validación</th>
                        <th className="pb-2 pr-4 text-xs text-accent-green font-semibold text-right">Done</th>
                        <th className="pb-2 pr-4 text-xs text-text-muted font-semibold text-right">Restante</th>
                        <th className="pb-2 pr-4 text-xs text-text-muted font-semibold text-right">Vel. hoy</th>
                        <th className="pb-2 text-xs text-text-muted font-semibold text-right">Proyectos</th>
                      </tr>
                    </thead>
                    <tbody>
                      {allByPerson.map((p, i) => (
                        <tr
                          key={p.account_id}
                          className={clsx(
                            'border-b border-border/40 transition-colors hover:bg-bg-secondary/30',
                            i % 2 === 0 && 'bg-bg-primary/20',
                          )}
                        >
                          <td className="py-2.5 pr-4 font-medium text-text-primary">{p.name}</td>
                          <td className="py-2.5 pr-4 text-right tabular-nums text-accent-blue">{p.todo_count}</td>
                          <td className="py-2.5 pr-4 text-right tabular-nums text-accent-yellow">{p.in_progress_count}</td>
                          <td className="py-2.5 pr-4 text-right tabular-nums text-accent-purple">{p.validation_count}</td>
                          <td className="py-2.5 pr-4 text-right tabular-nums text-accent-green">{p.done_count}</td>
                          <td className="py-2.5 pr-4 text-right tabular-nums text-text-primary font-medium">{p.remaining_h}h</td>
                          <td className="py-2.5 pr-4 text-right tabular-nums text-text-secondary">{p.velocity_today} SP/d</td>
                          <td className="py-2.5 text-right tabular-nums text-text-muted">{p.n_projects}</td>
                        </tr>
                      ))}
                      {allByPerson.length === 0 && (
                        <tr>
                          <td colSpan={8} className="py-6 text-center text-text-muted text-xs">
                            Sin datos de asignación
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Table 2: By project */}
              <div className="card border border-border">
                <p className="card-title">Estado por proyecto</p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm min-w-[780px]">
                    <thead>
                      <tr className="text-left border-b border-border">
                        <th className="pb-2 pr-4 text-xs text-text-muted font-semibold">Proyecto</th>
                        <th className="pb-2 pr-4 text-xs text-accent-blue font-semibold text-right">To Do</th>
                        <th className="pb-2 pr-4 text-xs text-accent-yellow font-semibold text-right">En Progreso</th>
                        <th className="pb-2 pr-4 text-xs text-accent-purple font-semibold text-right">Validación</th>
                        <th className="pb-2 pr-4 text-xs text-accent-green font-semibold text-right">Done</th>
                        <th className="pb-2 pr-4 text-xs text-text-muted font-semibold text-right">Restante</th>
                        <th className="pb-2 pr-4 text-xs text-text-muted font-semibold text-right">Desviación</th>
                        <th className="pb-2 pr-4 text-xs text-text-muted font-semibold text-right">Vel. hoy</th>
                        <th className="pb-2 text-xs text-text-muted font-semibold text-right">Oblig. pend.</th>
                      </tr>
                    </thead>
                    <tbody>
                      {byProject.map((p, i) => (
                        <tr
                          key={p.key}
                          className={clsx(
                            'border-b border-border/40 transition-colors hover:bg-bg-secondary/30',
                            i % 2 === 0 && 'bg-bg-primary/20',
                          )}
                        >
                          <td className="py-2.5 pr-4">
                            <span className="font-mono text-xs bg-bg-primary px-1.5 py-0.5 rounded border border-border">{p.key}</span>
                            <span className="ml-2 text-text-secondary text-xs">{p.name}</span>
                          </td>
                          <td className="py-2.5 pr-4 text-right tabular-nums text-accent-blue">{p.todo_count}</td>
                          <td className="py-2.5 pr-4 text-right tabular-nums text-accent-yellow">{p.in_progress_count}</td>
                          <td className="py-2.5 pr-4 text-right tabular-nums text-accent-purple">{p.validation_count}</td>
                          <td className="py-2.5 pr-4 text-right tabular-nums text-accent-green">{p.done_count}</td>
                          <td className="py-2.5 pr-4 text-right tabular-nums text-text-primary font-medium">{p.remaining_h}h</td>
                          <td className="py-2.5 pr-4 text-right tabular-nums font-semibold">
                            <DeviationSign v={p.deviation_pct} />
                          </td>
                          <td className="py-2.5 pr-4 text-right tabular-nums text-text-secondary">{p.velocity_today} SP/d</td>
                          <td className="py-2.5 text-right tabular-nums">
                            {p.mandatory_incomplete > 0
                              ? <span className="text-accent-red font-semibold">{p.mandatory_incomplete}</span>
                              : <span className="text-accent-green text-xs font-semibold">✓ ok</span>}
                          </td>
                        </tr>
                      ))}
                      {byProject.length === 0 && (
                        <tr>
                          <td colSpan={9} className="py-6 text-center text-text-muted text-xs">
                            Sin datos de proyecto
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>
          </section>

          {/* ── SECTION 5: Deviations ──────────────────────────────────────── */}
          <section>
            <SectionTitle>Desviaciones {'>'} 10%</SectionTitle>

            {deviations.length === 0 ? (
              <div className="card border border-accent-green/20 flex items-center gap-3 py-5">
                <CheckCircle size={18} className="text-accent-green flex-shrink-0" />
                <p className="text-sm text-accent-green font-medium">
                  Sin desviaciones significativas en este sprint
                </p>
              </div>
            ) : (
              <div className="card border border-border">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm min-w-[540px]">
                    <thead>
                      <tr className="text-left border-b border-border">
                        <th className="pb-2 pr-4 text-xs text-text-muted font-semibold">Clave</th>
                        <th className="pb-2 pr-4 text-xs text-text-muted font-semibold">Resumen</th>
                        <th className="pb-2 pr-4 text-xs text-text-muted font-semibold text-right">Estimado</th>
                        <th className="pb-2 pr-4 text-xs text-text-muted font-semibold text-right">Real</th>
                        <th className="pb-2 text-xs text-text-muted font-semibold text-right">Desviación %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {deviations.map((d, i) => (
                        <tr
                          key={d.key}
                          className={clsx(
                            'border-b border-border/40 transition-colors hover:bg-bg-secondary/30',
                            i % 2 === 0 && 'bg-bg-primary/20',
                          )}
                        >
                          <td className="py-2.5 pr-4">
                            <span className="font-mono text-xs text-accent-blue">{d.key}</span>
                          </td>
                          <td className="py-2.5 pr-4 text-text-secondary max-w-xs truncate">{d.summary}</td>
                          <td className="py-2.5 pr-4 text-right tabular-nums text-text-primary">{d.original_h}h</td>
                          <td className="py-2.5 pr-4 text-right tabular-nums text-text-primary">{d.spent_h}h</td>
                          <td className="py-2.5 text-right tabular-nums font-semibold">
                            <DeviationSign v={d.deviation_pct} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="text-xs text-text-muted mt-3">
                  {deviations.length} issue{deviations.length !== 1 ? 's' : ''} con desviación significativa
                </p>
              </div>
            )}
          </section>

        </>
      )}
    </div>
  )
}
