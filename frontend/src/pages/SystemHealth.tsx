import { useState, useEffect } from 'react'
import { systemApi, simulationApi } from '@/services/api'
import { useOfflineStore } from '@/store'
import { systemApi as sApi } from '@/services/api'
import { Activity, Database, Wifi, WifiOff, Camera, Brain, Server, RefreshCw } from 'lucide-react'
import clsx from 'clsx'
import { toast } from 'react-hot-toast'

export default function SystemHealth() {
  const [health, setHealth] = useState<any>(null)
  const { networkStatus } = useOfflineStore()
  const [isOffline, setIsOffline] = useState(false)
  const [loading, setLoading] = useState(false)

  const load = async () => {
    try {
      const h = await systemApi.health()
      setHealth(h)
      setIsOffline(h.network_status === 'offline')
    } catch { }
  }

  useEffect(() => { load(); const t = setInterval(load, 5000); return () => clearInterval(t) }, [])

  const toggleNetwork = async () => {
    setLoading(true)
    try {
      if (isOffline) {
        await sApi.goOnline()
        setIsOffline(false)
        toast.success('↑ Network restored')
      } else {
        await sApi.goOffline()
        setIsOffline(true)
        toast('⚠ Offline mode activated', { icon: '📴' })
      }
      await load()
    } catch { toast.error('Failed') } finally { setLoading(false) }
  }

  const StatusRow = ({ icon: Icon, label, status, detail }: any) => {
    const isGood = ['online', 'healthy', 'running', 'simulation'].includes(status)
    const isWarn = ['degraded', 'idle'].includes(status)
    return (
      <div className="flex items-center gap-4 p-4 rounded-xl bg-white/3 border border-white/5">
        <div className={clsx("w-10 h-10 rounded-xl flex items-center justify-center",
          isGood ? 'bg-emerald-500/20 text-emerald-400' :
          isWarn ? 'bg-yellow-500/20 text-yellow-400' :
          'bg-red-500/20 text-red-400')}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium text-white">{label}</p>
          {detail && <p className="text-xs text-gray-500 mt-0.5">{detail}</p>}
        </div>
        <div className={clsx("flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full border",
          isGood ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
          isWarn ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
          'bg-red-500/10 text-red-400 border-red-500/20')}>
          <div className={clsx("w-1.5 h-1.5 rounded-full", isGood ? 'bg-emerald-400 animate-pulse' : isWarn ? 'bg-yellow-400' : 'bg-red-400')} />
          {status.toUpperCase()}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-white">System Health</h2>
        <button onClick={load} className="btn-ghost text-xs">
          <RefreshCw className="w-3.5 h-3.5" />Refresh
        </button>
      </div>

      {health && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="card text-center">
              <p className="text-2xl font-bold text-indigo-400">{health.active_connections}</p>
              <p className="kpi-label mt-1">WS Connections</p>
            </div>
            <div className="card text-center">
              <p className="text-2xl font-bold text-emerald-400">{health.footfall}</p>
              <p className="kpi-label mt-1">Current Footfall</p>
            </div>
            <div className="card text-center">
              <p className="text-2xl font-bold text-yellow-400">{health.pending_sync_count}</p>
              <p className="kpi-label mt-1">Pending Sync</p>
            </div>
            <div className="card text-center">
              <p className="text-2xl font-bold text-gray-400">
                {health.simulation_mode ? 'SIM' : 'LIVE'}
              </p>
              <p className="kpi-label mt-1">Camera Mode</p>
            </div>
          </div>

          <div className="card space-y-3">
            <p className="section-title">Component Status</p>
            <StatusRow icon={Camera} label="Camera / Edge Pipeline"
              status={health.camera_status}
              detail={health.simulation_mode ? 'Running in simulation mode' : 'Real camera feed'} />
            <StatusRow icon={Brain} label="AI Decision Engine"
              status={health.ai_status}
              detail="Rule engine + signal fusion running" />
            <StatusRow icon={Database} label="Database"
              status={health.db_status}
              detail="PostgreSQL primary database" />
            <StatusRow icon={Wifi} label="Network / Sync"
              status={health.network_status}
              detail={health.network_status === 'offline' ? `${health.pending_sync_count} events queued locally` : 'Events syncing normally'} />
          </div>

          {/* Offline mode control */}
          <div className="card">
            <p className="section-title">Offline Mode Simulation</p>
            <div className="flex items-center gap-6">
              <div className="flex-1">
                <p className="font-medium text-white">
                  {isOffline ? '⚠ Network Disconnected' : '✓ Network Connected'}
                </p>
                <p className="text-sm text-gray-400 mt-1">
                  {isOffline
                    ? 'Events are being stored locally. AI decision engine continues operating independently.'
                    : 'Simulate internet failure to demonstrate edge-first, offline-capable operation.'}
                </p>
              </div>
              <button onClick={toggleNetwork} disabled={loading}
                className={clsx("btn min-w-[160px] justify-center",
                  isOffline ? 'btn-success' : 'btn-danger')}>
                {loading
                  ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  : isOffline
                    ? <><Wifi className="w-4 h-4" />Restore Network</>
                    : <><WifiOff className="w-4 h-4" />Simulate Failure</>
                }
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
