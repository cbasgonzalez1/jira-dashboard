import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, TrendingUp, UserX, Layers, Activity } from 'lucide-react'
import { getOverview } from '../api/jiraApi.js'
import KPICard from '../components/ui/KPICard.jsx'
import { KPISkeleton, ErrorCard } from '../components/ui/LoadingSpinner.jsx'
import clsx from 'clsx'

function ProjectCard({ proj }) {
  const pct = proj.sprint_pct || 0
  const barColor = pct >= 70 ? 'bg-accent-green' : pct >= 40 ? 'bg-accent-yellow' : 'bg-accent-red'

  return (
    <div className="card border border-border flex flex-col gap-4 hover:border-accent-blue/30 transition-colors">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-0.5">
            <span className="font-mono text-xs font-bold px-1.5 py-0.5 rounded bg-accent-blue/10 text-accent-blue border border-accent-blue/20">
              {proj.key}
            </span>
          </div>
          <h3 className="text-sm font-semibold text-text-primary mt-1">{proj.name}</h3>
        </div>
        <span className="text-xs text-text-muted">{proj.open_issues} abiertas</span>
      </div>

      {/* Sprint progress */}
      <div>
        <div className="flex justify-between text-xs text-text-muted mb-1.5">
          <span>Progreso del sprint</span>
          <span>{proj.sprint_done}/{proj.sprint_total} issues</span>
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

      {/* Quick links */}
      <div className="flex gap-2 pt-1 border-t border-border">
        {[
          { label: 'Velocidad', href: '/velocity' },
          { label: 'Burndown',  href: '/burndown' },
          { label: 'Equipo',    href: '/team' },
        ].map(({ label, href }) => (
          <a
            key={label}
            href={href}
            className="flex-1 text-center text-xs py-1.5 rounded-lg bg-bg-primary text-text-secondary hover:text-accent-blue hover:bg-accent-blue/5 transition-colors border border-border"
          >
            {label}
          </a>
        ))}
      </div>
    </div>
  )
}

export default function Overview() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['overview'],
    queryFn: () => getOverview().then(r => r.data),
    refetchInterval: 60_000,
  })

  if (isError) return <ErrorCard message="Error al cargar los datos del resumen." onRetry={refetch} />

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Global KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {isLoading ? (
          Array(4).fill(0).map((_, i) => <KPISkeleton key={i} />)
        ) : (
          <>
            <KPICard label="Issues abiertas"    value={data?.total_open}              icon={Activity}      color="blue"   subtitle="en todos los proyectos" />
            <KPICard label="Bugs críticos"       value={data?.total_critical_bugs}     icon={AlertTriangle} color="red"    subtitle="requieren acción inmediata" />
            <KPICard label="Sin asignar"         value={data?.total_unassigned}        icon={UserX}         color="yellow" subtitle="sin responsable" />
            <KPICard label="Épics en curso"      value={data?.total_epics_in_progress} icon={Layers}        color="purple" subtitle="iniciativas activas" />
          </>
        )}
      </div>

      {/* Section header */}
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-text-primary">Proyectos</h2>
        {!isLoading && (
          <span className="text-xs text-text-muted">{data?.active_projects} activos</span>
        )}
      </div>

      {/* Project cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {isLoading ? (
          Array(3).fill(0).map((_, i) => (
            <div key={i} className="card border border-border space-y-4">
              <div className="skeleton h-4 w-20 rounded" />
              <div className="skeleton h-3 w-full rounded" />
              <div className="skeleton h-3 w-full rounded" />
              <div className="grid grid-cols-3 gap-2">
                {Array(3).fill(0).map((_, j) => <div key={j} className="skeleton h-12 rounded-lg" />)}
              </div>
            </div>
          ))
        ) : (
          data?.projects?.map(proj => <ProjectCard key={proj.key} proj={proj} />)
        )}
      </div>
    </div>
  )
}
