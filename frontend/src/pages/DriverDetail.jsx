import { useParams, Link } from 'react-router-dom'
import { useState, useMemo } from 'react'
import {
  BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { useAppData } from '../contexts/DataContext'
import LoadingSpinner from '../components/LoadingSpinner'
import StatCard from '../components/StatCard'
import { positionColor, CHART_COLORS } from '../utils/standings'

const CHART_BG  = 'transparent'
const GRID_CLR  = '#27272a'
const AXIS_CLR  = '#71717a'

export default function DriverDetail() {
  const { name } = useParams()
  const { drivers, standings, loading, error } = useAppData()
  const [vsDriver, setVsDriver] = useState('')

  if (loading) return <LoadingSpinner />
  if (error)   return <p className="text-red-400 text-center py-12">Failed to load data: {error}</p>

  const driverName = decodeURIComponent(name)
  const driver = drivers?.drivers.find(d => d.name === driverName)
  if (!driver) return <p className="text-zinc-400 text-center py-12">Driver not found.</p>

  const { stats, race_history } = driver
  const races = standings?.races ?? []
  const allDriverNames = drivers?.drivers.map(d => d.name) ?? []

  // Points per race bar chart data
  const pointsData = races.map(race => {
    const h = race_history.find(r => r.race === race)
    return { race, points: h?.points ?? 0 }
  })

  // Position history line chart data
  const positionData = race_history.map(h => ({ race: h.race, position: h.position }))

  // Head-to-head: compare cumulative points per race
  const vsData = useMemo(() => {
    if (!vsDriver || !standings) return null
    const vsDriverData = drivers?.drivers.find(d => d.name === vsDriver)
    if (!vsDriverData) return null
    return races.map(race => {
      const myH  = race_history.find(r => r.race === race)
      const vsH  = vsDriverData.race_history.find(r => r.race === race)
      return {
        race,
        [driverName]: myH?.points ?? 0,
        [vsDriver]:   vsH?.points  ?? 0,
      }
    })
  }, [vsDriver, drivers, standings, race_history, races, driverName])

  return (
    <div className="space-y-8">

      {/* Header */}
      <div className="flex items-center gap-3">
        <Link to="/" className="text-zinc-500 hover:text-zinc-300 text-sm">← Standings</Link>
        <h1 className="text-2xl font-bold">{driverName}</h1>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-4 gap-3">
        <StatCard label="Total Points"  value={stats.total_points} accent="text-yellow-400" />
        <StatCard label="Races"         value={stats.races_entered} />
        <StatCard label="Wins"          value={stats.wins}          accent={stats.wins > 0 ? 'text-yellow-400' : ''} />
        <StatCard label="Podiums"       value={stats.podiums}       accent={stats.podiums > 0 ? 'text-amber-400' : ''} />
        <StatCard label="Fastest Laps"  value={stats.fastest_laps}  accent={stats.fastest_laps > 0 ? 'text-purple-400' : ''} />
        <StatCard label="Avg Position"  value={stats.avg_finish_position ?? '—'} />
        <StatCard label="Best Finish"   value={stats.best_finish  != null ? `P${stats.best_finish}`  : '—'} />
        <StatCard label="Penalties"     value={`${stats.total_penalties}s`} accent={stats.total_penalties > 0 ? 'text-red-400' : ''} />
      </div>

      {/* Race history table */}
      <div className="space-y-2">
        <h2 className="text-lg font-semibold">Race History</h2>
        <div className="overflow-x-auto scrollbar-thin rounded-lg border border-zinc-800">
          <table className="w-full text-sm">
            <thead className="bg-zinc-900 border-b border-zinc-800">
              <tr>
                {['Race', 'Position', 'Final', 'Points', 'Best Lap', 'Penalty'].map(h => (
                  <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold text-zinc-400 uppercase">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {race_history.map(h => (
                <tr key={h.race} className="border-b border-zinc-800/50 hover:bg-zinc-800/40">
                  <td className="px-4 py-2.5">
                    <Link to={`/races/${encodeURIComponent(h.race)}`} className="hover:text-racing-red transition-colors font-medium">
                      {h.race}
                    </Link>
                  </td>
                  <td className="px-4 py-2.5">
                    <span className={`inline-flex items-center justify-center w-7 h-7 rounded text-xs font-bold ${positionColor(h.position)}`}>
                      {h.position}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-zinc-400">{h.final}</td>
                  <td className={`px-4 py-2.5 font-bold ${h.has_fastest_lap ? 'text-purple-400' : 'text-zinc-100'}`}>
                    {h.points} {h.has_fastest_lap && '⚡'}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-zinc-300">{h.best_lap != null ? `${h.best_lap}s` : '—'}</td>
                  <td className={`px-4 py-2.5 font-mono ${h.penalty > 0 ? 'text-red-400' : 'text-zinc-500'}`}>
                    {h.penalty > 0 ? `+${h.penalty}s` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Points per race */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 space-y-3">
          <h3 className="text-sm font-semibold text-zinc-300">Points per Race</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={pointsData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID_CLR} vertical={false} />
              <XAxis dataKey="race" tick={{ fill: AXIS_CLR, fontSize: 11 }} />
              <YAxis tick={{ fill: AXIS_CLR, fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#18181b', border: '1px solid #27272a', borderRadius: 8 }} />
              <Bar dataKey="points" fill={CHART_COLORS[0]} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Position history */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 space-y-3">
          <h3 className="text-sm font-semibold text-zinc-300">Finishing Positions</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={positionData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID_CLR} />
              <XAxis dataKey="race" tick={{ fill: AXIS_CLR, fontSize: 11 }} />
              <YAxis reversed tick={{ fill: AXIS_CLR, fontSize: 11 }} domain={[1, 'dataMax']} />
              <Tooltip contentStyle={{ background: '#18181b', border: '1px solid #27272a', borderRadius: 8 }} />
              <ReferenceLine y={3} stroke="#cd7f32" strokeDasharray="4 2" label={{ value: 'P3', fill: '#cd7f32', fontSize: 10 }} />
              <Line type="monotone" dataKey="position" stroke={CHART_COLORS[0]} strokeWidth={2} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Head-to-head */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-zinc-300">Head-to-Head Comparison</h3>
          <select
            value={vsDriver}
            onChange={e => setVsDriver(e.target.value)}
            className="bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-sm text-zinc-200 focus:outline-none"
          >
            <option value="">Select driver…</option>
            {allDriverNames.filter(n => n !== driverName).map(n => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>

        {vsData ? (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={vsData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID_CLR} vertical={false} />
              <XAxis dataKey="race" tick={{ fill: AXIS_CLR, fontSize: 11 }} />
              <YAxis tick={{ fill: AXIS_CLR, fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#18181b', border: '1px solid #27272a', borderRadius: 8 }} />
              <Bar dataKey={driverName} fill={CHART_COLORS[0]} radius={[4, 4, 0, 0]} />
              <Bar dataKey={vsDriver}   fill={CHART_COLORS[1]} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-zinc-600 text-sm text-center py-8">Select a driver to compare</p>
        )}
      </div>
    </div>
  )
}
