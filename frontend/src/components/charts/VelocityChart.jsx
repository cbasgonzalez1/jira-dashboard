import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ReferenceLine, ResponsiveContainer,
} from 'recharts'

const TOOLTIP_STYLE = {
  backgroundColor: '#1e2130',
  border: '1px solid #2a2d3e',
  borderRadius: 8,
  color: '#e2e8f0',
  fontSize: 13,
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const committed = payload.find(p => p.dataKey === 'committed')?.value ?? 0
  const completed = payload.find(p => p.dataKey === 'completed')?.value ?? 0
  const pct = committed > 0 ? Math.round(completed / committed * 100) : 0
  return (
    <div style={TOOLTIP_STYLE} className="p-3 shadow-xl">
      <p className="font-semibold text-text-primary mb-2">{label}</p>
      <p className="text-accent-blue">Committed: <strong>{committed} pts</strong></p>
      <p className="text-accent-green">Completed: <strong>{completed} pts</strong></p>
      <p className="text-text-secondary mt-1">
        Completion: <strong className={pct >= 80 ? 'text-accent-green' : pct >= 60 ? 'text-accent-yellow' : 'text-accent-red'}>{pct}%</strong>
      </p>
    </div>
  )
}

export default function VelocityChart({ sprints = [], avgVelocity = 0 }) {
  const data = sprints.map(s => ({
    name: s.name.replace(/^(SCRUM|CRM|INF)\s/, ''),
    committed: s.committed,
    completed: s.completed,
    state: s.state,
  }))

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }} barGap={4}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3e" vertical={false} />
        <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
        <Legend
          formatter={(v) => <span style={{ color: '#94a3b8', fontSize: 12 }}>{v}</span>}
          wrapperStyle={{ paddingTop: 16 }}
        />
        <Bar dataKey="committed" name="Committed" fill="#3b82f6" fillOpacity={0.4} radius={[4, 4, 0, 0]} maxBarSize={40} />
        <Bar dataKey="completed" name="Completed" fill="#10b981" fillOpacity={0.85} radius={[4, 4, 0, 0]} maxBarSize={40} />
        {avgVelocity > 0 && (
          <ReferenceLine
            y={avgVelocity}
            stroke="#ef4444"
            strokeDasharray="6 3"
            label={{ value: `Avg ${avgVelocity}`, fill: '#ef4444', fontSize: 11, position: 'insideTopRight' }}
          />
        )}
      </BarChart>
    </ResponsiveContainer>
  )
}
