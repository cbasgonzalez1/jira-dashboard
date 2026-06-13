import { createContext, useContext, useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import Layout from './components/layout/Layout.jsx'
import Overview from './pages/Overview.jsx'
import Velocity from './pages/Velocity.jsx'
import Burndown from './pages/Burndown.jsx'
import Backlog from './pages/Backlog.jsx'
import TeamLoad from './pages/TeamLoad.jsx'
import SprintDashboard from './pages/SprintDashboard.jsx'
import { getSprintProjects } from './api/jiraApi.js'

// ── Project context ────────────────────────────────────────────────────────────
const ProjectContext = createContext(null)

export function useProject() {
  return useContext(ProjectContext)
}

const FALLBACK_PROJECT = 'DEVOPSSP'

export default function App() {
  const [project, setProject] = useState(FALLBACK_PROJECT)

  const projectsQ = useQuery({
    queryKey: ['app-projects'],
    queryFn: () => getSprintProjects().then(r => r.data),
    staleTime: 5 * 60_000,
  })

  const projects = projectsQ.data ?? [{ key: FALLBACK_PROJECT, name: FALLBACK_PROJECT }]

  // Switch to first accessible project if current one is not in the list
  useEffect(() => {
    if (projectsQ.data?.length > 0 && !projectsQ.data.find(p => p.key === project)) {
      setProject(projectsQ.data[0].key)
    }
  }, [projectsQ.data])

  return (
    <ProjectContext.Provider value={{ project, setProject, projects }}>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
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
