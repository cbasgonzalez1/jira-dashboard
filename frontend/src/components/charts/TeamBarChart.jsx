import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts'

const TOOLTIP_STYLE = {
  backgroundColor: '#1e2130',
  border: '1px solid #2a2d3e',
  borderRadius: 8,
  color: '#e2e8f0',
  fontSize: 13,
}

const COLORS = [
  '#3b82f6', '#10b981', '#8b5cf6', '#f59e0b',
  '#ef4444', '#f97316', '#06b6d4', '#84cc16',
]

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const d = payload[0]?.payload
  return (
    <div style={TOOLTIP_STYLE} className="p-3 shadow-xl">
      <p className="font-semibold text-text-primary mb-2">{label}</p>
      <p className="text-accent-blue">Issues: <strong>{d?.issues}</strong></p>
      <p className="text-accent-green">Story Points: <strong>{d?.story_points}</strong></p>
      {d?.blocked > 0 && <p className="text-accent-red">Blocked: <strong>{d.blocked}</strong></p>}
    </div>
  )
}

export default function TeamBarChart({ users = [] }) {
  const data = users
    .filter(([k]) => k !== '_unassigned')
    .map(([, info], i) => ({
      name: info.display.split(' ')[0], // first name only for readability
      display: info.display,
      issues: info.issues,
      story_points: info.story_points,
      blocked: info.blocked,
      color: COLORS[i % COLORS.length],
    }))
    .slice(0, 10) // max 10 people

  return (
    <ResponsiveContainer width="100%" height={Math.max(200, data.length * 44)}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 0, right: 40, left: 10, bottom: 0 }}
        barSize={18}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3e" horizontal={false} />
        <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis
          type="category"
          dataKey="name"
          width={70}
          tick={{ fill: '#e2e8f0', fontSize: 12 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
        <Bar dataKey="issues" name="Open Issues" radius={[0, 4, 4, 0]}>
          {data.map((d, i) => <Cell key={i} fill={d.color} fillOpacity={0.8} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
