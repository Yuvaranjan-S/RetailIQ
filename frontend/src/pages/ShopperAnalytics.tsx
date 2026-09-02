import { useStoreState } from '@/store'
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import clsx from 'clsx'

export default function ShopperAnalytics() {
  const { snapshot } = useStoreState()
  if (!snapshot) return <div className="text-gray-500">Loading...</div>

  const footfallData = snapshot.footfall_history.slice(-40).map((p, i) => ({ i, v: p.count }))
  const zones = snapshot.zones.filter(z => z.zone_type !== 'storage')
  const sortedZones = [...zones].sort((a, b) => b.people_count - a.people_count)

  return (
    <div className="space-y-6 animate-fade-in">
      {/* KPIs */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card text-center">
          <p className="text-3xl font-bold text-indigo-400">{snapshot.current_footfall}</p>
          <p className="kpi-label mt-1">Current Visitors</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-emerald-400">{snapshot.total_customers_today}</p>
          <p className="kpi-label mt-1">Total Visitors Today</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-yellow-400">
            {zones.length > 0 ? Math.round(zones.reduce((s, z) => s + z.dwell_time_avg, 0) / zones.length) : 0}s
          </p>
          <p className="kpi-label mt-1">Avg Dwell Time</p>
        </div>
      </div>

      {/* Footfall trend */}
      <div className="card">
        <p className="section-title">Live Footfall Trend</p>
        <ResponsiveContainer width="100%" height={160}>
          <AreaChart data={footfallData}>
            <defs>
              <linearGradient id="ff-gradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="i" hide />
            <YAxis hide />
            <Tooltip
              contentStyle={{ background: '#141d36', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 11 }}
              labelFormatter={() => ''}
              formatter={(v: any) => [v, 'Visitors']}
            />
            <Area type="monotone" dataKey="v" stroke="#6366f1" fill="url(#ff-gradient)" strokeWidth={2.5} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Zone occupancy */}
      <div className="grid grid-cols-2 gap-6">
        <div className="card">
          <p className="section-title">Zone Occupancy</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={sortedZones.map(z => ({ name: z.name.split(' ')[0], count: z.people_count }))}>
              <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 11 }} />
              <YAxis hide />
              <Tooltip
                contentStyle={{ background: '#141d36', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 11 }}
              />
              <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <p className="section-title">Zone Details</p>
          <div className="space-y-3">
            {sortedZones.map(z => {
              const pct = Math.min(100, (z.people_count / (z.zone_type === 'checkout' ? 50 : 80)) * 100)
              const trafficColor = z.traffic_level === 'critical' ? 'bg-red-500' :
                                   z.traffic_level === 'high' ? 'bg-orange-500' :
                                   z.traffic_level === 'medium' ? 'bg-yellow-500' : 'bg-emerald-500'
              return (
                <div key={z.id} className="flex items-center gap-3">
                  <div className="w-24 text-xs text-gray-400 truncate">{z.name.split(' ')[0]}</div>
                  <div className="flex-1 bg-white/5 rounded-full h-2">
                    <div className={clsx("h-2 rounded-full transition-all duration-700", trafficColor)}
                         style={{ width: `${pct}%` }} />
                  </div>
                  <span className="text-xs font-mono text-white w-8 text-right">{z.people_count}</span>
                  <span className="text-xs text-gray-600 w-16 text-right">{Math.round(z.dwell_time_avg)}s dwell</span>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
