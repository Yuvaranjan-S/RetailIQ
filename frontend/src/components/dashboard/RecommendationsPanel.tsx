// AI Recommendations Panel — Live right sidebar of command center
import { useState } from 'react'
import { Brain, CheckCircle, XCircle, ChevronDown, ChevronUp, Sparkles } from 'lucide-react'
import { useStoreState } from '@/store'
import { recommendationsApi } from '@/services/api'
import { toast } from 'react-hot-toast'
import clsx from 'clsx'
import type { Recommendation } from '@/types'

const PRIORITY_STYLES: Record<string, string> = {
  CRITICAL: 'border-red-500/40 bg-red-500/5',
  HIGH: 'border-orange-500/40 bg-orange-500/5',
  MEDIUM: 'border-yellow-500/40 bg-yellow-500/5',
  LOW: 'border-blue-500/40 bg-blue-500/5',
}
const PRIORITY_DOT: Record<string, string> = {
  CRITICAL: 'bg-red-500 animate-pulse',
  HIGH: 'bg-orange-500',
  MEDIUM: 'bg-yellow-500',
  LOW: 'bg-blue-500',
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100)
  return (
    <div className="flex items-center gap-2 mt-2">
      <div className="flex-1 bg-white/5 rounded-full h-1.5">
        <div
          className={clsx("h-1.5 rounded-full transition-all",
            pct >= 85 ? 'bg-emerald-500' : pct >= 65 ? 'bg-yellow-500' : 'bg-orange-500'
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-mono text-gray-400">{pct}%</span>
    </div>
  )
}

function RecCard({ rec, onAccept, onReject }: {
  rec: Recommendation
  onAccept: (id: number) => void
  onReject: (id: number) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const [loading, setLoading] = useState<'accept' | 'reject' | null>(null)

  const handleAccept = async () => {
    setLoading('accept')
    await onAccept(rec.id)
    setLoading(null)
  }
  const handleReject = async () => {
    setLoading('reject')
    await onReject(rec.id)
    setLoading(null)
  }

  return (
    <div className={clsx(
      "rounded-xl border p-3 transition-all duration-300 animate-slide-in",
      PRIORITY_STYLES[rec.priority]
    )}>
      {/* Header */}
      <div className="flex items-start gap-2">
        <div className={clsx("w-2 h-2 mt-1 rounded-full flex-shrink-0", PRIORITY_DOT[rec.priority])} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={clsx(
              "text-xs font-bold uppercase tracking-wide",
              rec.priority === 'CRITICAL' ? 'text-red-400' :
              rec.priority === 'HIGH' ? 'text-orange-400' :
              rec.priority === 'MEDIUM' ? 'text-yellow-400' : 'text-blue-400'
            )}>
              {rec.priority}
            </span>
          </div>
          <p className="text-sm font-medium text-white mt-0.5 leading-snug">{rec.title}</p>
          <ConfidenceBar value={rec.confidence} />
        </div>
        <button onClick={() => setExpanded(!expanded)} className="text-gray-500 hover:text-white mt-0.5">
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Expanded: evidence + action */}
      {expanded && (
        <div className="mt-3 pl-4 animate-fade-in">
          {rec.evidence?.length > 0 && (
            <div className="mb-3">
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-1.5">Evidence</p>
              <ul className="space-y-1">
                {rec.evidence.map((e, i) => (
                  <li key={i} className="text-xs text-gray-400 flex items-start gap-1.5">
                    <span className="text-gray-600 mt-0.5">→</span>
                    {e}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {rec.recommended_action && (
            <div className="mb-3 p-2.5 bg-white/5 rounded-lg">
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Recommended Action</p>
              <p className="text-xs text-gray-200">{rec.recommended_action}</p>
            </div>
          )}
          {rec.expected_impact && (
            <p className="text-xs text-emerald-400 mb-3">✓ {rec.expected_impact}</p>
          )}
        </div>
      )}

      {/* Action buttons */}
      {rec.status === 'pending' && (
        <div className="flex gap-2 mt-3 pl-4">
          <button
            onClick={handleAccept}
            disabled={!!loading}
            className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-medium
                       bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30
                       transition-colors disabled:opacity-50"
          >
            {loading === 'accept' ? <span className="w-3 h-3 border border-white/30 border-t-white rounded-full animate-spin" /> : <CheckCircle className="w-3.5 h-3.5" />}
            Accept
          </button>
          <button
            onClick={handleReject}
            disabled={!!loading}
            className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-medium
                       bg-red-600/10 hover:bg-red-600/20 text-red-400 border border-red-500/20
                       transition-colors disabled:opacity-50"
          >
            {loading === 'reject' ? <span className="w-3 h-3 border border-white/30 border-t-white rounded-full animate-spin" /> : <XCircle className="w-3.5 h-3.5" />}
            Reject
          </button>
        </div>
      )}
      {rec.status !== 'pending' && (
        <div className="mt-2 pl-4">
          <span className={clsx("text-xs badge",
            rec.status === 'accepted' ? 'badge-ok' : 'badge-offline'
          )}>
            {rec.status.toUpperCase()}
          </span>
        </div>
      )}
    </div>
  )
}

export default function RecommendationsPanel() {
  const { recommendations, removeRecommendation } = useStoreState()
  const pending = recommendations.filter(r => r.status === 'pending').slice(0, 5)

  const handleAccept = async (id: number) => {
    try {
      await recommendationsApi.accept(id)
      removeRecommendation(id)
      toast.success('✓ Action accepted & applied to store')
    } catch {
      toast.error('Failed to accept recommendation')
    }
  }

  const handleReject = async (id: number) => {
    try {
      await recommendationsApi.reject(id)
      removeRecommendation(id)
      toast('Recommendation rejected', { icon: '✗' })
    } catch {
      toast.error('Failed to reject')
    }
  }

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-7 h-7 bg-indigo-600/30 border border-indigo-500/30 rounded-lg flex items-center justify-center">
          <Brain className="w-4 h-4 text-indigo-400" />
        </div>
        <div>
          <p className="text-sm font-semibold text-white">AI Recommendations</p>
          <p className="text-xs text-gray-500">Confidence-scored actions</p>
        </div>
        {pending.length > 0 && (
          <span className="ml-auto bg-indigo-600 text-white text-xs px-2 py-0.5 rounded-full animate-pulse">
            {pending.length} new
          </span>
        )}
      </div>

      {pending.length === 0 ? (
        <div className="text-center py-6">
          <Sparkles className="w-8 h-8 text-gray-600 mx-auto mb-2" />
          <p className="text-sm text-gray-500">All clear — no pending actions</p>
          <p className="text-xs text-gray-600 mt-1">AI monitoring continuously</p>
        </div>
      ) : (
        <div className="space-y-3 max-h-[500px] overflow-y-auto">
          {pending.map(rec => (
            <RecCard key={rec.id} rec={rec} onAccept={handleAccept} onReject={handleReject} />
          ))}
        </div>
      )}
    </div>
  )
}
