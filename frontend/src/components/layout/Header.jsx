import { useLocation } from 'react-router-dom'
import { RefreshCw, Calendar } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import { useProject } from '../../App.jsx'

const PAGE_TITLES = {
  '/':          { title: 'Overview',          subtitle: 'All projects at a glance' },
  '/velocity':  { title: 'Velocity',          subtitle: 'Sprint committed vs completed' },
  '/burndown':  { title: 'Burndown',          subtitle: 'Active sprint progress' },
  '/backlog':   { title: 'Backlog',           subtitle: 'Unplanned issue distribution' },
  '/team':      { title: 'Team Load',         subtitle: 'Workload per team member' },
  '/sprint':    { title: 'Sprint Dashboard',  subtitle: 'Estado, capacidad y desviaciones del sprint' },
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
          {format(new Date(), 'MMM d, yyyy')}
        </div>

        <div className="h-4 w-px bg-border" />

        <span className="font-mono text-xs px-2 py-1 rounded bg-bg-primary border border-border text-text-secondary">
          {project}
        </span>

        <button
          onClick={handleRefresh}
          className="flex items-center gap-1.5 btn btn-ghost text-xs"
          title="Refresh all data"
        >
          <RefreshCw size={13} />
          Refresh
        </button>
      </div>
    </header>
  )
}
