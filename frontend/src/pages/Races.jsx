import { Link } from 'react-router-dom'
import { useAppData } from '../contexts/DataContext'
import LoadingSpinner from '../components/LoadingSpinner'

function RaceCard({ race }) {
  const winner = race.results.find(r => r.position === 1)
  const p2     = race.results.find(r => r.position === 2)
  const p3     = race.results.find(r => r.position === 3)

  return (
    <Link
      to={`/races/${encodeURIComponent(race.name)}`}
      className="block bg-zinc-900 border border-zinc-800 rounded-xl p-5 hover:border-zinc-600
                 hover:bg-zinc-800/60 transition-all group"
    >
      <div className="flex items-start justify-between mb-4">
        <h2 className="text-lg font-bold text-zinc-100 group-hover:text-white">{race.name}</h2>
        <span className="text-xs text-zinc-500 bg-zinc-800 px-2 py-0.5 rounded">
          {race.results.length} drivers
        </span>
      </div>

      {/* Podium */}
      <div className="space-y-1.5 mb-4">
        {[{ r: winner, medal: '🥇', cls: 'text-yellow-400' },
          { r: p2,     medal: '🥈', cls: 'text-zinc-400'   },
          { r: p3,     medal: '🥉', cls: 'text-amber-600'  }].map(({ r, medal, cls }) =>
          r && (
            <div key={r.driver} className="flex items-center gap-2 text-sm">
              <span>{medal}</span>
              <span className={`font-semibold ${cls}`}>{r.driver}</span>
              <span className="text-zinc-500 ml-auto font-mono">{r.points} pts</span>
            </div>
          )
        )}
      </div>

      {/* FL */}
      {race.fastest_lap_driver && (
        <div className="flex items-center gap-1.5 text-xs text-purple-400 border-t border-zinc-800 pt-3">
          <span>⚡</span>
          <span>{race.fastest_lap_driver}</span>
          {race.fastest_lap_time && (
            <span className="text-zinc-500 ml-auto font-mono">{race.fastest_lap_time}s</span>
          )}
        </div>
      )}
    </Link>
  )
}

export default function Races() {
  const { races, loading, error } = useAppData()

  if (loading) return <LoadingSpinner />
  if (error)   return <p className="text-red-400 text-center py-12">Failed to load data: {error}</p>

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Race Results</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {races.races.map(race => <RaceCard key={race.name} race={race} />)}
      </div>
    </div>
  )
}
