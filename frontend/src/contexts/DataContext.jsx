import { createContext, useContext, useState, useEffect } from 'react'

const DataContext = createContext(null)

export function DataProvider({ children }) {
  const [standings, setStandings]   = useState(null)
  const [races,     setRaces]       = useState(null)
  const [drivers,   setDrivers]     = useState(null)
  const [stats,     setStats]       = useState(null)
  const [loading,   setLoading]     = useState(true)
  const [error,     setError]       = useState(null)

  useEffect(() => {
    const base = import.meta.env.BASE_URL
    Promise.all([
      fetch(`${base}data/standings.json`).then(r => r.json()),
      fetch(`${base}data/races.json`).then(r => r.json()),
      fetch(`${base}data/drivers.json`).then(r => r.json()),
      fetch(`${base}data/season_stats.json`).then(r => r.json()),
    ])
      .then(([s, r, d, st]) => {
        setStandings(s)
        setRaces(r)
        setDrivers(d)
        setStats(st)
        setLoading(false)
      })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [])

  return (
    <DataContext.Provider value={{ standings, races, drivers, stats, loading, error }}>
      {children}
    </DataContext.Provider>
  )
}

export const useAppData = () => useContext(DataContext)
