import { HashRouter, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './contexts/ThemeContext'
import { DataProvider } from './contexts/DataContext'
import Layout from './components/Layout'
import Standings   from './pages/Standings'
import Races       from './pages/Races'
import RaceDetail  from './pages/RaceDetail'
import DriverDetail from './pages/DriverDetail'
import Charts      from './pages/Charts'

export default function App() {
  return (
    <ThemeProvider>
      <DataProvider>
        <HashRouter>
          <Layout>
            <Routes>
              <Route path="/"                  element={<Standings />} />
              <Route path="/races"             element={<Races />} />
              <Route path="/races/:name"       element={<RaceDetail />} />
              <Route path="/drivers/:name"     element={<DriverDetail />} />
              <Route path="/charts"            element={<Charts />} />
            </Routes>
          </Layout>
        </HashRouter>
      </DataProvider>
    </ThemeProvider>
  )
}
