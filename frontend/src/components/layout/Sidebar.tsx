import { NavLink, useLocation } from 'react-router-dom'
import { useAuthStore, useStoreState, useOfflineStore } from '@/store'
import { useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Package, ShoppingCart, Users, Brain,
  BarChart3, Shield, Wifi, WifiOff, Activity, LogOut, Zap,
} from 'lucide-react'
import clsx from 'clsx'

const NAV = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/inventory', icon: Package, label: 'Inventory' },
  { to: '/queue', icon: ShoppingCart, label: 'Queue & Checkout' },
  { to: '/shoppers', icon: Users, label: 'Shopper Analytics' },
  { to: '/ai-center', icon: Brain, label: 'AI Action Center' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/system', icon: Activity, label: 'System Health' },
  { to: '/demo', icon: Zap, label: 'Judge Demo' },
]

export default function Sidebar() {
  const { user, logout } = useAuthStore()
  const { snapshot } = useStoreState()
  const { networkStatus } = useOfflineStore()
  const navigate = useNavigate()

  const handleLogout = () => { logout(); navigate('/login') }
  const isOffline = networkStatus === 'offline'

  return (
    <aside className="w-64 flex-shrink-0 bg-[#0f1629] border-r border-white/5 flex flex-col h-screen">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="font-bold text-white text-sm tracking-wide">RetailIQ</div>
            <div className="text-xs text-gray-500">AI Retail Platform</div>
          </div>
        </div>
      </div>

      {/* Store status pill */}
      <div className="px-4 py-3 border-b border-white/5">
        <div className={clsx(
          "flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium",
          isOffline
            ? "bg-orange-500/10 border border-orange-500/20 text-orange-400"
            : "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"
        )}>
          {isOffline
            ? <><WifiOff className="w-3.5 h-3.5" /><span>OFFLINE MODE</span></>
            : <><div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" /><span>LIVE — Simulation</span></>
          }
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              isActive ? 'sidebar-link-active' : 'sidebar-link'
            }
          >
            <Icon className="w-4 h-4 flex-shrink-0" />
            <span className="flex-1">{label}</span>
            {label === 'AI Action Center' && (snapshot?.active_recommendations_count ?? 0) > 0 && (
              <span className="ml-auto bg-indigo-600 text-white text-xs px-1.5 py-0.5 rounded-full min-w-[20px] text-center">
                {snapshot?.active_recommendations_count}
              </span>
            )}
            {label === 'Dashboard' && (snapshot?.active_alerts_count ?? 0) > 0 && (
              <span className="ml-auto bg-red-600 text-white text-xs px-1.5 py-0.5 rounded-full">
                {snapshot?.active_alerts_count}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* User + logout */}
      <div className="px-4 py-4 border-t border-white/5">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 bg-indigo-600/30 border border-indigo-500/30 rounded-full flex items-center justify-center text-xs font-bold text-indigo-400">
            {user?.full_name?.[0] ?? user?.username?.[0]?.toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-white truncate">{user?.full_name ?? user?.username}</div>
            <div className="text-xs text-gray-500 capitalize">{user?.role?.replace('_', ' ')}</div>
          </div>
        </div>
        <button onClick={handleLogout} className="w-full btn-ghost justify-center text-xs">
          <LogOut className="w-3.5 h-3.5" />
          Sign out
        </button>
      </div>
    </aside>
  )
}
