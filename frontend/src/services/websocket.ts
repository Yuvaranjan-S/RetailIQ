// WebSocket client — manages connection to /ws/store
import { useEffect, useRef, useCallback } from 'react'
import { useStoreState, useOfflineStore } from '@/store'
import { storeApi } from '@/services/api'
import type { WSMessage, StoreSnapshot } from '@/types'

const getWsUrl = (storeId: number) => {
  const host = typeof window !== 'undefined' ? window.location.hostname : 'localhost'
  const protocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${host}:8000/ws/store?store_id=${storeId}`
}

const RECONNECT_DELAY = 3000

export function useWebSocket(storeId = 1) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const { setSnapshot, setFusion, addAlert, addRecommendations } = useStoreState()
  const { setNetworkStatus, setPendingSyncCount, setSyncMessage, setIsSyncing } = useOfflineStore()

  // Initial HTTP fetch to populate dashboard instantly
  useEffect(() => {
    storeApi.getState(storeId).then((data) => {
      if (data && data.store_id) {
        setSnapshot(data)
      }
    }).catch(() => {})
  }, [storeId, setSnapshot])

  const connect = useCallback(() => {
    try {
      const url = getWsUrl(storeId)
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('[WS] Connected to store', storeId)
        const ping = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) ws.send('ping')
        }, 30000)
        ;(ws as any)._pingInterval = ping
      }

      ws.onmessage = (event) => {
        try {
          const msg: WSMessage = JSON.parse(event.data)

          switch (msg.type) {
            case 'store_state':
              setSnapshot(msg as StoreSnapshot)
              setNetworkStatus((msg as StoreSnapshot).network_status)
              setPendingSyncCount((msg as StoreSnapshot).pending_sync_count)
              break

            case 'fusion_update':
              setFusion(msg.fusion)
              if (msg.new_recommendations?.length) {
                addRecommendations(msg.new_recommendations as any)
              }
              break

            case 'new_alert':
              addAlert(msg.alert as any)
              break

            case 'network_status_change':
              setNetworkStatus(msg.status as any)
              setSyncMessage(msg.message)
              if (msg.syncing) setIsSyncing(true)
              break

            case 'sync_complete':
              setIsSyncing(false)
              setNetworkStatus('online')
              setSyncMessage(msg.message)
              setTimeout(() => setSyncMessage(''), 5000)
              break

            case 'scenario_changed':
              setSyncMessage(`🎬 ${msg.message}`)
              setTimeout(() => setSyncMessage(''), 4000)
              break
          }
        } catch (e) {
          console.error('[WS] Parse error', e)
        }
      }

      ws.onerror = () => {
        console.warn('[WS] Connection error')
      }

      ws.onclose = () => {
        console.log('[WS] Disconnected — reconnecting in', RECONNECT_DELAY, 'ms')
        clearInterval((ws as any)._pingInterval)
        reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY)
      }
    } catch (e) {
      console.error('[WS] Failed to connect', e)
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY)
    }
  }, [storeId, setSnapshot, setFusion, addAlert, addRecommendations, setNetworkStatus, setPendingSyncCount, setSyncMessage, setIsSyncing])

  useEffect(() => {
    connect()
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [connect])

  return wsRef
}
