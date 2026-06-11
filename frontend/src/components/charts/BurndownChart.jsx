import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ReferenceLine, ResponsiveContainer, Area, ComposedChart,
} from 'recharts'
import { format } from 'date-fns'

const TOOLTIP_STYLE = {
  backgroundColor: '#1e2130',
  border: '1px solid #2a2d3e',
  borderRadius: 8,
  color: '#e2e8f0',
  fontSize: 13,
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const ideal = payload.find(p => p.dataKey === 'ideal')?.value
  const actual = payload.find(p => p.dataKey === 'actual')?.value
  return (
    <div style={TOOLTIP_STYLE} className="p-3 shadow-xl">
      <p className="font-semibold text-text-primary mb-2">{label}</p>
      {ideal != null && <p className="text-text-secondary">Ideal: <strong>{ideal} pts</strong></p>}
      {actual != null && (
        <p className="text-accent-blue">
          Actual: <strong>{actual} pts</strong>
          {ideal != null && actual > ideal && <span className="text-accent-red ml-1">(+{actual - ideal} behind)</span>}
          {ideal != null && actual < ideal && <span className="text-accent-green ml-1">({ideal - actual} ahead)</span>}
        </p>
      )}
    </div>
  )
}

export default function BurndownChart({ days = [], ideal = [], actual = [] }) {
  const data = days.map((day, i) => ({
    day,
    ideal: ideal[i] ?? null,
    actual: actual[i] ?? null,
  }))

  // Find today index (first null in actual)
  const todayIdx = actual.findIndex(v => v === null)
  const todayLabel = todayIdx > 0 ? days[todayIdx] : null

  return (
    <ResponsiveContainer width="100%" height={340}>
      <ComposedChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3e" vertical={false} />
        <XAxis
          dataKey="day"
          tick={{ fill: '#94a3b8', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          interval="preserveStartEnd"
        />
        <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
        <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#2a2d3e' }} />
        <Legend
          formatter={(v) => <span style={{ color: '#94a3b8', fontSize: 12 }}>{v}</span>}
          wrapperStyle={{ paddingTop: 16 }}
        />
        <Area
          dataKey="actual"
          name="Actual remaining"
          stroke="#3b82f6"
          strokeWidth={2}
          fill="#3b82f6"
          fillOpacity={0.08}
          dot={false}
          connectNulls={false}
        />
        <Line
          dataKey="ideal"
          name="Ideal burndown"
          stroke="#94a3b8"
          strokeWidth={1.5}
          strokeDasharray="6 4"
          dot={false}
          connectNulls
        />
        {todayLabel && (
          <ReferenceLine
            x={todayLabel}
            stroke="#f59e0b"
            strokeDasharray="4 2"
            label={{ value: 'Today', fill: '#f59e0b', fontSize: 11, position: 'insideTopRight' }}
          />
        )}
      </ComposedChart>
    </ResponsiveContainer>
  )
}
