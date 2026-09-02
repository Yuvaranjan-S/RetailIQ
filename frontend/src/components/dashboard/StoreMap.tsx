// Store Map — renders a top-down floor plan with zone heatmap
import type { ZoneState } from '@/types'
import clsx from 'clsx'

const TRAFFIC_OPACITY: Record<string, number> = {
  low: 0.15, medium: 0.35, high: 0.65, critical: 0.90,
}

interface Props { zones: ZoneState[] }

export default function StoreMap({ zones }: Props) {
  if (!zones.length) return null

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <p className="section-title mb-0">Live Store Map</p>
        <div className="flex items-center gap-3 text-xs text-gray-500">
          {[['low','bg-blue-500'],['medium','bg-yellow-500'],['high','bg-orange-500'],['critical','bg-red-500']].map(([l,c]) => (
            <span key={l} className="flex items-center gap-1">
              <span className={clsx("w-2 h-2 rounded-sm", c)} />
              {l}
            </span>
          ))}
        </div>
      </div>

      {/* Floor plan grid — 100×60 coordinate space */}
      <div
        className="relative w-full rounded-xl border border-white/5 overflow-hidden"
        style={{ paddingTop: '60%', background: '#141d36' }}
      >
        <div className="absolute inset-0 p-2">
          {zones.map((zone) => {
            const opacity = TRAFFIC_OPACITY[zone.traffic_level] ?? 0.15
            return (
              <div
                key={zone.id}
                className="absolute rounded-lg border border-white/10 flex flex-col items-center justify-center
                           cursor-default hover:border-white/30 transition-all duration-500 overflow-hidden"
                style={{
                  left: `${zone.coord_x}%`,
                  top: `${zone.coord_y}%`,
                  width: `${zone.coord_w}%`,
                  height: `${zone.coord_h * (100 / 60)}%`,
                  backgroundColor: zone.display_color + Math.round(opacity * 255).toString(16).padStart(2, '0'),
                  borderColor: zone.display_color + '60',
                }}
              >
                {/* Heat fill */}
                <div
                  className="absolute inset-0 transition-all duration-700"
                  style={{
                    background: `radial-gradient(circle, ${zone.display_color}${Math.round(opacity * 200).toString(16).padStart(2,'0')} 0%, transparent 70%)`,
                  }}
                />
                <div className="relative z-10 text-center p-1">
                  <div className="text-white font-medium text-xs leading-tight">{zone.name}</div>
                  <div className="text-white/80 text-xs mt-0.5">
                    <span className="font-bold">{zone.people_count}</span>
                    <span className="text-white/50 ml-0.5">ppl</span>
                  </div>
                  {zone.traffic_level !== 'low' && (
                    <div className="mt-0.5">
                      <span className={clsx(
                        "text-xs font-medium px-1 py-0.5 rounded",
                        zone.traffic_level === 'critical' ? 'bg-red-500/30 text-red-300' :
                        zone.traffic_level === 'high' ? 'bg-orange-500/30 text-orange-300' :
                        'bg-yellow-500/30 text-yellow-300'
                      )}>
                        {zone.traffic_level.toUpperCase()}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Zone detail grid */}
      <div className="mt-3 grid grid-cols-3 gap-2">
        {zones.filter(z => z.zone_type !== 'storage').map(zone => (
          <div key={zone.id} className="flex items-center gap-2 p-2 bg-white/3 rounded-lg">
            <div className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ backgroundColor: zone.display_color }} />
            <div className="min-w-0">
              <div className="text-xs font-medium text-white truncate">{zone.name.split(' ')[0]}</div>
              <div className="text-xs text-gray-500">{zone.people_count} · {Math.round(zone.dwell_time_avg)}s dwell</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
