import { useStoreState } from '@/store'
import { inventoryApi } from '@/services/api'
import { useState } from 'react'
import { toast } from 'react-hot-toast'
import { Package, AlertTriangle, TrendingDown, RefreshCw } from 'lucide-react'
import clsx from 'clsx'
import type { InventoryItem } from '@/types'

const STATUS_CONFIG: Record<string, { label: string; dot: string; badge: string }> = {
  ok:       { label: 'In Stock',   dot: 'bg-emerald-500', badge: 'badge-ok' },
  low:      { label: 'Low Stock',  dot: 'bg-yellow-500',  badge: 'badge-medium' },
  critical: { label: 'Critical',   dot: 'bg-orange-500',  badge: 'badge-high' },
  out:      { label: 'Out of Stock', dot: 'bg-red-500',   badge: 'badge-critical' },
}

function StockBar({ item }: { item: InventoryItem }) {
  const pct = item.stock_percentage
  const color = item.stock_status === 'out' ? 'bg-red-500' :
                item.stock_status === 'critical' ? 'bg-orange-500' :
                item.stock_status === 'low' ? 'bg-yellow-500' : 'bg-emerald-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-white/5 rounded-full h-1.5">
        <div className={clsx("h-1.5 rounded-full transition-all duration-700", color)}
             style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-500 w-10 text-right">{pct.toFixed(0)}%</span>
    </div>
  )
}

export default function Inventory() {
  const { snapshot } = useStoreState()
  const [filter, setFilter] = useState<string>('all')
  const [restocking, setRestocking] = useState<number | null>(null)

  if (!snapshot) return <div className="text-gray-500">Loading...</div>

  const items = snapshot.inventory
    .filter(i => filter === 'all' || i.stock_status === filter)
    .sort((a, b) => a.stock_percentage - b.stock_percentage)

  const handleRestock = async (item: InventoryItem) => {
    setRestocking(item.id)
    try {
      await inventoryApi.restock(item.sku, item.max_stock * 0.6)
      toast.success(`✓ Restocked ${item.product_name}`)
    } catch {
      toast.error('Restock failed')
    } finally {
      setRestocking(null)
    }
  }

  const alertItems = snapshot.inventory.filter(i => i.stock_status !== 'ok')

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Summary KPIs */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Total SKUs', value: snapshot.inventory.length, color: 'text-gray-300' },
          { label: 'In Stock', value: snapshot.inventory.filter(i => i.stock_status === 'ok').length, color: 'text-emerald-400' },
          { label: 'Low / Critical', value: snapshot.low_stock_count, color: 'text-yellow-400' },
          { label: 'Out of Stock', value: snapshot.out_of_stock_count, color: 'text-red-400' },
        ].map(k => (
          <div key={k.label} className="card text-center">
            <p className={clsx("text-3xl font-bold", k.color)}>{k.value}</p>
            <p className="kpi-label mt-1">{k.label}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {['all', 'out', 'critical', 'low', 'ok'].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={clsx("px-4 py-1.5 rounded-lg text-sm font-medium transition-colors",
              filter === f ? 'bg-indigo-600 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'
            )}>
            {f === 'all' ? 'All Items' : STATUS_CONFIG[f]?.label ?? f}
          </button>
        ))}
      </div>

      {/* Inventory Table */}
      <div className="card overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/5">
                {['Product', 'SKU', 'Category', 'Stock', 'Level', 'Demand/min', 'Stockout ETA', 'Status', 'Action'].map(h => (
                  <th key={h} className="text-left text-xs font-medium text-gray-500 uppercase tracking-wide px-4 py-3">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const cfg = STATUS_CONFIG[item.stock_status]
                return (
                  <tr key={item.id} className="border-b border-white/5 hover:bg-white/2 transition-colors">
                    <td className="px-4 py-3">
                      <span className="font-medium text-white">{item.product_name}</span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">{item.sku}</td>
                    <td className="px-4 py-3 text-gray-400 text-xs">{item.category}</td>
                    <td className="px-4 py-3">
                      <span className="font-bold text-white">{item.current_stock.toFixed(0)}</span>
                      <span className="text-gray-600 text-xs ml-1">/ {item.max_stock}</span>
                    </td>
                    <td className="px-4 py-3 w-36">
                      <StockBar item={item} />
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-400">
                      {item.demand_rate.toFixed(3)}
                    </td>
                    <td className="px-4 py-3">
                      {item.predicted_stockout_minutes != null ? (
                        <span className={clsx("text-xs font-medium flex items-center gap-1",
                          item.predicted_stockout_minutes < 20 ? 'text-red-400' : 'text-orange-400'
                        )}>
                          <TrendingDown className="w-3 h-3" />
                          {item.predicted_stockout_minutes.toFixed(0)} min
                        </span>
                      ) : (
                        <span className="text-xs text-gray-600">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className={clsx("badge", cfg.badge)}>{cfg.label}</span>
                    </td>
                    <td className="px-4 py-3">
                      {item.stock_status !== 'ok' && (
                        <button
                          onClick={() => handleRestock(item)}
                          disabled={restocking === item.id}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
                                     bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30
                                     transition-colors disabled:opacity-50"
                        >
                          {restocking === item.id
                            ? <span className="w-3 h-3 border border-emerald-400/30 border-t-emerald-400 rounded-full animate-spin" />
                            : <RefreshCw className="w-3 h-3" />
                          }
                          Restock
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
