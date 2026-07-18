import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Users, AlertTriangle } from 'lucide-react'
import { getTeam } from '../api/jiraApi.js'
import { useProject } from '../App.jsx'
import TeamBarChart from '../components/charts/TeamBarChart.jsx'
import KPICard from '../components/ui/KPICard.jsx'
import { KPISkeleton, ChartSkeleton, ErrorCard } from '../components/ui/LoadingSpinner.jsx'
import clsx from 'clsx'

const AVATAR_COLORS = [
  'bg-accent-blue', 'bg-accent-green', 'bg-accent-purple',
  'bg-accent-yellow', 'bg-accent-red', 'bg-accent-orange',
  'bg-teal-500', 'bg-pink-500',
]

const TYPE_PILL_COLORS = {
  story:    'bg-accent-blue/15 text-accent-blue',
  bug:      'bg-accent-red/15 text-accent-red',
  task:     'bg-accent-green/15 text-accent-green',
  epic:     'bg-accent-purple/15 text-accent-purple',
  historia: 'bg-accent-blue/15 text-accent-blue',
  error:    'bg-accent-red/15 text-accent-red',
  tarea:    'bg-accent-green/15 text-accent-green',
}

function initials(name) {
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
}

function UserCard({ username, block, idx }) {
  if (username === '_unassigned') return null
  const avatarColor = AVATAR_COLORS[idx % AVATAR_COLORS.length]

  return (
    <div className="card border border-border flex flex-col gap-3 hover:border-accent-blue/30 transition-colors">
      <div className="flex items-center gap-3">
        <div className={clsx('w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white flex-shrink-0', avatarColor)}>
          {initials(block.display)}
        </div>
        <div className="min-w-0">
          <div className="text-sm font-semibold text-text-primary truncate">{block.display}</div>
          <div className="text-xs text-text-muted truncate">{username}</div>
        </div>
        {block.blocked > 0 && (
          <span className="ml-auto flex items-center gap-1 text-xs text-accent-red bg-accent-red/10 border border-accent-red/20 rounded px-1.5 py-0.5">
            <AlertTriangle size={10} />
            {block.blocked}
          </span>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-2">
        <div className="bg-bg-primary rounded-lg p-2 text-center">
          <div className="text-lg font-bold text-accent-blue tabular-nums">{block.issues}</div>
          <div className="text-xs text-text-muted">Issues</div>
        </div>
        <div className="bg-bg-primary rounded-lg p-2 text-center">
          <div className="text-lg font-bold text-accent-green tabular-nums">{block.hours}h</div>
          <div className="text-xs text-text-muted">Horas</div>
        </div>
      </div>

      {/* Type pills */}
      <div className="flex flex-wrap gap-1.5">
        {Object.entries(block.by_type).map(([type, count]) => {
          const key = type.toLowerCase()
          const color = TYPE_PILL_COLORS[key] || 'bg-bg-primary text-text-secondary'
          return (
            <span key={type} className={clsx('text-xs px-2 py-0.5 rounded-full', color)}>
              {type} ({count})
            </span>
          )
        })}
      </div>

      {/* Load bar */}
      <div>
        <div className="h-1 bg-bg-primary rounded-full overflow-hidden">
          <div
            className={clsx('h-full rounded-full', avatarColor)}
            style={{ width: '100%', opacity: 0.3 + (block.issues / 20) * 0.7 }}
          />
        </div>
      </div>
    </div>
  )
}

const SCOPES = [
  { key: 'sprint', label: 'Sprint actual' },
  { key: 'backlog', label: 'Backlog total' },
]

export default function TeamLoad() {
  const { project } = useProject()
  const [scope, setScope] = useState('sprint')

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['team', project],
    queryFn: () => getTeam(project).then(r => r.data),
    refetchInterval: 60_000,
  })

  if (isError) return <ErrorCard message="Error al cargar datos del equipo." onRetry={refetch} />

  const users = data?.users ?? []
  // Project each person down to the selected scope's block — both blocks
  // share the same shape (display, issues, hours, blocked, by_type).
  const scopedUsers = users.map(([username, info]) => [username, info[scope]])
  const assignedUsers = scopedUsers.filter(([k, block]) => k !== '_unassigned' && block.issues > 0)
  const unassigned = scopedUsers.find(([k]) => k === '_unassigned')?.[1]
  const totalBlocked = scopedUsers.reduce((s, [, block]) => s + block.blocked, 0)
  const totalIssues = scope === 'backlog'
    ? (data?.total_issues ?? 0)
    : scopedUsers.reduce((s, [, block]) => s + block.issues, 0)

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Scope toggle */}
      <div className="inline-flex rounded-lg border border-border bg-bg-card p-1">
        {SCOPES.map(s => (
          <button
            key={s.key}
            onClick={() => setScope(s.key)}
            className={clsx(
              'px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
              scope === s.key ? 'bg-accent-blue text-white' : 'text-text-muted hover:text-text-primary',
            )}
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {isLoading ? Array(4).fill(0).map((_, i) => <KPISkeleton key={i} />) : (
          <>
            <KPICard label="Miembros del equipo" value={assignedUsers.length}    icon={Users}         color="blue"   subtitle="con issues abiertos" />
            <KPICard label="Issues totales"       value={totalIssues}             icon={Users}         color="green"  subtitle={scope === 'backlog' ? 'abiertos en el equipo' : 'en el sprint actual'} />
            <KPICard label="Sin asignar"          value={unassigned?.issues ?? 0} icon={AlertTriangle} color="yellow" subtitle="sin responsable" />
            <KPICard label="Bloqueados"           value={totalBlocked}            icon={AlertTriangle} color="red"    subtitle="issues bloqueados" />
          </>
        )}
      </div>

      {/* Horizontal bar chart */}
      {isLoading ? <ChartSkeleton height="h-64" /> : assignedUsers.length > 0 && (
        <div className="card border border-border">
          <p className="card-title">Issues por miembro del equipo</p>
          <TeamBarChart users={assignedUsers} />
        </div>
      )}

      {/* User cards grid */}
      <div>
        <h2 className="text-sm font-semibold text-text-primary mb-4">
          Detalle del equipo
          {!isLoading && <span className="text-text-muted font-normal ml-2">({assignedUsers.length} miembros)</span>}
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {isLoading ? (
            Array(6).fill(0).map((_, i) => (
              <div key={i} className="card border border-border space-y-3">
                <div className="flex items-center gap-3">
                  <div className="skeleton w-10 h-10 rounded-full" />
                  <div className="space-y-1.5 flex-1">
                    <div className="skeleton h-3 w-24 rounded" />
                    <div className="skeleton h-3 w-16 rounded" />
                  </div>
                </div>
                <div className="skeleton h-12 rounded-lg" />
              </div>
            ))
          ) : (
            assignedUsers.map(([username, block], idx) => (
              <UserCard key={username} username={username} block={block} idx={idx} />
            ))
          )}
        </div>
      </div>

      {/* Unassigned callout */}
      {!isLoading && unassigned && unassigned.issues > 0 && (
        <div className="card border border-accent-yellow/30 flex items-center gap-4">
          <AlertTriangle size={20} className="text-accent-yellow flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-text-primary">
              {unassigned.issues} issue{unassigned.issues > 1 ? 's' : ''} sin asignar
            </p>
            <p className="text-xs text-text-muted">
              {unassigned.hours}h sin responsable — asígnalos en Jira para mejorar el seguimiento.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
