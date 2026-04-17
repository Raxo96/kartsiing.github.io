import { useMemo, useState } from 'react'
import {
  LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from 'recharts'
import { useAppData } from '../contexts/DataContext'
import LoadingSpinner from '../components/LoadingSpinner'
import { CHART_COLORS, positionColor } from '../utils/standings'

const GRID_CLR = '#27272a'
const AXIS_CLR = '#71717a'

function ChartCard({ title, children }) {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
      <h2 className="text-base font-semibold text-zinc-200">{title}</h2>
      {children}
    </div>
  )
}

export default function Charts() {
  const { standings, loading, error } = useAppData()
  const [topN, setTopN] = useState(8)

  if (loading) return <LoadingSpinner />
  if (error)   return <p className="text-red-400 text-center py-12">Failed to load data: {error}</p>

  const races = standings.races
  const allRows = standings.standings

  // Top-N drivers by total points
  const topDrivers = allRows.slice(0, topN)

  // --- Points progression (cumulative per race) ---
  const progressionData = useMemo(() => races.map((race, i) => {
    const point = { race }
    for (const d of topDrivers) {
      point[d.driver] = races.slice(0, i + 1).reduce((s, r) => s + (d.race_points[r] || 0), 0)
    }
    return point
  }), [standings, topN])

  // --- Championship gap to leader after each race ---
  const gapData = useMemo(() => races.map((race, i) => {
    const prevRaces = races.slice(0, i + 1)
    const totals = allRows
      .map(d => ({ driver: d.driver, pts: prevRaces.reduce((s, r) => s + (d.race_points[r] || 0), 0) }))
      .sort((a, b) => b.pts - a.pts)
    const leaderPts = totals[0]?.pts ?? 0
    const point = { race }
    for (const d of topDrivers) {
      const found = totals.find(t => t.driver === d.driver)
      point[d.driver] = leaderPts - (found?.pts ?? 0)
    }
    return point
  }), [standings, topN])

  // --- Position heatmap: driver × race ---
  const heatmapDrivers = allRows.filter(d =>
    d.race_points && Object.values(d.race_points).some(v => v > 0)
  )

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Season Charts</h1>
        <div className="flex items-center gap-2 text-sm text-zinc-400">
          <span>Show top</span>
          {[5, 8, 12].map(n => (
            <button
              key={n}
              onClick={() => setTopN(n)}
              className={`px-2.5 py-1 rounded transition-colors ${
                topN === n ? 'bg-zinc-700 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              {n}
            </button>
          ))}
          <span>drivers</span>
        </div>
      </div>

      {/* Points progression */}
      <ChartCard title="Championship Points Progression">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={progressionData} margin={{ top: 8, right: 24, left: -8, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={GRID_CLR} />
            <XAxis dataKey="race" tick={{ fill: AXIS_CLR, fontSize: 12 }} />
            <YAxis tick={{ fill: AXIS_CLR, fontSize: 12 }} />
            <Tooltip contentStyle={{ background: '#18181b', border: '1px solid #27272a', borderRadius: 8, fontSize: 12 }} />
            <Legend wrapperStyle={{ fontSize: 11, color: AXIS_CLR }} />
            {topDrivers.map((d, i) => (
              <Line
                key={d.driver}
                type="monotone"
                dataKey={d.driver}
                stroke={CHART_COLORS[i % CHART_COLORS.length]}
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Championship gap */}
      <ChartCard title="Gap to Championship Leader (after each race)">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={gapData} margin={{ top: 8, right: 24, left: -8, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={GRID_CLR} vertical={false} />
            <XAxis dataKey="race" tick={{ fill: AXIS_CLR, fontSize: 12 }} />
            <YAxis tick={{ fill: AXIS_CLR, fontSize: 12 }} />
            <Tooltip contentStyle={{ background: '#18181b', border: '1px solid #27272a', borderRadius: 8, fontSize: 12 }} />
            <Legend wrapperStyle={{ fontSize: 11, color: AXIS_CLR }} />
            {topDrivers.slice(1).map((d, i) => (
              <Bar key={d.driver} dataKey={d.driver} fill={CHART_COLORS[(i + 1) % CHART_COLORS.length]} radius={[4, 4, 0, 0]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
        <p className="text-xs text-zinc-500">Leader ({topDrivers[0]?.driver}) is always 0 — showing gap for all others.</p>
      </ChartCard>

      {/* Position heatmap */}
      <ChartCard title="Finishing Position Heatmap">
        <div className="overflow-x-auto scrollbar-thin">
          {/* Header row */}
          <div className="grid text-xs text-zinc-500 font-semibold mb-1"
               style={{ gridTemplateColumns: `180px repeat(${races.length}, 1fr)` }}>
            <span className="px-2">Driver</span>
            {races.map(r => <span key={r} className="text-center">{r}</span>)}
          </div>
          {/* Data rows */}
          {heatmapDrivers.map(row => (
            <div key={row.driver}
                 className="grid items-center border-b border-zinc-800/30 hover:bg-zinc-800/30"
                 style={{ gridTemplateColumns: `180px repeat(${races.length}, 1fr)` }}>
              <span className="px-2 py-1.5 text-xs text-zinc-300 truncate">{row.driver}</span>
              {races.map(race => {
                const pts = row.race_points[race]
                if (!pts) return <span key={race} className="mx-0.5 my-1 rounded text-[10px] text-center bg-zinc-800 text-zinc-600 py-1">—</span>
                // Derive position from standings data via points (approximation)
                return (
                  <span key={race} className={`mx-0.5 my-1 rounded text-[10px] font-bold text-center py-1 ${pts >= 25 ? 'bg-yellow-500 text-black' : pts >= 18 ? 'bg-zinc-400 text-black' : pts >= 15 ? 'bg-amber-600 text-black' : pts >= 8 ? 'bg-emerald-700 text-white' : pts > 0 ? 'bg-zinc-700 text-zinc-200' : 'bg-zinc-800 text-zinc-600'}`}>
                    {pts}
                  </span>
                )
              })}
            </div>
          ))}
        </div>
        <p className="text-xs text-zinc-500 mt-2">Cells show points earned. Gold = P1 (25pts), Silver = P2, Bronze = P3.</p>
      </ChartCard>

    </div>
  )
}
