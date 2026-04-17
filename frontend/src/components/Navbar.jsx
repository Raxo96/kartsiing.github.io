import { NavLink } from 'react-router-dom'
import { useTheme } from '../contexts/ThemeContext'

const links = [
  { to: '/',        label: 'Standings' },
  { to: '/races',   label: 'Races'     },
  { to: '/charts',  label: 'Charts'    },
]

export default function Navbar() {
  const { dark, toggle } = useTheme()

  return (
    <header className="sticky top-0 z-50 bg-zinc-900/90 backdrop-blur border-b border-zinc-800">
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-14">

        {/* Brand */}
        <span className="font-bold text-lg tracking-tight">
          <span className="text-racing-red">🏁</span>
          <span className="ml-2 text-zinc-100">Kart Cup</span>
          <span className="ml-1 text-zinc-500 text-sm font-normal">2026</span>
        </span>

        {/* Nav links */}
        <nav className="flex gap-1">
          {links.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-zinc-700 text-zinc-100'
                    : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Theme toggle */}
        <button
          onClick={toggle}
          className="text-zinc-400 hover:text-zinc-100 transition-colors text-lg"
          aria-label="Toggle theme"
        >
          {dark ? '☀️' : '🌙'}
        </button>
      </div>
    </header>
  )
}
