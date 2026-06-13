import { NavLink } from 'react-router-dom'
import { LayoutDashboard, TrendingUp, Flame, ListTodo, Users, ExternalLink, Kanban } from 'lucide-react'
import { useProject } from '../../App.jsx'
import clsx from 'clsx'

const NAV = [
  { to: '/',          icon: LayoutDashboard, label: 'Resumen' },
  { to: '/velocity',  icon: TrendingUp,      label: 'Velocidad' },
  { to: '/burndown',  icon: Flame,           label: 'Burndown' },
  { to: '/backlog',   icon: ListTodo,        label: 'Backlog' },
  { to: '/team',      icon: Users,           label: 'Carga del Equipo' },
  { to: '/sprint',    icon: Kanban,          label: 'Sprint Dashboard' },
]

export default function Sidebar() {
  const { project, setProject, projects } = useProject()

  return (
    <aside className="fixed top-0 left-0 bottom-0 w-60 bg-bg-secondary border-r border-border flex flex-col z-20">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-border">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-accent-blue flex items-center justify-center text-sm">📊</div>
          <div>
            <div className="text-sm font-bold text-text-primary leading-tight">Jira Dashboard</div>
            <div className="text-xs text-text-muted leading-tight">mda-tfm</div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        <p className="px-2 py-2 text-xs font-semibold uppercase tracking-widest text-text-muted">Dashboards</p>
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => clsx(
              'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors duration-150',
              isActive
                ? 'bg-accent-blue/10 text-accent-blue font-medium border border-accent-blue/20'
                : 'text-text-secondary hover:text-text-primary hover:bg-bg-primary'
            )}
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}

        <div className="pt-4">
          <p className="px-2 py-2 text-xs font-semibold uppercase tracking-widest text-text-muted">Enlaces</p>
          <a
            href="https://jira.aes.alcatel.fr:8443"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-text-secondary hover:text-text-primary hover:bg-bg-primary transition-colors"
          >
            <ExternalLink size={16} />
            Jira Server ↗
          </a>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-text-secondary hover:text-text-primary hover:bg-bg-primary transition-colors"
          >
            <ExternalLink size={16} />
            API Docs ↗
          </a>
        </div>
      </nav>

      {/* Project selector */}
      <div className="px-3 py-4 border-t border-border">
        <p className="px-2 mb-2 text-xs font-semibold uppercase tracking-widest text-text-muted">Proyecto</p>
        <div className="space-y-1">
          {projects.map(p => (
            <button
              key={p.key}
              onClick={() => setProject(p.key)}
              className={clsx(
                'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors duration-150 text-left',
                project === p.key
                  ? 'bg-bg-primary text-text-primary font-medium'
                  : 'text-text-secondary hover:text-text-primary hover:bg-bg-primary'
              )}
            >
              <span className="w-2 h-2 rounded-full flex-shrink-0 bg-accent-blue" />
              <span className="font-mono text-xs text-text-muted w-12 flex-shrink-0 truncate">{p.key}</span>
              <span className="truncate">{p.name}</span>
            </button>
          ))}
        </div>
      </div>
    </aside>
  )
}
