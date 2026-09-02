import { useState, useEffect } from 'react'
import { analyticsApi } from '@/services/api'
import { useStoreState } from '@/store'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'

export default function Analytics() {
  const { snapshot } = useStoreState()
  const [aiPerf, setAiPerf] = useState<any>(null)

  useEffect(() => {
    analyticsApi.aiPerformance().then(setAiPerf).catch(() => {})
  }, [])

  const queueData = snapshot?.queue_history.slice(-60).map((p, i) => ({ i, v: p.total_queue })) ?? []
  const footfallData = snapshot?.footfall_history.slice(-60).map((p, i) => ({ i, v: p.count })) ?? []

  const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

  return (
    <div className="space-y-6 animate-fade-in">
      <h2 className="text-lg font-bold text-white">Analytics Hub</h2>

      {/* AI Performance */}
      {aiPerf && (
        <div className="card">
          <p className="section-title">AI Performance</p>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-3xl font-bold text-indigo-400">{aiPerf.total_recommendations}</p>
              <p className="text-xs text-gray-500 mt-1">Total Recommendations</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-emerald-400">{aiPerf.acceptance_rate.toFixed(0)}%</p>
              <p className="text-xs text-gray-500 mt-1">Acceptance Rate</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-yellow-400">{aiPerf.success_rate.toFixed(0)}%</p>
              <p className="text-xs text-gray-500 mt-1">Success Rate</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-white">{aiPerf.total_outcomes_measured}</p>
              <p className="text-xs text-gray-500 mt-1">Outcomes Measured</p>
            </div>
          </div>
          {aiPerf.recent_outcomes.length > 0 && (
            <div className="mt-4 space-y-2">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Recent Outcomes</p>
              {aiPerf.recent_outcomes.map((o: any, i: number) => (
                <div key={i} className="flex items-center gap-3 p-2 bg-white/3 rounded-lg text-sm">
                  <span className={o.success ? 'text-emerald-400' : 'text-red-400'}>{o.success ? '✓' : '✗'}</span>
                  <span className="flex-1 text-gray-300 truncate">{o.title}</span>
                  {o.improvement_pct != null && (
                    <span className={o.success ? 'text-emerald-400 text-xs' : 'text-red-400 text-xs'}>
                      {o.improvement_pct > 0 ? '↓' : '↑'}{Math.abs(o.improvement_pct).toFixed(0)}%
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Charts grid */}
      <div className="grid grid-cols-2 gap-6">
        <div className="card">
          <p className="section-title">Footfall Trend (Session)</p>
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={footfallData}>
              <XAxis dataKey="i" hide />
              <YAxis hide />
              <Tooltip contentStyle={{ background: '#141d36', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 11 }}
                labelFormatter={() => ''} formatter={(v: any) => [v, 'Visitors']} />
              <Line type="monotone" dataKey="v" stroke="#6366f1" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <p className="section-title">Queue Trend (Session)</p>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={queueData}>
              <XAxis dataKey="i" hide />
              <YAxis hide />
              <Tooltip contentStyle={{ background: '#141d36', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 11 }}
                labelFormatter={() => ''} formatter={(v: any) => [v, 'Queue']} />
              <Bar dataKey="v" fill="#f59e0b" radius={[2, 2, 0, 0]} maxBarSize={6} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Inventory category breakdown */}
      {snapshot && (
        <div className="card">
          <p className="section-title">Inventory Stock Health</p>
          <div className="grid grid-cols-2 gap-6">
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'In Stock', value: snapshot.inventory.filter(i => i.stock_status === 'ok').length },
                    { name: 'Low', value: snapshot.inventory.filter(i => i.stock_status === 'low').length },
                    { name: 'Critical', value: snapshot.inventory.filter(i => i.stock_status === 'critical').length },
                    { name: 'Out', value: snapshot.inventory.filter(i => i.stock_status === 'out').length },
                  ].filter(d => d.value > 0)}
                  dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} innerRadius={50}
                >
                  {COLORS.map((c, i) => <Cell key={i} fill={c} />)}
                </Pie>
                <Tooltip contentStyle={{ background: '#141d36', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-3 self-center">
              {[
                { label: 'In Stock', count: snapshot.inventory.filter(i => i.stock_status === 'ok').length, color: 'bg-emerald-500' },
                { label: 'Low Stock', count: snapshot.inventory.filter(i => i.stock_status === 'low').length, color: 'bg-yellow-500' },
                { label: 'Critical', count: snapshot.inventory.filter(i => i.stock_status === 'critical').length, color: 'bg-orange-500' },
                { label: 'Out of Stock', count: snapshot.inventory.filter(i => i.stock_status === 'out').length, color: 'bg-red-500' },
              ].map(item => (
                <div key={item.label} className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-sm flex-shrink-0 ${item.color}`} />
                  <span className="text-sm text-gray-300 flex-1">{item.label}</span>
                  <span className="text-sm font-bold text-white">{item.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
