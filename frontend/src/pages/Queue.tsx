import { useStoreState } from '@/store'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'
import clsx from 'clsx'
import type { CheckoutState } from '@/types'

export default function Queue() {
  const { snapshot } = useStoreState()
  if (!snapshot) return <div className="text-gray-500">Loading...</div>

  const queueData = snapshot.queue_history.slice(-40).map((p, i) => ({ i, v: p.total_queue }))

  const statusColors: Record<string, string> = {
    normal: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
    busy: 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400',
    critical: 'bg-red-500/10 border-red-500/20 text-red-400',
    closed: 'bg-gray-500/10 border-gray-500/20 text-gray-500',
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4">
        <div className="card text-center">
          <p className="text-3xl font-bold text-yellow-400">{snapshot.total_queue_length}</p>
          <p className="kpi-label mt-1">Total Queue</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-indigo-400">{snapshot.open_checkouts}</p>
          <p className="kpi-label mt-1">Open Checkouts</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-white">{snapshot.avg_wait_seconds.toFixed(0)}s</p>
          <p className="kpi-label mt-1">Avg Wait</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-emerald-400">
            {snapshot.checkouts.filter(c => c.is_open).reduce((s, c) => s + c.service_rate, 0).toFixed(1)}
          </p>
          <p className="kpi-label mt-1">Service Rate /min</p>
        </div>
      </div>

      {/* Checkout cards */}
      <div className="grid grid-cols-2 gap-4">
        {snapshot.checkouts.map((c: CheckoutState) => {
          const barPct = c.is_open ? Math.min(100, (c.queue_length / 15) * 100) : 0
          return (
            <div key={c.id} className={clsx("card border", c.is_open ? 'border-white/5' : 'border-dashed border-white/5 opacity-60')}>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-white">{c.name}</h3>
                <span className={clsx("badge border", statusColors[c.status])}>{c.status.toUpperCase()}</span>
              </div>
              <div className="flex items-baseline gap-2 mb-3">
                <span className="text-4xl font-bold text-white">{c.queue_length}</span>
                <span className="text-gray-500">people in queue</span>
              </div>
              <div className="w-full bg-white/5 rounded-full h-2 mb-3">
                <div className={clsx("h-2 rounded-full transition-all duration-700",
                  barPct > 70 ? 'bg-red-500' : barPct > 40 ? 'bg-yellow-500' : 'bg-emerald-500'
                )} style={{ width: `${barPct}%` }} />
              </div>
              <div className="grid grid-cols-3 gap-2 text-center text-xs text-gray-500">
                <div>
                  <p className="font-medium text-white">{c.arrival_rate.toFixed(2)}</p>
                  <p>Arrivals/min</p>
                </div>
                <div>
                  <p className="font-medium text-white">{c.service_rate.toFixed(2)}</p>
                  <p>Service/min</p>
                </div>
                <div>
                  <p className="font-medium text-white">{c.estimated_wait_minutes?.toFixed(1) ?? '0'}m</p>
                  <p>Est. wait</p>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Queue trend */}
      <div className="card">
        <p className="section-title">Total Queue Trend</p>
        <ResponsiveContainer width="100%" height={160}>
          <LineChart data={queueData}>
            <XAxis dataKey="i" hide />
            <YAxis hide domain={[0, 'auto']} />
            <Tooltip
              contentStyle={{ background: '#141d36', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 11 }}
              labelFormatter={() => ''}
              formatter={(v: any) => [v, 'Queue Length']}
            />
            <Line type="monotone" dataKey="v" stroke="#f59e0b" strokeWidth={2.5} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
