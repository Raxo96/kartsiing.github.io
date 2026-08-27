import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useAppData } from '../contexts/DataContext'
import StatCard from '../components/StatCard'
import LoadingSpinner from '../components/LoadingSpinner'
import { buildRaceMeta, computePreviousPositions, podiumClass } from '../utils/standings'

function SortIcon({ active, dir }) {
  if (!active) return <span className="text-zinc-600 ml-1">↕</span>
  return <span className="text-zinc-200 ml-1">{dir === 'asc' ? '↑' : '↓'}</span>
}

function DeltaBadge({ current, prev }) {
  if (!prev) return null
  const delta = prev - current
  if (delta === 0) return <span className="text-zinc-500 text-xs">—</span>
  if (delta > 0)   return <span className="text-green-500 text-xs font-semibold">▲{delta}</span>
  return               <span className="text-red-400 text-xs font-semibold">▼{Math.abs(delta)}</span>
}

export default function Standings() {
  const { standings, races: racesData, stats, loading, error } = useAppData()
  const [filter, setFilter]       = useState('')
  const [sort, setSort]           = useState({ key: 'position', dir: 'asc' })

  const races     = standings?.races ?? []
  const rows      = standings?.standings ?? []
  const raceMeta  = useMemo(() => buildRaceMeta(racesData), [racesData])
  const prevPos   = useMemo(() => computePreviousPositions(standings), [standings])

  const sorted = useMemo(() => {
    const filtered = rows.filter(s =>
      s.driver.toLowerCase().includes(filter.toLowerCase())
    )
    return [...filtered].sort((a, b) => {
      let av, bv
      if (sort.key === 'position')     { av = a.position;     bv = b.position }
      else if (sort.key === 'top8')    { av = a.top8_points;  bv = b.top8_points }
      else if (sort.key === 'total')   { av = a.total_points; bv = b.total_points }
      else                             { av = a.race_points[sort.key] ?? 0; bv = b.race_points[sort.key] ?? 0 }
      return sort.dir === 'asc' ? av - bv : bv - av
    })
  }, [rows, filter, sort])

  const handleSort = key => setSort(s => ({
    key, dir: s.key === key && s.dir === 'asc' ? 'desc' : 'asc',
  }))

  const Th = ({ label, sortKey, className = '' }) => (
    <th
      onClick={() => handleSort(sortKey)}
      className={`px-3 py-3 text-xs font-semibold uppercase tracking-wider text-zinc-400 cursor-pointer
                  select-none hover:text-zinc-200 whitespace-nowrap ${className}`}
    >
      {label}<SortIcon active={sort.key === sortKey} dir={sort.dir} />
    </th>
  )

  if (loading) return <LoadingSpinner />
  if (error)   return <p className="text-red-400 text-center py-12">Failed to load data: {error}</p>

  return (
    <div className="space-y-6">

      {/* Season stats bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard label="Races"   value={stats?.total_races}   />
        <StatCard label="Drivers" value={stats?.total_drivers} />
        <StatCard label="Leader"  value={stats?.leader} sub={`${stats?.leader_points} pts (Top 8)`} accent="text-yellow-400" />
        <StatCard label="Most Wins" value={stats?.records.most_wins.driver} sub={`${stats?.records.most_wins.wins} win${stats?.records.most_wins.wins !== 1 ? 's' : ''}`} />
      </div>

      {/* Extra records */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {stats?.records.track_veteran?.driver && (() => {
          const v = stats.records.track_veteran
          const hours = (v.track_time_s / 3600).toFixed(2)
          return (
            <StatCard
              label="Track Veteran"
              value={v.driver}
              sub={`${v.laps} laps · ${hours}h est. track time`}
              accent="text-emerald-400"
            />
          )
        })()}
        {stats?.records.top_gainer?.driver && (
          <StatCard
            label="Top Gainer"
            value={stats.records.top_gainer.driver}
            sub={`▲ ${stats.records.top_gainer.positions_gained} pos · was P${stats.records.top_gainer.worst_rank}, now P${stats.records.top_gainer.current_rank}`}
            accent="text-green-400"
          />
        )}
        {stats?.records.top_loser?.driver && (
          <StatCard
            label="Top Loser"
            value={stats.records.top_loser.driver}
            sub={`▼ ${stats.records.top_loser.positions_lost} pos · was P${stats.records.top_loser.best_rank}, now P${stats.records.top_loser.current_rank}`}
            accent="text-red-400"
          />
        )}
        {stats?.records.most_consistent?.driver && (
          <StatCard
            label="Most Consistent"
            value={stats.records.most_consistent.driver}
            sub={`σ ${stats.records.most_consistent.stdev} position std dev`}
            accent="text-sky-400"
          />
        )}
        {stats?.records.most_penalties?.driver && stats.records.most_penalties.penalty_seconds > 0 && (
          <StatCard
            label="Penalty King"
            value={stats.records.most_penalties.driver}
            sub={`${stats.records.most_penalties.penalty_seconds}s total penalties`}
            accent="text-orange-400"
          />
        )}
        {stats?.records.most_fastest_laps?.driver && (
          <StatCard
            label="Most Fastest Laps"
            value={stats.records.most_fastest_laps.driver}
            sub={`${stats.records.most_fastest_laps.count} fastest lap${stats.records.most_fastest_laps.count !== 1 ? 's' : ''}`}
            accent="text-purple-400"
          />
        )}
        {stats?.records.most_podiums?.driver && (
          <StatCard
            label="Most Podiums"
            value={stats.records.most_podiums.driver}
            sub={`${stats.records.most_podiums.podiums} podium${stats.records.most_podiums.podiums !== 1 ? 's' : ''}`}
            accent="text-amber-400"
          />
        )}
      </div>

      {/* Filter */}
      <div className="flex items-center gap-3">
        <input
          value={filter}
          onChange={e => setFilter(e.target.value)}
          placeholder="Filter driver…"
          className="bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100
                     placeholder-zinc-500 focus:outline-none focus:border-zinc-500 w-48"
        />
        {filter && (
          <button onClick={() => setFilter('')} className="text-zinc-500 hover:text-zinc-300 text-sm">
            Clear
          </button>
        )}
        <span className="text-zinc-500 text-sm ml-auto">{sorted.length} drivers</span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto scrollbar-thin rounded-lg border border-zinc-800">
        <table className="w-full text-sm">
          <thead className="bg-zinc-900 border-b border-zinc-800">
            <tr>
              <Th label="Pos"    sortKey="position" className="text-center w-12" />
              <Th label="Driver" sortKey="driver"   className="text-left" />
              {races.map(r => <Th key={r} label={r} sortKey={r} className="text-center" />)}
              <Th label="Total"   sortKey="total"    className="text-center" />
              <Th label="Top 8"   sortKey="top8"     className="text-center font-bold text-yellow-400" />
            </tr>
          </thead>
          <tbody>
            {sorted.map((row, i) => {
              const pc = podiumClass(row.position)
              return (
                <tr key={row.driver} className={`border-b border-zinc-800/50 hover:bg-zinc-800/40 transition-colors ${pc}`}>

                  {/* Position */}
                  <td className="px-3 py-2.5 text-center w-12">
                    <div className="flex items-center justify-center gap-1">
                      <span className="font-mono font-semibold text-zinc-300">{row.position}</span>
                      <DeltaBadge current={row.position} prev={prevPos[row.driver]} />
                    </div>
                  </td>

                  {/* Driver */}
                  <td className="px-3 py-2.5">
                    <Link
                      to={`/drivers/${encodeURIComponent(row.driver)}`}
                      className="font-medium text-zinc-100 hover:text-racing-red transition-colors"
                    >
                      {row.driver}
                    </Link>
                  </td>

                  {/* Per-race points */}
                  {races.map(race => {
                    const pts    = row.race_points[race] ?? 0
                    const meta   = raceMeta[race]?.[row.driver]
                    const isFL   = meta?.has_fastest_lap
                    const hasPen = meta?.penalty > 0
                    const dropped = pts > 0 && row.counted_races && !row.counted_races.includes(race)
                    return (
                      <td key={race} className="px-3 py-2.5 text-center">
                        {pts === 0 ? (
                          <span className="text-zinc-600">—</span>
                        ) : (
                          <span className={`inline-flex items-center gap-1 font-mono
                            ${dropped  ? 'text-zinc-600 line-through'  : ''}
                            ${!dropped && isFL   ? 'text-purple-400' : ''}
                            ${!dropped && hasPen ? 'text-red-400'    : ''}
                            ${!dropped && !isFL && !hasPen ? 'text-zinc-200' : ''}`}
                          >
                            {pts}
                            {!dropped && isFL   && <span title="Fastest lap" className="text-purple-400 text-xs">⚡</span>}
                            {!dropped && hasPen && <span title={`+${meta.penalty}s penalty`} className="text-red-400 text-xs">⚠</span>}
                          </span>
                        )}
                      </td>
                    )
                  })}

                  {/* Total */}
                  <td className="px-3 py-2.5 text-center text-zinc-500">
                    {row.total_points}
                  </td>

                  {/* Top 8 */}
                  <td className="px-3 py-2.5 text-center font-bold text-yellow-400">
                    {row.top8_points}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex gap-4 text-xs text-zinc-500">
        <span><span className="text-purple-400">⚡</span> Fastest lap bonus (+1 pt)</span>
        <span><span className="text-red-400">⚠</span> Time penalty applied</span>
        <span><span className="text-yellow-400">▲</span>/<span className="text-red-400">▼</span> Position change vs previous race</span>
        <span><span className="text-zinc-600 line-through">pts</span> Dropped result (not in top 8)</span>
      </div>
    </div>
  )
}
