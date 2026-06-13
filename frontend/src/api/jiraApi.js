import axios from 'axios'

const API = axios.create({
  baseURL: '',
  timeout: 30_000,
})

export const getProjects       = ()                     => API.get('/api/projects')
export const getOverview       = ()                     => API.get('/api/overview')
export const getVelocity       = (project)              => API.get(`/api/velocity/${project}`)
export const getBurndown       = (project)              => API.get(`/api/burndown/${project}`)
export const getBacklog        = (project)              => API.get(`/api/backlog/${project}`)
export const getTeam           = (project)              => API.get(`/api/team/${project}`)
export const getSprintProjects = ()                     => API.get('/api/sprint-dashboard/projects')
export const getSprintBoards   = (projectKey = null)    => API.get('/api/sprint-dashboard/boards', { params: projectKey ? { project_key: projectKey } : undefined })
export const getSprintSprints  = (boardId)              => API.get(`/api/sprint-dashboard/sprints/${boardId}`)
export const getSprintData     = (boardId, sprintId)    => API.get('/api/sprint-dashboard/data', { params: { board_id: boardId, sprint_id: sprintId } })
