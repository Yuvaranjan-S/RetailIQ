// Zustand stores — global state management
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, StoreSnapshot, FusionState, Alert, Recommendation, NetworkStatus } from '@/types'

// ─── Auth Store ─────────────────────────────────────────────────────────────
interface AuthState {
  user: User | null
  token: string | null
  login: (user: User, token: string) => void
  logout: () => void
  isAuthenticated: boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      login: (user, token) => set({ user, token, isAuthenticated: true }),
      logout: () => set({ user: null, token: null, isAuthenticated: false }),
    }),
    { name: 'retailiq-auth' }
  )
)

// ─── Store State (Digital Twin) ──────────────────────────────────────────────
interface StoreStateStore {
  snapshot: StoreSnapshot | null
  fusion: FusionState | null
  alerts: Alert[]
  recommendations: Recommendation[]
  lastUpdated: string | null
  setSnapshot: (s: StoreSnapshot) => void
  setFusion: (f: FusionState) => void
  addAlert: (a: Alert) => void
  addRecommendations: (recs: Recommendation[]) => void
  removeRecommendation: (id: number) => void
}

export const useStoreState = create<StoreStateStore>((set, get) => ({
  snapshot: null,
  fusion: null,
  alerts: [],
  recommendations: [],
  lastUpdated: null,
  setSnapshot: (snapshot) => {
    set({ snapshot, lastUpdated: new Date().toISOString() })
  },
  setFusion: (fusion) => set({ fusion }),
  addAlert: (alert) =>
    set((s) => ({
      alerts: [alert, ...s.alerts].slice(0, 100),
    })),
  addRecommendations: (recs) =>
    set((s) => {
      const existing = new Set(s.recommendations.map((r) => r.id))
      const newOnes = recs.filter((r) => !existing.has(r.id))
      return { recommendations: [...newOnes, ...s.recommendations].slice(0, 50) }
    }),
  removeRecommendation: (id) =>
    set((s) => ({
      recommendations: s.recommendations.filter((r) => r.id !== id),
    })),
}))

// ─── Offline Store ───────────────────────────────────────────────────────────
interface OfflineStore {
  networkStatus: NetworkStatus
  pendingSyncCount: number
  lastSyncMessage: string
  isSyncing: boolean
  setNetworkStatus: (s: NetworkStatus) => void
  setPendingSyncCount: (n: number) => void
  setSyncMessage: (msg: string) => void
  setIsSyncing: (v: boolean) => void
}

export const useOfflineStore = create<OfflineStore>((set) => ({
  networkStatus: 'online',
  pendingSyncCount: 0,
  lastSyncMessage: '',
  isSyncing: false,
  setNetworkStatus: (networkStatus) => set({ networkStatus }),
  setPendingSyncCount: (pendingSyncCount) => set({ pendingSyncCount }),
  setSyncMessage: (lastSyncMessage) => set({ lastSyncMessage }),
  setIsSyncing: (isSyncing) => set({ isSyncing }),
}))
