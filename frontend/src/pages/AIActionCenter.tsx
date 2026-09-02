import { useState, useEffect } from 'react'
import { recommendationsApi } from '@/services/api'
import { Brain, CheckCircle, XCircle, ChevronDown, ChevronUp, Award, TrendingUp } from 'lucide-react'
import clsx from 'clsx'
import { toast } from 'react-hot-toast'
import type { Recommendation } from '@/types'

const PRIORITY_CONFIG: Record<string, string> = {
  CRITICAL: 'border-red-500/40 bg-red-500/5 text-red-400',
  HIGH: 'border-orange-500/40 bg-orange-500/5 text-orange-400',
  MEDIUM: 'border-yellow-500/40 bg-yellow-500/5 text-yellow-400',
  LOW: 'border-blue-500/40 bg-blue-500/5 text-blue-400',
}

function RecFull({ rec, onAccept, onReject }: {
  rec: Recommendation; onAccept: (id: number) => void; onReject: (id: number) => void
}) {
  const [expanded, setExpanded] = useState(true)
  const [acting, setActing] = useState<string | null>(null)
  const pctConf = Math.round(rec.confidence * 100)
  const cfg = PRIORITY_CONFIG[rec.priority] ?? PRIORITY_CONFIG.LOW

  return (
    <div className={clsx("border rounded-xl p-5 transition-all", cfg)}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className={clsx("badge border", cfg.split(' ').slice(2).join(' '))}>
              {rec.priority}
            </span>
            <span className="text-xs text-gray-500 capitalize">{rec.rec_type.replace(/_/g, ' ')}</span>
            {rec.status !== 'pending' && (
              <span className={clsx("badge", rec.status === 'accepted' ? 'badge-ok' : 'badge-offline')}>
                {rec.status.toUpperCase()}
              </span>
            )}
          </div>
          <h3 className="font-semibold text-white text-base">{rec.title}</h3>
          <p className="text-sm text-gray-400 mt-1">{rec.reason}</p>
        </div>
        <div className="text-right flex-shrink-0">
          <div className="text-2xl font-bold text-white">{pctConf}%</div>
          <div className="text-xs text-gray-500">Confidence</div>
        </div>
      </div>

      {/* Confidence bar */}
      <div className="w-full bg-white/5 rounded-full h-2 mt-3">
        <div
          className={clsx("h-2 rounded-full transition-all", pctConf >= 85 ? 'bg-emerald-500' : pctConf >= 65 ? 'bg-yellow-500' : 'bg-orange-500')}
          style={{ width: `${pctConf}%` }}
        />
      </div>

      {/* Evidence */}
      {rec.evidence?.length > 0 && (
        <div className="mt-4 p-3 bg-white/3 rounded-lg">
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-1">
            Evidence
          </p>
          <ul className="space-y-1">
            {rec.evidence.map((e, i) => (
              <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                <span className="text-gray-600 mt-0.5 text-xs">▸</span>{e}
              </li>
            ))}
          </ul>
        </div>
      )}

      {rec.recommended_action && (
        <div className="mt-3 p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-lg">
          <p className="text-xs text-indigo-400 uppercase tracking-wide mb-1">Recommended Action</p>
          <p className="text-sm text-white">{rec.recommended_action}</p>
        </div>
      )}
      {rec.expected_impact && (
        <div className="mt-2 flex items-start gap-1.5 text-sm text-emerald-400">
          <TrendingUp className="w-4 h-4 flex-shrink-0 mt-0.5" />
          {rec.expected_impact}
        </div>
      )}

      {rec.status === 'pending' && (
        <div className="flex gap-3 mt-4">
          <button onClick={async () => { setActing('accept'); await onAccept(rec.id); setActing(null) }}
            disabled={!!acting}
            className="flex-1 btn-success justify-center py-2.5">
            {acting === 'accept' ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <CheckCircle className="w-4 h-4" />}
            Accept & Apply
          </button>
          <button onClick={async () => { setActing('reject'); await onReject(rec.id); setActing(null) }}
            disabled={!!acting}
            className="flex-1 btn-danger justify-center py-2.5">
            {acting === 'reject' ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <XCircle className="w-4 h-4" />}
            Reject
          </button>
        </div>
      )}
    </div>
  )
}

export default function AIActionCenter() {
  const [recs, setRecs] = useState<Recommendation[]>([])
  const [outcomes, setOutcomes] = useState<any[]>([])
  const [tab, setTab] = useState<'active' | 'history'>('active')
  const [loading, setLoading] = useState(true)

  const load = async () => {
    try {
      const [active, history] = await Promise.all([
        recommendationsApi.getAll(1, 'all'),
        recommendationsApi.getOutcomes(),
      ])
      setRecs(active.recommendations)
      setOutcomes(history.outcomes)
    } catch { } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleAccept = async (id: number) => {
    await recommendationsApi.accept(id)
    toast.success('✓ Action accepted & applied')
    await load()
  }
  const handleReject = async (id: number) => {
    await recommendationsApi.reject(id)
    toast('Recommendation rejected')
    await load()
  }

  const pending = recs.filter(r => r.status === 'pending')
  const actedOn = recs.filter(r => r.status !== 'pending')

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-indigo-600/30 border border-indigo-500/30 rounded-xl flex items-center justify-center">
          <Brain className="w-5 h-5 text-indigo-400" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-white">AI Action Center</h2>
          <p className="text-sm text-gray-500">Review confidence-scored recommendations with full evidence</p>
        </div>
        <div className="ml-auto flex gap-2">
          <button onClick={() => setTab('active')} className={clsx("px-4 py-2 rounded-lg text-sm font-medium transition-colors",
            tab === 'active' ? 'bg-indigo-600 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10')}>
            Active {pending.length > 0 && `(${pending.length})`}
          </button>
          <button onClick={() => setTab('history')} className={clsx("px-4 py-2 rounded-lg text-sm font-medium transition-colors",
            tab === 'history' ? 'bg-indigo-600 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10')}>
            History & Outcomes
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : tab === 'active' ? (
        <div className="space-y-4">
          {pending.length === 0 && (
            <div className="card text-center py-12">
              <Brain className="w-12 h-12 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400">No pending recommendations</p>
              <p className="text-xs text-gray-600 mt-1">AI is monitoring — activate a scenario to generate recommendations</p>
            </div>
          )}
          {pending.map(r => <RecFull key={r.id} rec={r} onAccept={handleAccept} onReject={handleReject} />)}
          {actedOn.length > 0 && (
            <div>
              <p className="section-title">Acted On</p>
              {actedOn.slice(0, 5).map(r => <RecFull key={r.id} rec={r} onAccept={handleAccept} onReject={handleReject} />)}
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {outcomes.length === 0 ? (
            <div className="card text-center py-12">
              <Award className="w-12 h-12 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400">No outcome data yet</p>
              <p className="text-xs text-gray-600 mt-1">Accept recommendations and wait for outcomes to be measured</p>
            </div>
          ) : (
            outcomes.map((o, i) => (
              <div key={i} className="card flex items-center gap-4">
                <div className={clsx("w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0",
                  o.success ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400')}>
                  {o.success ? <CheckCircle className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-white text-sm">{o.title}</p>
                  <p className="text-xs text-gray-500">{o.rec_type?.replace(/_/g, ' ')} · {o.taken_at ? new Date(o.taken_at).toLocaleString() : ''}</p>
                </div>
                {o.metric_before != null && o.metric_after != null && (
                  <div className="text-right text-xs">
                    <p className="text-gray-500">{o.metric_name}</p>
                    <p className="text-white font-mono">{o.metric_before} → {o.metric_after}</p>
                    {o.improvement_pct != null && (
                      <p className={clsx("font-medium", o.success ? 'text-emerald-400' : 'text-red-400')}>
                        {o.improvement_pct > 0 ? '↓' : '↑'} {Math.abs(o.improvement_pct).toFixed(0)}%
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
