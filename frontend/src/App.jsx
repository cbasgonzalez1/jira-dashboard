import { createContext, useContext, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout.jsx'
import Overview from './pages/Overview.jsx'
import Velocity from './pages/Velocity.jsx'
import Burndown from './pages/Burndown.jsx'
import Backlog from './pages/Backlog.jsx'
import TeamLoad from './pages/TeamLoad.jsx'
import SprintDashboard from './pages/SprintDashboard.jsx'

// ── Project context ────────────────────────────────────────────────────────────
const ProjectContext = createContext(null)

export function useProject() {
  return useContext(ProjectContext)
}

const PROJECTS = [
  { key: 'SCRUM', name: 'MDA Portal' },
  { key: 'CRM',   name: 'CRM & Admissions' },
  { key: 'INF',   name: 'Infrastructure' },
]

export default function App() {
  const [project, setProject] = useState('SCRUM')

  return (
    <ProjectContext.Provider value={{ project, setProject, projects: PROJECTS }}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/"          element={<Overview />} />
            <Route path="/velocity"  element={<Velocity />} />
            <Route path="/burndown"  element={<Burndown />} />
            <Route path="/backlog"   element={<Backlog />} />
            <Route path="/team"      element={<TeamLoad />} />
            <Route path="/sprint"    element={<SprintDashboard />} />
            <Route path="*"          element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ProjectContext.Provider>
  )
}
