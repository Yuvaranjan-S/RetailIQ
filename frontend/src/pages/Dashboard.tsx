import { useStoreState } from '@/store'
import { Users, ShoppingCart, Package, AlertTriangle, Brain, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { AreaChart, Area, ResponsiveContainer, Tooltip, XAxis, BarChart, Bar } from 'recharts'
import RecommendationsPanel from '@/components/dashboard/RecommendationsPanel'
import StoreMap from '@/components/dashboard/StoreMap'
import clsx from 'clsx'
import type { CheckoutState, InventoryItem } from '@/types'

// ─── KPI Card ────────────────────────────────────────────────────────────────
function KpiCard({ label, value, sub, icon: Icon, color, trend }: {
  label: string; value: string | number; sub?: string
  icon: any; color: string; trend?: 'up' | 'down' | 'neutral'
}) {
  return (
    <div className={clsx("kpi-card hover:border-white/10 transition-colors", color)}>
      <div className="flex items-start justify-between">
        <div>
          <p className="kpi-label">{label}</p>
          <p className="kpi-value">{value}</p>
          {sub && <p className="text-xs text-gray-500 mt-0.5">{sub}</p>}
        </div>
        <div className={clsx("p-2.5 rounded-xl", color.replace('glow', 'bg'))}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      {trend && (
        <div className={clsx(
          "mt-2 text-xs flex items-center gap-1",
          trend === 'up' ? 'text-emerald-400' : trend === 'down' ? 'text-red-400' : 'text-gray-500'
        )}>
          {trend === 'up' ? <TrendingUp className="w-3 h-3" /> :
           trend === 'down' ? <TrendingDown className="w-3 h-3" /> :
           <Minus className="w-3 h-3" />}
          <span>{trend === 'up' ? 'Increasing' : trend === 'down' ? 'Decreasing' : 'Stable'}</span>
        </div>
      )}
    </div>
  )
}

// ─── Queue card ───────────────────────────────────────────────────────────────
function QueueCard({ checkout }: { checkout: CheckoutState }) {
  const statusColors: Record<string, string> = {
    normal: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    busy: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
    critical: 'text-red-400 bg-red-500/10 border-red-500/20',
    closed: 'text-gray-500 bg-gray-500/10 border-gray-500/20',
  }
  const barWidth = checkout.is_open ? Math.min(100, (checkout.queue_length / 15) * 100) : 0

  return (
    <div className="card-sm">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-white">{checkout.name}</span>
        <span className={clsx("badge border", statusColors[checkout.status])}>
          {checkout.status.toUpperCase()}
        </span>
      </div>
      <div className="flex items-baseline gap-2 mb-2">
        <span className="text-2xl font-bold text-white">{checkout.queue_length}</span>
        <span className="text-xs text-gray-500">in queue</span>
        {checkout.is_open && (
          <span className="ml-auto text-xs text-gray-400">
            ~{checkout.estimated_wait_minutes?.toFixed(1) ?? '0.0'} min wait
          </span>
        )}
      </div>
      <div className="w-full bg-white/5 rounded-full h-1.5">
        <div
          className={clsx("h-1.5 rounded-full transition-all duration-700",
            barWidth > 70 ? 'bg-red-500' : barWidth > 40 ? 'bg-yellow-500' : 'bg-emerald-500'
          )}
          style={{ width: `${barWidth}%` }}
        />
      </div>
    </div>
  )
}

// ─── Inventory alert row ──────────────────────────────────────────────────────
function InventoryRow({ item }: { item: InventoryItem }) {
  const statusColors: Record<string, string> = {
    ok: 'bg-emerald-500', low: 'bg-yellow-500', critical: 'bg-orange-500', out: 'bg-red-500',
  }
  return (
    <div className="flex items-center gap-3 py-2 border-b border-white/5 last:border-0">
      <div className={clsx("w-2 h-2 rounded-full flex-shrink-0", statusColors[item.stock_status])} />
      <span className="flex-1 text-sm text-gray-300 truncate">{item.product_name}</span>
      <span className="text-sm font-mono text-white">{item.current_stock.toFixed(0)}</span>
      <span className="text-xs text-gray-600">/ {item.max_stock}</span>
    </div>
  )
}

// ─── Dashboard ────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const { snapshot } = useStoreState()

  if (!snapshot) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500 text-sm">Connecting to store digital twin...</p>
        </div>
      </div>
    )
  }

  const footfallData = snapshot.footfall_history.slice(-30).map((p, i) => ({
    i, v: p.count
  }))
  const queueData = snapshot.queue_history.slice(-30).map((p, i) => ({
    i, v: p.total_queue
  }))

  const criticalInventory = snapshot.inventory
    .filter(i => i.stock_status !== 'ok')
    .sort((a, b) => (a.stock_percentage ?? 0) - (b.stock_percentage ?? 0))
    .slice(0, 6)

  const queueTrend = snapshot.total_queue_length > 8 ? 'up' :
                     snapshot.total_queue_length < 3 ? 'down' : 'neutral'

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Simulation mode banner */}
      {snapshot.simulation_mode && (
        <div className="bg-indigo-600/10 border border-indigo-500/20 rounded-xl px-4 py-2.5 flex items-center gap-3">
          <div className="w-2 h-2 bg-indigo-400 rounded-full animate-pulse" />
          <span className="text-indigo-300 text-xs font-medium">
            SIMULATION MODE — Realistic store events generated. Switch to REAL CAMERA MODE when hardware is available.
          </span>
        </div>
      )}

      {/* KPI Row */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <KpiCard
          label="Current Footfall"
          value={snapshot.current_footfall}
          sub={`${snapshot.total_customers_today} today`}
          icon={Users}
          color="text-indigo-400"
          trend={snapshot.current_footfall > 40 ? 'up' : 'neutral'}
        />
        <KpiCard
          label="Queue Length"
          value={snapshot.total_queue_length}
          sub={`${snapshot.open_checkouts} checkouts open`}
          icon={ShoppingCart}
          color="text-yellow-400"
          trend={queueTrend}
        />
        <KpiCard
          label="Low Stock Items"
          value={snapshot.low_stock_count}
          sub={`${snapshot.out_of_stock_count} out of stock`}
          icon={Package}
          color={snapshot.out_of_stock_count > 0 ? "text-red-400" : "text-orange-400"}
          trend={snapshot.low_stock_count > 3 ? 'up' : 'neutral'}
        />
        <KpiCard
          label="Active Alerts"
          value={snapshot.active_alerts_count}
          sub={`${snapshot.available_staff} staff available`}
          icon={AlertTriangle}
          color={snapshot.active_alerts_count > 3 ? "text-red-400" : "text-emerald-400"}
        />
      </div>

      {/* Main 3-column grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

        {/* Left: Store Map + Zone breakdown */}
        <div className="xl:col-span-2 space-y-4">
          <StoreMap zones={snapshot.zones} />

          {/* Footfall sparkline */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <p className="section-title mb-0">Footfall Trend</p>
              <span className="text-xs text-gray-500">Last 30 readings</span>
            </div>
            <ResponsiveContainer width="100%" height={80}>
              <AreaChart data={footfallData}>
                <defs>
                  <linearGradient id="footfall-gradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <Tooltip
                  contentStyle={{ background: '#141d36', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 11 }}
                  labelFormatter={() => ''}
                  formatter={(v: any) => [v, 'People']}
                />
                <Area type="monotone" dataKey="v" stroke="#6366f1" fill="url(#footfall-gradient)" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Checkout queue grid */}
          <div className="card">
            <p className="section-title">Checkout Status</p>
            <div className="grid grid-cols-2 gap-3">
              {snapshot.checkouts.map(c => <QueueCard key={c.id} checkout={c} />)}
            </div>
          </div>
        </div>

        {/* Right: AI Recommendations */}
        <div className="space-y-4">
          <RecommendationsPanel />

          {/* Inventory alerts */}
          <div className="card">
            <div className="flex items-center justify-between mb-3">
              <p className="section-title mb-0">Inventory Alerts</p>
              <span className="badge-high">{criticalInventory.length} items</span>
            </div>
            {criticalInventory.length === 0 ? (
              <p className="text-xs text-gray-600 text-center py-4">All stock levels healthy ✓</p>
            ) : (
              <div>
                {criticalInventory.map(item => <InventoryRow key={item.id} item={item} />)}
              </div>
            )}
          </div>

          {/* Queue trend sparkline */}
          <div className="card">
            <div className="flex items-center justify-between mb-3">
              <p className="section-title mb-0">Queue Trend</p>
              <span className="text-xs text-gray-500">{snapshot.avg_wait_seconds.toFixed(0)}s avg wait</span>
            </div>
            <ResponsiveContainer width="100%" height={60}>
              <BarChart data={queueData}>
                <Bar dataKey="v" fill="#f59e0b" radius={[2, 2, 0, 0]} maxBarSize={8} />
                <Tooltip
                  contentStyle={{ background: '#141d36', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 11 }}
                  labelFormatter={() => ''}
                  formatter={(v: any) => [v, 'Queue']}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  )
}
