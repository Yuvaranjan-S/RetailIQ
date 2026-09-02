import { Bell, RefreshCw, Wifi, WifiOff } from 'lucide-react'
import { useStoreState, useOfflineStore } from '@/store'
import { useLocation } from 'react-router-dom'
import clsx from 'clsx'

const PAGE_TITLES: Record<string, string> = {
  '/': 'Store Command Center',
  '/inventory': 'Inventory Intelligence',
  '/queue': 'Queue & Checkout Management',
  '/shoppers': 'Shopper Analytics',
  '/ai-center': 'AI Action Center',
  '/analytics': 'Analytics Hub',
  '/system': 'System Health',
  '/demo': 'Judge Demo Mode',
}

export default function TopBar() {
  const location = useLocation()
  const { snapshot } = useStoreState()
  const { networkStatus, isSyncing, lastSyncMessage, pendingSyncCount } = useOfflineStore()
  const title = PAGE_TITLES[location.pathname] ?? 'RetailIQ'
  const isOffline = networkStatus === 'offline'

  return (
    <header className="h-14 bg-[#0f1629]/80 backdrop-blur border-b border-white/5 flex items-center justify-between px-6 sticky top-0 z-40">
      <div>
        <h1 className="text-sm font-semibold text-white">{title}</h1>
        {snapshot && (
          <p className="text-xs text-gray-500">
            {snapshot.store_name} · Last updated {new Date(snapshot.timestamp).toLocaleTimeString()}
          </p>
        )}
      </div>

      <div className="flex items-center gap-3">
        {/* Sync message */}
        {lastSyncMessage && (
          <div className={clsx(
            "text-xs px-3 py-1.5 rounded-full flex items-center gap-1.5 animate-fade-in",
            isSyncing ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                      : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
          )}>
            {isSyncing && <RefreshCw className="w-3 h-3 animate-spin" />}
            <span>{lastSyncMessage}</span>
          </div>
        )}

        {/* Network status */}
        <div className={clsx(
          "flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border",
          isOffline
            ? "bg-orange-500/10 text-orange-400 border-orange-500/20"
            : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
        )}>
          {isOffline ? <WifiOff className="w-3.5 h-3.5" /> : <Wifi className="w-3.5 h-3.5" />}
          <span>{isOffline ? `OFFLINE · ${pendingSyncCount} queued` : 'ONLINE'}</span>
        </div>

        {/* Alert bell */}
        <button className="relative p-2 rounded-lg hover:bg-white/5 transition-colors">
          <Bell className="w-4 h-4 text-gray-400" />
          {(snapshot?.active_alerts_count ?? 0) > 0 && (
            <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center leading-none">
              {snapshot?.active_alerts_count}
            </span>
          )}
        </button>
      </div>
    </header>
  )
}
