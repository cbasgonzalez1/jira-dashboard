import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'

const PALETTE = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
  '#8b5cf6', '#f97316', '#06b6d4', '#84cc16',
]

const TOOLTIP_STYLE = {
  backgroundColor: '#1e2130',
  border: '1px solid #2a2d3e',
  borderRadius: 8,
  color: '#e2e8f0',
  fontSize: 13,
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const { name, value } = payload[0]
  return (
    <div style={TOOLTIP_STYLE} className="p-2.5 shadow-xl">
      <p className="text-text-primary font-medium">{name}</p>
      <p className="text-text-secondary">{value.toLocaleString()} issues</p>
    </div>
  )
}

export default function DonutChart({ title, data = {} }) {
  const entries = Object.entries(data).filter(([, v]) => v > 0)
  const total = entries.reduce((s, [, v]) => s + v, 0)

  const chartData = entries.map(([name, value]) => ({ name, value }))

  return (
    <div className="card border border-border flex flex-col">
      <p className="card-title">{title}</p>
      {total === 0 ? (
        <div className="flex items-center justify-center h-40 text-text-muted text-sm">No data</div>
      ) : (
        <>
          <div className="relative">
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={52}
                  outerRadius={76}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {chartData.map((_, i) => (
                    <Cell key={i} fill={PALETTE[i % PALETTE.length]} strokeWidth={0} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            {/* Center label */}
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-2xl font-bold text-text-primary">{total.toLocaleString()}</span>
              <span className="text-xs text-text-muted">total</span>
            </div>
          </div>
          {/* Legend */}
          <div className="mt-2 space-y-1">
            {chartData.map(({ name, value }, i) => (
              <div key={name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: PALETTE[i % PALETTE.length] }} />
                  <span className="text-text-secondary">{name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-text-primary font-medium">{value}</span>
                  <span className="text-text-muted w-8 text-right">{Math.round(value / total * 100)}%</span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
