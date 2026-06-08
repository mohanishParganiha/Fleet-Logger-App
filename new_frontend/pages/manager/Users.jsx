import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useLang } from '../../context/LangContext'
import api from '../../hooks/useApi'

export default function Users() {
  const { t } = useLang()
  const [success, setSuccess] = useState('')
  const [error, setError]     = useState('')

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm()

  async function onSubmit(data) {
    setSuccess('')
    setError('')
    try {
      await api.post('/users/create/', {
        email:    data.email,
        username: data.username,
        password: data.password,
      })
      setSuccess(`User ${data.email} created.`)
      reset()
    } catch (err) {
      const d = err.response?.data
      setError(d ? Object.values(d).flat().join(' ') : 'Something went wrong.')
    }
  }

  return (
    <div className="space-y-6 max-w-lg">
      <h2 className="font-display text-3xl font-bold text-ink tracking-wide uppercase">
        {t.users || 'Users'}
      </h2>

      <p className="font-body text-sm text-ink-400">
        Create a new user account. Role (manager / staff) must be set via Django admin.
      </p>

      <div className="card space-y-4">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="label">Email</label>
            <input
              type="email"
              className="input-field"
              placeholder="driver@company.com"
              {...register('email', { required: true })}
            />
            {errors.email && <p className="text-rust text-xs mt-1">Required</p>}
          </div>

          <div>
            <label className="label">Username</label>
            <input
              className="input-field"
              placeholder="Ramesh Kumar"
              {...register('username', { required: true })}
            />
            {errors.username && <p className="text-rust text-xs mt-1">Required</p>}
          </div>

          <div>
            <label className="label">Password</label>
            <input
              type="password"
              className="input-field"
              placeholder="Strong password"
              {...register('password', { required: true, minLength: 8 })}
            />
            {errors.password && <p className="text-rust text-xs mt-1">Min 8 characters</p>}
          </div>

          {error && (
            <p className="text-rust font-body text-sm bg-rust/5 border border-rust/20 rounded px-3 py-2">
              {error}
            </p>
          )}

          {success && (
            <p className="text-green-700 font-body text-sm bg-green-50 border border-green-200 rounded px-3 py-2">
              {success}
            </p>
          )}

          <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
            {isSubmitting ? 'Creating…' : 'Create User'}
          </button>
        </form>
      </div>
    </div>
  )
}
