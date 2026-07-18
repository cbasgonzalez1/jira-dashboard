import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { AlertTriangle, UserX, Layers, Activity, FolderOpen } from 'lucide-react'
import { getOverview, getSprintProjects } from '../api/jiraApi.js'
import { useProject } from '../App.jsx'
import KPICard from '../components/ui/KPICard.jsx'
import { KPISkeleton, ErrorCard } from '../components/ui/LoadingSpinner.jsx'
import clsx from 'clsx'

// ── Project card ───────────────────────────────────────────────────────────────
function ProjectCard({ proj, hasStats, onNavigate }) {
  const pct = proj.sprint_pct ?? 0
  const barColor = pct >= 70 ? 'bg-accent-green' : pct >= 40 ? 'bg-accent-yellow' : 'bg-accent-red'

  return (
    <div className="card border border-border flex flex-col gap-3 hover:border-accent-blue/30 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <span className="font-mono text-xs font-bold px-1.5 py-0.5 rounded bg-accent-blue/10 text-accent-blue border border-accent-blue/20">
            {proj.key}
          </span>
          <h3 className="text-sm font-semibold text-text-primary mt-2 truncate">{proj.name}</h3>
        </div>
        {hasStats && (
          <span className="text-xs text-text-muted flex-shrink-0">{proj.open_issues} abiertas</span>
        )}
      </div>

      {hasStats ? (
        <>
          {/* Sprint progress */}
          <div>
            <div className="flex justify-between text-xs text-text-muted mb-1.5">
              <span>Progreso del sprint</span>
              <span>{proj.sprint_done}/{proj.sprint_total}</span>
            </div>
            <div className="h-1.5 bg-bg-primary rounded-full overflow-hidden">
              <div className={clsx('h-full rounded-full transition-all', barColor)} style={{ width: `${pct}%` }} />
            </div>
            <div className="text-xs text-text-muted mt-1">{pct}% completado</div>
          </div>

          {/* Mini stats */}
          <div className="grid grid-cols-3 gap-2">
            {[
              { label: 'Críticos',    value: proj.critical_bugs,     color: 'text-accent-red' },
              { label: 'Sin asignar', value: proj.unassigned,        color: 'text-accent-yellow' },
              { label: 'Épics',       value: proj.epics_in_progress, color: 'text-accent-purple' },
            ].map(({ label, value, color }) => (
              <div key={label} className="bg-bg-primary rounded-lg p-2 text-center">
                <div className={clsx('text-lg font-bold tabular-nums', color)}>{value}</div>
                <div className="text-xs text-text-muted">{label}</div>
              </div>
            ))}
          </div>
        </>
      ) : (
        /* No stats yet — simple placeholder */
        <div className="flex items-center gap-2 text-xs text-text-muted py-1">
          <FolderOpen size={14} className="opacity-50" />
          <span>Sin datos de sprint activo</span>
        </div>
      )}

      {/* Quick links — switch the active project, then navigate */}
      <div className="flex gap-2 pt-1 border-t border-border">
        {[
          { label: 'Velocidad', href: '/velocity' },
          { label: 'Burndown',  href: '/burndown' },
          { label: 'Equipo',    href: '/team' },
        ].map(({ label, href }) => (
          <button
            key={label}
            onClick={() => onNavigate(proj.key, href)}
            className="flex-1 text-center text-xs py-1.5 rounded-lg bg-bg-primary text-text-secondary hover:text-accent-blue hover:bg-accent-blue/5 transition-colors border border-border"
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────────
export default function Overview() {
  const { setProject } = useProject()
  const navigate = useNavigate()

  function handleNavigate(projectKey, href) {
    setProject(projectKey)
    navigate(href)
  }

  // Global KPI stats (may show 0s if Jira calls fail — logged server-side)
  const { data: overviewData, isLoading: overviewLoading, isError, refetch } = useQuery({
    queryKey: ['overview'],
    queryFn: () => getOverview().then(r => r.data),
    refetchInterval: 60_000,
  })

  // Project list — uses same cache key as App.jsx to avoid duplicate requests
  const { data: projects, isLoading: projectsLoading } = useQuery({
    queryKey: ['app-projects'],
    queryFn: () => getSprintProjects().then(r => r.data),
    staleTime: 5 * 60_000,
  })

  // Build a map from overview per-project stats for fast lookup
  const statsMap = new Map((overviewData?.projects ?? []).map(p => [p.key, p]))

  const isLoading = overviewLoading || projectsLoading

  if (isError) return <ErrorCard message="Error al cargar los datos del resumen." onRetry={refetch} />

  return (
    <div className="space-y-6 animate-fade-in">

      {/* ── Global KPIs ──────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {overviewLoading ? (
          Array(4).fill(0).map((_, i) => <KPISkeleton key={i} />)
        ) : (
          <>
            <KPICard label="Issues abiertas"  value={overviewData?.total_open}              icon={Activity}      color="blue"   subtitle="en todos los proyectos" />
            <KPICard label="Bugs críticos"    value={overviewData?.total_critical_bugs}     icon={AlertTriangle} color="red"    subtitle="requieren acción inmediata" />
            <KPICard label="Sin asignar"      value={overviewData?.total_unassigned}        icon={UserX}         color="yellow" subtitle="sin responsable" />
            <KPICard label="Épics en curso"   value={overviewData?.total_epics_in_progress} icon={Layers}        color="purple" subtitle="iniciativas activas" />
          </>
        )}
      </div>

      {/* ── Project grid header ───────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-text-primary">Proyectos accesibles</h2>
        {!projectsLoading && (
          <span className="text-xs text-text-muted">{projects?.length ?? 0} proyectos</span>
        )}
      </div>

      {/* ── Project cards ─────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {projectsLoading ? (
          Array(6).fill(0).map((_, i) => (
            <div key={i} className="card border border-border space-y-4">
              <div className="skeleton h-4 w-20 rounded" />
              <div className="skeleton h-3 w-32 rounded" />
              <div className="skeleton h-3 w-full rounded" />
              <div className="grid grid-cols-3 gap-2">
                {Array(3).fill(0).map((_, j) => <div key={j} className="skeleton h-12 rounded-lg" />)}
              </div>
            </div>
          ))
        ) : (projects ?? []).length === 0 ? (
          <div className="col-span-3 card border border-border flex flex-col items-center gap-3 py-12 text-center text-text-muted">
            <FolderOpen size={32} className="opacity-25" />
            <p className="text-sm">No se encontraron proyectos accesibles</p>
          </div>
        ) : (
          (projects ?? []).map(p => {
            const stats = statsMap.get(p.key)
            return (
              <ProjectCard
                key={p.key}
                proj={{ key: p.key, name: p.name, ...stats }}
                hasStats={!!stats}
                onNavigate={handleNavigate}
              />
            )
          })
        )}
      </div>

    </div>
  )
}
