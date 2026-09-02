import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store'
import { authApi } from '@/services/api'
import { Zap, Eye, EyeOff, AlertCircle } from 'lucide-react'

export default function Login() {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin123')
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { login } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const data = await authApi.login(username, password)
      login(data.user, data.access_token)
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Login failed. Check credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-emerald-600/8 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-md relative">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-indigo-600 rounded-2xl mb-4 shadow-2xl shadow-indigo-500/30">
            <Zap className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">RetailIQ</h1>
          <p className="text-gray-500 text-sm mt-1">Edge-First AI Retail Intelligence Platform</p>
          <p className="text-xs text-gray-600 mt-0.5">Smart India Hackathon 2026 · PS-179</p>
        </div>

        {/* Card */}
        <div className="gradient-border">
          <div className="bg-[#0f1629] rounded-xl p-8">
            <h2 className="text-lg font-semibold text-white mb-6">Sign in to your store</h2>

            {error && (
              <div className="mb-4 flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Username</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white
                             placeholder-gray-600 focus:outline-none focus:border-indigo-500 focus:ring-1
                             focus:ring-indigo-500 transition-colors text-sm"
                  placeholder="username"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Password</label>
                <div className="relative">
                  <input
                    type={showPass ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 pr-12 text-white
                               placeholder-gray-600 focus:outline-none focus:border-indigo-500 focus:ring-1
                               focus:ring-indigo-500 transition-colors text-sm"
                    placeholder="••••••••"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPass(!showPass)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                  >
                    {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <button type="submit" disabled={loading} className="w-full btn-primary justify-center py-3">
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Signing in...
                  </span>
                ) : 'Sign in'}
              </button>
            </form>

            {/* Demo credentials */}
            <div className="mt-6 pt-5 border-t border-white/5">
              <p className="text-xs text-gray-600 text-center mb-3">Demo credentials</p>
              <div className="grid grid-cols-3 gap-2 text-xs">
                {[
                  { role: 'Admin', user: 'admin', pass: 'admin123' },
                  { role: 'Manager', user: 'manager', pass: 'manager123' },
                  { role: 'Staff', user: 'staff1', pass: 'staff123' },
                ].map((c) => (
                  <button
                    key={c.user}
                    onClick={() => { setUsername(c.user); setPassword(c.pass) }}
                    className="p-2 bg-white/3 hover:bg-white/8 border border-white/5 rounded-lg
                               text-gray-400 hover:text-white transition-colors text-center"
                  >
                    <div className="font-medium">{c.role}</div>
                    <div className="text-gray-600">{c.user}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
