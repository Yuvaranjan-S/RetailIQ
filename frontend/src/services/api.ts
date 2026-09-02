import axios from 'axios'
import { useAuthStore } from '@/store'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// Auto-attach JWT
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-logout on 401
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ─── Auth ────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }).then((r) => r.data),
  me: () => api.get('/auth/me').then((r) => r.data),
}

// ─── Store State ─────────────────────────────────────────────────────────────
export const storeApi = {
  getState: (storeId = 1) => api.get(`/store/state?store_id=${storeId}`).then((r) => r.data),
  getZones: (storeId = 1) => api.get(`/store/zones?store_id=${storeId}`).then((r) => r.data),
  getCheckouts: (storeId = 1) => api.get(`/store/checkouts?store_id=${storeId}`).then((r) => r.data),
}

// ─── Inventory ────────────────────────────────────────────────────────────────
export const inventoryApi = {
  getAll: (storeId = 1, status?: string) =>
    api.get(`/inventory?store_id=${storeId}${status ? `&status=${status}` : ''}`).then((r) => r.data),
  getAlerts: (storeId = 1) => api.get(`/inventory/alerts?store_id=${storeId}`).then((r) => r.data),
  restock: (sku: string, quantity: number, storeId = 1) =>
    api.post(`/inventory/${sku}/restock?quantity=${quantity}&store_id=${storeId}`).then((r) => r.data),
}

// ─── Alerts ───────────────────────────────────────────────────────────────────
export const alertsApi = {
  getAll: (storeId = 1, status?: string) =>
    api.get(`/alerts?store_id=${storeId}${status ? `&status=${status}` : ''}`).then((r) => r.data),
  resolve: (id: number) => api.put(`/alerts/${id}/resolve`).then((r) => r.data),
  acknowledge: (id: number) => api.put(`/alerts/${id}/acknowledge`).then((r) => r.data),
}

// ─── Recommendations ──────────────────────────────────────────────────────────
export const recommendationsApi = {
  getAll: (storeId = 1, status = 'pending') =>
    api.get(`/recommendations?store_id=${storeId}&status=${status}`).then((r) => r.data),
  accept: (id: number, notes?: string) =>
    api.post(`/recommendations/${id}/accept`, { notes }).then((r) => r.data),
  reject: (id: number, notes?: string) =>
    api.post(`/recommendations/${id}/reject`, { notes }).then((r) => r.data),
  getResult: (id: number) => api.get(`/recommendations/${id}/result`).then((r) => r.data),
  getOutcomes: (storeId = 1) =>
    api.get(`/recommendations/history/outcomes?store_id=${storeId}`).then((r) => r.data),
}

// ─── Analytics ────────────────────────────────────────────────────────────────
export const analyticsApi = {
  footfall: (storeId = 1, range = '24h') =>
    api.get(`/analytics/footfall?store_id=${storeId}&range=${range}`).then((r) => r.data),
  heatmap: (storeId = 1) => api.get(`/analytics/heatmap?store_id=${storeId}`).then((r) => r.data),
  queueTrends: (storeId = 1) => api.get(`/analytics/queue-trends?store_id=${storeId}`).then((r) => r.data),
  aiPerformance: (storeId = 1) => api.get(`/analytics/ai-performance?store_id=${storeId}`).then((r) => r.data),
  overview: (storeId = 1) => api.get(`/analytics/store-overview?store_id=${storeId}`).then((r) => r.data),
}

// ─── Simulation ───────────────────────────────────────────────────────────────
export const simulationApi = {
  setScenario: (scenario: string, storeId = 1) =>
    api.post('/simulation/scenario', { scenario, store_id: storeId }).then((r) => r.data),
  getStatus: () => api.get('/simulation/status').then((r) => r.data),
}

// ─── System ───────────────────────────────────────────────────────────────────
export const systemApi = {
  health: (storeId = 1) => api.get(`/system/health?store_id=${storeId}`).then((r) => r.data),
  goOffline: (storeId = 1) => api.post(`/system/offline?store_id=${storeId}`).then((r) => r.data),
  goOnline: (storeId = 1) => api.post(`/system/online?store_id=${storeId}`).then((r) => r.data),
}

export default api
