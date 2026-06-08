import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useAuth } from '../context/AuthContext'
import { useLang } from '../context/LangContext'
import LangToggle from '../components/LangToggle'
import api from '../hooks/useApi'

export default function Login() {
  const { login } = useAuth()
  const { t } = useLang()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm()

  async function onSubmit(data) {
    setLoading(true)
    setError('')
    try {
      const res = await api.post('/login/', data)
      login(res.data)
      // Route based on role
      if (res.data.is_staff || res.data.is_manager) {
        navigate('/manager/vehicles')
      } else {
        navigate('/driver/trips')
      }
    } catch {
      setError(t.invalid_creds)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Lang toggle top-right */}
        <div className="flex justify-end mb-6">
          <LangToggle />
        </div>

        {/* Brand */}
        <div className="mb-8">
          <h1 className="font-display text-5xl font-bold tracking-widest text-ink uppercase">
            Fleet
          </h1>
          <div className="h-1 w-12 bg-amber mt-2 rounded-full" />
          <p className="font-body text-sm text-ink-400 mt-3">
            Fleet Logger — Logistics Management
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="card space-y-4">
          <div>
            <label className="label">{t.email}</label>
            <input
              type="email"
              className="input-field"
              placeholder="you@company.com"
              {...register('email', { required: true })}
            />
            {errors.email && <p className="text-rust text-xs mt-1">Required</p>}
          </div>

          <div>
            <label className="label">{t.password}</label>
            <input
              type="password"
              className="input-field"
              placeholder="••••••••"
              {...register('password', { required: true })}
            />
            {errors.password && <p className="text-rust text-xs mt-1">Required</p>}
          </div>

          {error && (
            <p className="text-rust text-sm font-body bg-rust/5 border border-rust/20 rounded px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full mt-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? t.signing_in : t.login}
          </button>
        </form>
      </div>
    </div>
  )
}
