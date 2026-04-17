/** Build a lookup: raceName → driverName → { has_fastest_lap, penalty } */
export function buildRaceMeta(racesData) {
  if (!racesData) return {}
  return Object.fromEntries(
    racesData.races.map(race => [
      race.name,
      Object.fromEntries(
        race.results.map(r => [r.driver, { has_fastest_lap: r.has_fastest_lap, penalty: r.penalty }])
      ),
    ])
  )
}

/**
 * Compute each driver's championship position after the penultimate race.
 * Returns { driverName: position } or {} if fewer than 2 races.
 */
export function computePreviousPositions(standings) {
  if (!standings || standings.races.length < 2) return {}
  const prevRaces = standings.races.slice(0, -1)
  const totals = standings.standings
    .map(s => ({ driver: s.driver, pts: prevRaces.reduce((n, r) => n + (s.race_points[r] || 0), 0) }))
    .sort((a, b) => b.pts - a.pts)
  return Object.fromEntries(totals.map((s, i) => [s.driver, i + 1]))
}

/** Podium CSS classes for table rows */
export function podiumClass(position) {
  if (position === 1) return 'bg-yellow-500/10 border-l-2 border-yellow-500'
  if (position === 2) return 'bg-zinc-400/10 border-l-2 border-zinc-400'
  if (position === 3) return 'bg-amber-700/10 border-l-2 border-amber-700'
  return ''
}

/** Colour for a finishing position (used in heatmap and badges) */
export function positionColor(pos) {
  if (!pos) return 'bg-zinc-800 text-zinc-500'
  if (pos === 1)  return 'bg-yellow-500 text-black'
  if (pos === 2)  return 'bg-zinc-400 text-black'
  if (pos === 3)  return 'bg-amber-600 text-black'
  if (pos <= 10)  return 'bg-emerald-700 text-white'
  return 'bg-zinc-700 text-zinc-300'
}

/** CHART_COLORS – distinct palette for multi-driver charts */
export const CHART_COLORS = [
  '#e63946', '#2196f3', '#4caf50', '#ff9800', '#9c27b0',
  '#00bcd4', '#ff5722', '#8bc34a', '#673ab7', '#f06292',
  '#26a69a', '#ffd54f', '#ef5350', '#42a5f5', '#66bb6a',
]
