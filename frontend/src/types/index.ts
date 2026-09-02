// All TypeScript interfaces matching backend schemas

export type UserRole = 'admin' | 'store_manager' | 'staff'
export type AlertSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
export type AlertStatus = 'active' | 'acknowledged' | 'resolved' | 'dismissed'
export type RecPriority = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
export type RecStatus = 'pending' | 'accepted' | 'rejected' | 'modified' | 'expired'
export type StockStatus = 'ok' | 'low' | 'critical' | 'out'
export type TrafficLevel = 'low' | 'medium' | 'high' | 'critical'
export type NetworkStatus = 'online' | 'offline' | 'degraded'

export interface User {
  id: number
  username: string
  email: string
  role: UserRole
  full_name?: string
}

export interface ZoneState {
  id: number
  name: string
  zone_type: string
  people_count: number
  dwell_time_avg: number
  traffic_level: TrafficLevel
  heat_score: number
  coord_x: number
  coord_y: number
  coord_w: number
  coord_h: number
  display_color: string
  last_updated: string
}

export interface CheckoutState {
  id: number
  name: string
  is_open: boolean
  checkout_type: string
  queue_length: number
  estimated_wait_seconds: number
  estimated_wait_minutes: number
  arrival_rate: number
  service_rate: number
  staff_count: number
  status: 'normal' | 'busy' | 'critical' | 'closed'
}

export interface InventoryItem {
  id: number
  sku: string
  product_name: string
  category: string
  current_stock: number
  max_stock: number
  reorder_level: number
  demand_rate: number
  predicted_stockout_minutes?: number
  stock_percentage: number
  stock_status: StockStatus
}

export interface StaffMember {
  id: number
  name: string
  role: string
  current_zone_id?: number
  current_zone_name?: string
  availability: 'available' | 'busy' | 'break' | 'offline'
  current_task?: string
}

export interface StoreSnapshot {
  type: string
  store_id: number
  store_name: string
  status: string
  timestamp: string
  // KPIs
  current_footfall: number
  total_customers_today: number
  active_alerts_count: number
  active_recommendations_count: number
  // Details
  zones: ZoneState[]
  checkouts: CheckoutState[]
  inventory: InventoryItem[]
  staff: StaffMember[]
  // Aggregates
  open_checkouts: number
  total_queue_length: number
  avg_wait_seconds: number
  low_stock_count: number
  out_of_stock_count: number
  available_staff: number
  // System
  network_status: NetworkStatus
  simulation_mode: boolean
  pending_sync_count: number
  // History
  footfall_history: Array<{ ts: string; count: number }>
  queue_history: Array<{ ts: string; total_queue: number }>
}

export interface Alert {
  id: number
  alert_type: string
  severity: AlertSeverity
  title: string
  description?: string
  location?: string
  recommended_action?: string
  status: AlertStatus
  created_at: string
  resolved_at?: string
}

export interface Recommendation {
  id: number
  rec_type: string
  title: string
  description?: string
  priority: RecPriority
  confidence: number
  reason?: string
  evidence: string[]
  recommended_action?: string
  expected_impact?: string
  status: RecStatus
  created_at: string
  checkout_id?: number
  zone_id?: number
  inventory_id?: number
}

export interface FusionState {
  compound_score: number
  signals: Record<string, number>
  dominant_signal: string
  scenario_tags: string[]
  store_stress_level: string
}

export interface SystemHealth {
  store_id: number
  camera_status: string
  ai_status: string
  db_status: string
  network_status: string
  simulation_mode: boolean
  active_connections: number
  footfall: number
  pending_sync_count: number
  checked_at: string
}

// WebSocket message types
export type WSMessage =
  | (StoreSnapshot & { type: 'store_state' })
  | { type: 'fusion_update'; fusion: FusionState; new_recommendations: Recommendation[] }
  | { type: 'new_alert'; alert: Alert }
  | { type: 'scenario_changed'; scenario: string; message: string }
  | { type: 'network_status_change'; status: string; message: string; syncing?: boolean; pending_count?: number }
  | { type: 'sync_complete'; message: string; synced_count: number }
  | { type: 'pong' }
