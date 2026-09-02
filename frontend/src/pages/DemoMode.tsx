import { useState } from 'react'
import { useStoreState } from '@/store'
import { simulationApi, systemApi } from '@/services/api'
import { toast } from 'react-hot-toast'
import { Zap, Play, WifiOff, Wifi, Users, ShoppingCart, Package, AlertTriangle } from 'lucide-react'
import clsx from 'clsx'

const SCENARIOS = [
  { id: 'normal', label: 'Normal Operation', desc: 'Regular store activity', color: 'emerald', icon: '🏪' },
  { id: 'surge', label: 'Customer Surge', desc: 'Sudden 2.5× footfall spike', color: 'orange', icon: '📈' },
  { id: 'queue', label: 'Queue Congestion', desc: 'High arrival, slow service', color: 'red', icon: '🚶' },
  { id: 'low_stock', label: 'Low Stock Event', desc: '3× demand rate on all SKUs', color: 'yellow', icon: '📦' },
  { id: 'stockout', label: 'Stockout Crisis', desc: '5× demand — multiple items out', color: 'red', icon: '❌' },
  { id: 'staff_shortage', label: 'Staff Shortage', desc: 'High footfall, slow service', color: 'purple', icon: '👤' },
  { id: 'multi', label: 'Multi-Incident (WOW)', desc: 'Surge + Low Stock + Queue', color: 'red', icon: '⚡' },
]

const COLOR_STYLES: Record<string, string> = {
  emerald: 'border-emerald-500/30 bg-emerald-500/5 hover:bg-emerald-500/10',
  orange: 'border-orange-500/30 bg-orange-500/5 hover:bg-orange-500/10',
  red: 'border-red-500/30 bg-red-500/5 hover:bg-red-500/10',
  yellow: 'border-yellow-500/30 bg-yellow-500/5 hover:bg-yellow-500/10',
  purple: 'border-purple-500/30 bg-purple-500/5 hover:bg-purple-500/10',
  blue: 'border-blue-500/30 bg-blue-500/5 hover:bg-blue-500/10',
}

export default function DemoMode() {
  const { snapshot } = useStoreState()
  const [activeScenario, setActiveScenario] = useState('normal')
  const [loading, setLoading] = useState<string | null>(null)
  const [isOffline, setIsOffline] = useState(false)

  const activateScenario = async (scenario: string) => {
    setLoading(scenario)
    try {
      await simulationApi.setScenario(scenario)
      setActiveScenario(scenario)
      const s = SCENARIOS.find(s => s.id === scenario)
      toast.success(`🎬 Scenario: ${s?.label}`)
    } catch {
      toast.error('Failed to activate scenario')
    } finally {
      setLoading(null)
    }
  }

  const toggleOffline = async () => {
    setLoading('offline')
    try {
      if (isOffline) {
        await systemApi.goOnline()
        setIsOffline(false)
        toast.success('↑ Network restored — syncing events...')
      } else {
        await systemApi.goOffline()
        setIsOffline(true)
        toast('⚠ Network disconnected. AI continues locally.', { icon: '📴' })
      }
    } catch {
      toast.error('Failed')
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Hero */}
      <div className="gradient-border">
        <div className="bg-[#0f1629] rounded-xl p-6 text-center">
          <div className="w-12 h-12 bg-indigo-600/30 border border-indigo-500/30 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Zap className="w-6 h-6 text-indigo-400" />
          </div>
          <h2 className="text-xl font-bold text-white">Judge Demo Mode</h2>
          <p className="text-gray-400 text-sm mt-1">One-click scenario activation for live demonstration</p>
          <p className="text-xs text-gray-600 mt-1">Smart India Hackathon 2026 · Problem Statement 179</p>
        </div>
      </div>

      {/* Live KPIs */}
      {snapshot && (
        <div className="grid grid-cols-4 gap-3">
          <div className="card-sm text-center">
            <p className="text-2xl font-bold text-indigo-400">{snapshot.current_footfall}</p>
            <p className="text-xs text-gray-500 mt-0.5">Current Footfall</p>
          </div>
          <div className="card-sm text-center">
            <p className="text-2xl font-bold text-yellow-400">{snapshot.total_queue_length}</p>
            <p className="text-xs text-gray-500 mt-0.5">Total Queue</p>
          </div>
          <div className="card-sm text-center">
            <p className="text-2xl font-bold text-orange-400">{snapshot.low_stock_count}</p>
            <p className="text-xs text-gray-500 mt-0.5">Low Stock</p>
          </div>
          <div className="card-sm text-center">
            <p className="text-2xl font-bold text-red-400">{snapshot.active_alerts_count}</p>
            <p className="text-xs text-gray-500 mt-0.5">Active Alerts</p>
          </div>
        </div>
      )}

      {/* Scenario Launcher */}
      <div className="card">
        <p className="section-title">Scenario Launcher</p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {SCENARIOS.map(s => (
            <button
              key={s.id}
              onClick={() => activateScenario(s.id)}
              disabled={loading === s.id}
              className={clsx(
                "p-4 rounded-xl border text-left transition-all duration-200",
                activeScenario === s.id
                  ? 'ring-2 ring-indigo-500 border-indigo-500/50 bg-indigo-500/10'
                  : COLOR_STYLES[s.color] ?? COLOR_STYLES.blue,
              )}
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl">{s.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-white text-sm">{s.label}</span>
                    {activeScenario === s.id && (
                      <span className="text-xs text-indigo-400 flex items-center gap-1">
                        <Play className="w-2.5 h-2.5" />ACTIVE
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">{s.desc}</p>
                </div>
                {loading === s.id && (
                  <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin flex-shrink-0" />
                )}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Offline Mode Control */}
      <div className="card">
        <p className="section-title">Offline Mode Simulation</p>
        <div className="flex items-center gap-6">
          <div className="flex-1">
            <h3 className="font-semibold text-white mb-1">
              {isOffline ? '⚠ Network Disconnected' : '✓ Network Connected'}
            </h3>
            <p className="text-sm text-gray-400">
              {isOffline
                ? 'AI Decision Engine continues locally. Events buffered for sync.'
                : 'Click to simulate internet failure. Dashboard continues, AI continues, events queue locally.'}
            </p>
          </div>
          <button
            onClick={toggleOffline}
            disabled={loading === 'offline'}
            className={clsx("btn min-w-[160px] justify-center",
              isOffline ? 'btn-success' : 'btn-danger'
            )}
          >
            {loading === 'offline'
              ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              : isOffline
                ? <><Wifi className="w-4 h-4" />Restore Network</>
                : <><WifiOff className="w-4 h-4" />Simulate Failure</>
            }
          </button>
        </div>
      </div>

      {/* WOW moment script */}
      <div className="card border border-indigo-500/20">
        <p className="section-title">🎯 Recommended Demo Flow (for judges)</p>
        <ol className="space-y-2 text-sm text-gray-300">
          {[
            'Start with "Normal Operation" — show baseline metrics on dashboard',
            'Activate "Multi-Incident (WOW)" — watch footfall surge, queue grow, stock deplete',
            'AI recommendations appear automatically (right panel of Dashboard)',
            'Open AI Action Center — show evidence + reasoning for each recommendation',
            'Accept "Open Checkout 4" — watch queue metrics improve in real-time',
            'Accept "Restock" recommendation — watch inventory recover',
            'Click "Simulate Failure" — dashboard stays live in OFFLINE MODE',
            'Click "Restore Network" — watch sync counter and confirmation message',
          ].map((step, i) => (
            <li key={i} className="flex items-start gap-3">
              <span className="w-6 h-6 bg-indigo-600/30 text-indigo-400 rounded-full text-xs flex items-center justify-center flex-shrink-0 font-bold">
                {i + 1}
              </span>
              {step}
            </li>
          ))}
        </ol>
      </div>
    </div>
  )
}
