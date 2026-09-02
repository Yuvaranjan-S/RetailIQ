import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from './store'
import AppLayout from './components/layout/AppLayout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Inventory from './pages/Inventory'
import Queue from './pages/Queue'
import ShopperAnalytics from './pages/ShopperAnalytics'
import AIActionCenter from './pages/AIActionCenter'
import Analytics from './pages/Analytics'
import SystemHealth from './pages/SystemHealth'
import DemoMode from './pages/DemoMode'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
})

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <RequireAuth>
                <AppLayout />
              </RequireAuth>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="inventory" element={<Inventory />} />
            <Route path="queue" element={<Queue />} />
            <Route path="shoppers" element={<ShopperAnalytics />} />
            <Route path="ai-center" element={<AIActionCenter />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="system" element={<SystemHealth />} />
            <Route path="demo" element={<DemoMode />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
