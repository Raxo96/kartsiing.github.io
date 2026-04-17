import { useParams, Link } from 'react-router-dom'
import { useAppData } from '../contexts/DataContext'
import LoadingSpinner from '../components/LoadingSpinner'
import { positionColor } from '../utils/standings'

export default function RaceDetail() {
  const { name } = useParams()
  const { races, loading, error } = useAppData()

  if (loading) return <LoadingSpinner />
  if (error)   return <p className="text-red-400 text-center py-12">Failed to load data: {error}</p>

  const race = races?.races.find(r => r.name === decodeURIComponent(name))
  if (!race) return <p className="text-zinc-400 text-center py-12">Race not found.</p>

  const finalGroups = [...new Set(race.results.map(r => r.final))].sort()

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/races" className="text-zinc-500 hover:text-zinc-300 text-sm">← Races</Link>
        <h1 className="text-2xl font-bold">{race.name}</h1>
        {race.fastest_lap_driver && (
          <span className="ml-auto text-purple-400 text-sm">
            ⚡ Fastest lap: <strong>{race.fastest_lap_driver}</strong>
            {race.fastest_lap_time && <span className="text-zinc-500 font-mono ml-1">({race.fastest_lap_time}s)</span>}
          </span>
        )}
      </div>

      {/* Results per final group */}
      {finalGroups.map(final => {
        const group = race.results.filter(r => r.final === final)
        return (
          <div key={final} className="space-y-2">
            <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider">Final {final}</h2>
            <div className="overflow-x-auto scrollbar-thin rounded-lg border border-zinc-800">
              <table className="w-full text-sm">
                <thead className="bg-zinc-900 border-b border-zinc-800">
                  <tr>
                    {['Pos', 'Driver', 'Kart', 'Laps', 'Gap', 'Best Lap', 'Penalty', 'Points'].map(h => (
                      <th key={h} className="px-3 py-2.5 text-left text-xs font-semibold text-zinc-400 uppercase whitespace-nowrap">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {group.map(r => (
                    <tr key={r.driver} className="border-b border-zinc-800/50 hover:bg-zinc-800/40">
                      <td className="px-3 py-2.5">
                        <span className={`inline-block w-7 h-7 rounded text-xs font-bold flex items-center justify-center ${positionColor(r.position)}`}>
                          {r.position}
                        </span>
                      </td>
                      <td className="px-3 py-2.5 font-medium">
                        <Link
                          to={`/drivers/${encodeURIComponent(r.driver)}`}
                          className="hover:text-racing-red transition-colors"
                        >
                          {r.driver}
                        </Link>
                      </td>
                      <td className="px-3 py-2.5 text-zinc-400 font-mono text-xs">{r.kart ?? '—'}</td>
                      <td className="px-3 py-2.5 text-zinc-300 font-mono">{r.laps ?? '—'}</td>
                      <td className="px-3 py-2.5 text-zinc-300 font-mono">
                        {r.gap != null ? `+${r.gap}s` : '—'}
                      </td>
                      <td className={`px-3 py-2.5 font-mono ${r.has_fastest_lap ? 'text-purple-400 font-bold' : 'text-zinc-300'}`}>
                        {r.best_lap != null ? `${r.best_lap}s` : '—'}
                        {r.has_fastest_lap && <span className="ml-1">⚡</span>}
                      </td>
                      <td className={`px-3 py-2.5 font-mono ${r.penalty > 0 ? 'text-red-400' : 'text-zinc-500'}`}>
                        {r.penalty > 0 ? `+${r.penalty}s` : '—'}
                      </td>
                      <td className="px-3 py-2.5 font-bold text-zinc-100">{r.points}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )
      })}
    </div>
  )
}
