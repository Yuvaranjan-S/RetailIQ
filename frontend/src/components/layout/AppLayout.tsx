import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import TopBar from './TopBar'
import { useWebSocket } from '@/services/websocket'
import { Toaster } from 'react-hot-toast'

export default function AppLayout() {
  useWebSocket(1) // Connect WebSocket for store 1

  return (
    <div className="flex h-screen overflow-hidden bg-[#0a0e1a]">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: { background: '#141d36', color: '#f3f4f6', border: '1px solid rgba(255,255,255,0.1)' },
        }}
      />
    </div>
  )
}
