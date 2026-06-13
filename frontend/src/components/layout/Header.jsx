import { useLocation } from 'react-router-dom'
import { RefreshCw, Calendar } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import { useProject } from '../../App.jsx'

const PAGE_TITLES = {
  '/':          { title: 'Resumen',            subtitle: 'Vista global de todos los proyectos' },
  '/velocity':  { title: 'Velocidad',          subtitle: 'Sprints comprometidos vs completados' },
  '/burndown':  { title: 'Burndown',           subtitle: 'Progreso del sprint activo' },
  '/backlog':   { title: 'Backlog',            subtitle: 'Distribución de issues sin planificar' },
  '/team':      { title: 'Carga del Equipo',   subtitle: 'Carga de trabajo por miembro' },
  '/sprint':    { title: 'Sprint Dashboard',   subtitle: 'Estado, capacidad y desviaciones del sprint' },
}

export default function Header() {
  const location = useLocation()
  const qc = useQueryClient()
  const { project } = useProject()
  const page = PAGE_TITLES[location.pathname] || { title: 'Dashboard', subtitle: '' }

  const handleRefresh = () => {
    qc.invalidateQueries()
  }

  return (
    <header className="h-14 border-b border-border bg-bg-secondary/50 backdrop-blur flex items-center justify-between px-6 flex-shrink-0">
      <div>
        <h1 className="text-base font-semibold text-text-primary">{page.title}</h1>
        <p className="text-xs text-text-muted">{page.subtitle}</p>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 text-xs text-text-muted">
          <Calendar size={13} />
          {format(new Date(), "d MMM yyyy", { locale: es })}
        </div>

        <div className="h-4 w-px bg-border" />

        <span className="font-mono text-xs px-2 py-1 rounded bg-bg-primary border border-border text-text-secondary">
          {project}
        </span>

        <button
          onClick={handleRefresh}
          className="flex items-center gap-1.5 btn btn-ghost text-xs"
          title="Actualizar datos"
        >
          <RefreshCw size={13} />
          Actualizar
        </button>
      </div>
    </header>
  )
}
