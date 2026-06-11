import { useState, useEffect, useCallback } from 'react'
import { createPortal } from 'react-dom' // <-- Add this line
import { useForm } from 'react-hook-form'
import { useLang } from '../../context/LangContext'
import api from '../../hooks/useApi'

export default function Drivers() {
  const { t } = useLang()
  const [drivers, setDrivers]     = useState([])
  const [vehicles, setVehicles]   = useState([])
  const [loading, setLoading]     = useState(true)
  const [modal, setModal]         = useState(null)   // null | { mode: 'add'|'edit', data? }
  const [delTarget, setDelTarget] = useState(null)
  const [filters, setFilters]     = useState({ status: '', name: '' })
  const [apiError, setApiError]   = useState('')

  const { register, handleSubmit, reset, watch, formState: { errors, isSubmitting } } = useForm()
  const password = watch('user_password')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = {}
      if (filters.status) params.status = filters.status
      if (filters.name)   params.name   = filters.name
      const [dRes, vRes] = await Promise.all([
        api.get('/drivers/', { params }),
        api.get('/vehicles/', { params: { status: 'active' } }),
      ])
      setDrivers(dRes.data.results  || [])
      setVehicles(vRes.data.results || [])
    } finally { setLoading(false) }
  }, [filters])

  useEffect(() => { load() }, [load])

  function openAdd() {
    setApiError('')
    reset({
      name: '', license_number: '', phone_number: '', status: 'active', primary_vehicle: '',
      user_email: '', user_username: '', user_password: '', user_password2: ''
    })
    setModal({ mode: 'add' })
  }

  function openEdit(d) {
    setApiError('')
    reset({
      name: d.name,
      phone_number: d.phone_number || '',
      status: d.status,
      primary_vehicle: d.primary_vehicle || '',
    })
    setModal({ mode: 'edit', data: d })
  }

  async function onSubmit(data) {
    setApiError('')

    if (modal.mode === 'add') {
      // frontend password match validation
      if (data.user_password !== data.user_password2) {
        setApiError('Passwords do not match.')
        return
      }

      const payload = {
        user: {
          email:    data.user_email,
          username: data.user_username,
          password: data.user_password,
        },
        name:            data.name,
        phone_number:    data.phone_number,
        license_number:  data.license_number,
        status:          data.status,
      }
      if (data.primary_vehicle) payload.primary_vehicle = data.primary_vehicle

      try {
        await api.post('/drivers/', payload)
        setModal(null)
        load()
      } catch (err) {
        const d = err.response?.data
        if (d) {
          // flatten nested error object
          const msgs = []
          const flatten = (obj, prefix = '') => {
            Object.entries(obj).forEach(([k, v]) => {
              if (Array.isArray(v)) msgs.push(`${prefix}${k}: ${v.join(', ')}`)
              else if (typeof v === 'object') flatten(v, `${k}.`)
              else msgs.push(`${prefix}${k}: ${v}`)
            })
          }
          flatten(d)
          setApiError(msgs.join(' | '))
        } else {
          setApiError('Something went wrong.')
        }
      }
    } else {
      // edit — only these fields
      const payload = {
        name:            data.name,
        phone_number:    data.phone_number,
        status:          data.status,
      }
      if (data.primary_vehicle) payload.primary_vehicle = data.primary_vehicle
      else payload.primary_vehicle = null

      try {
        await api.patch(`/drivers/${modal.data.id}/`, payload)
        setModal(null)
        load()
      } catch (err) {
        const d = err.response?.data
        setApiError(d ? Object.values(d).flat().join(' ') : 'Something went wrong.')
      }
    }
  }

  async function confirmDelete() {
    await api.delete(`/drivers/${delTarget.id}/`)
    setDelTarget(null)
    load()
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="font-display text-3xl font-bold text-ink tracking-wide uppercase">
          {t.drivers}
        </h2>
        <button className="btn-primary" onClick={openAdd}>
          + {t.add_driver}
        </button>
      </div>

      {/* Filters */}
      <div className="card flex flex-wrap gap-3 items-end">
        <div>
          <label className="label">{t.status}</label>
          <select
            className="input-field w-36"
            value={filters.status}
            onChange={e => setFilters(f => ({ ...f, status: e.target.value }))}
          >
            <option value="">All</option>
            <option value="active">{t.active}</option>
            <option value="inactive">{t.inactive}</option>
          </select>
        </div>
        <div>
          <label className="label">{t.name || 'Name'}</label>
          <input
            className="input-field w-44"
            placeholder="Search name…"
            value={filters.name}
            onChange={e => setFilters(f => ({ ...f, name: e.target.value }))}
          />
        </div>
        <button className="btn-secondary" onClick={() => setFilters({ status: '', name: '' })}>
          Clear
        </button>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        {loading ? (
          <p className="p-5 text-ink-400 font-body text-sm">{t.loading}</p>
        ) : drivers.length === 0 ? (
          <p className="p-5 text-ink-400 font-body text-sm">{t.no_data}</p>
        ) : (
          <table className="w-full text-sm font-body">
            <thead className="bg-slate border-b border-slate-border">
              <tr>
                {['Name', 'Phone', 'License', 'Primary Vehicle', t.status, t.actions].map(h => (
                  <th key={h} className="text-left px-4 py-3 font-display text-xs tracking-widest uppercase text-ink-400">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-border">
              {drivers.map(d => (
                <tr key={d.id} className="table-row-hover">
                  <td className="px-4 py-3 font-medium text-ink">{d.name}</td>
                  <td className="px-4 py-3 text-ink-400">{d.phone_number || '—'}</td>
                  <td className="px-4 py-3 text-ink-400">{d.license_number}</td>
                  <td className="px-4 py-3 text-ink-400">
                    {vehicles.find(v => v.id === d.primary_vehicle)?.registered_number || '—'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={d.status === 'active' ? 'badge-active' : 'badge-inactive'}>
                      {d.status === 'active' ? t.active : t.inactive}
                    </span>
                  </td>
                  <td className="px-4 py-3 flex gap-2">
                    <button className="btn-secondary text-xs py-1 px-3" onClick={() => openEdit(d)}>{t.edit}</button>
                    <button className="btn-danger text-xs py-1 px-3" onClick={() => setDelTarget(d)}>{t.delete}</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Add Modal */}
      {modal?.mode === 'add' && (
        <Modal title={t.add_driver || 'Add Driver'} onClose={() => { setModal(null); setApiError('') }}>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 max-h-[75vh] overflow-y-auto pr-1">

            {/* ── Driver Info ── */}
            <p className="text-xs font-display uppercase tracking-widest text-ink-400 border-b border-slate-border pb-1">
              Driver Info
            </p>

            <div>
              <label className="label">Full Name *</label>
              <input className="input-field" placeholder="Ramesh Kumar"
                {...register('name', { required: 'Required' })} />
              {errors.name && <p className="text-rust text-xs mt-1">{errors.name.message}</p>}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">License Number *</label>
                <input className="input-field" placeholder="MH0120230001234"
                  {...register('license_number', { required: 'Required' })} />
                {errors.license_number && <p className="text-rust text-xs mt-1">{errors.license_number.message}</p>}
              </div>
              <div>
                <label className="label">Phone Number *</label>
                <input className="input-field" placeholder="9876543210"
                  {...register('phone_number', {
                    required: 'Required',
                    pattern: { value: /^\d{10}$/, message: 'Must be 10 digits' }
                  })} />
                {errors.phone_number && <p className="text-rust text-xs mt-1">{errors.phone_number.message}</p>}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Primary Vehicle (optional)</label>
                <select className="input-field" {...register('primary_vehicle')}>
                  <option value="">— None —</option>
                  {vehicles.map(v => (
                    <option key={v.id} value={v.id}>
                      {v.registered_number}{v.model ? ` — ${v.model}` : ''}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">{t.status}</label>
                <select className="input-field" {...register('status')}>
                  <option value="active">{t.active}</option>
                  <option value="inactive">{t.inactive}</option>
                </select>
              </div>
            </div>

            {/* ── User Account ── */}
            <p className="text-xs font-display uppercase tracking-widest text-ink-400 border-b border-slate-border pb-1 mt-2">
              Login Account
            </p>

            <div>
              <label className="label">Email *</label>
              <input type="email" className="input-field" placeholder="driver@company.com"
                {...register('user_email', { required: 'Required' })} />
              {errors.user_email && <p className="text-rust text-xs mt-1">{errors.user_email.message}</p>}
            </div>

            <div>
              <label className="label">Username *</label>
              <input className="input-field" placeholder="ramesh_kumar"
                {...register('user_username', { required: 'Required' })} />
              {errors.user_username && <p className="text-rust text-xs mt-1">{errors.user_username.message}</p>}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Password *</label>
                <input type="password" className="input-field" placeholder="Min 8 chars"
                  {...register('user_password', { required: 'Required', minLength: { value: 8, message: 'Min 8 chars' } })} />
                {errors.user_password && <p className="text-rust text-xs mt-1">{errors.user_password.message}</p>}
              </div>
              <div>
                <label className="label">Confirm Password *</label>
                <input type="password" className="input-field" placeholder="Repeat password"
                  {...register('user_password2', {
                    required: 'Required',
                    validate: v => v === password || 'Passwords do not match'
                  })} />
                {errors.user_password2 && <p className="text-rust text-xs mt-1">{errors.user_password2.message}</p>}
              </div>
            </div>

            {apiError && (
              <p className="text-rust font-body text-xs bg-rust/5 border border-rust/20 rounded px-3 py-2">
                {apiError}
              </p>
            )}

            <div className="flex gap-2 pt-2">
              <button type="submit" disabled={isSubmitting} className="btn-primary">
                {isSubmitting ? 'Creating…' : 'Create Driver'}
              </button>
              <button type="button" className="btn-secondary" onClick={() => { setModal(null); setApiError('') }}>
                {t.cancel}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Edit Modal — only driver metadata fields */}
      {modal?.mode === 'edit' && (
        <Modal title={t.edit_driver || 'Edit Driver'} onClose={() => { setModal(null); setApiError('') }}>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">

            <div>
              <label className="label">Full Name *</label>
              <input className="input-field" {...register('name', { required: 'Required' })} />
              {errors.name && <p className="text-rust text-xs mt-1">{errors.name.message}</p>}
            </div>

            <div>
              <label className="label">Phone Number *</label>
              <input className="input-field"
                {...register('phone_number', {
                  required: 'Required',
                  pattern: { value: /^\d{10}$/, message: 'Must be 10 digits' }
                })} />
              {errors.phone_number && <p className="text-rust text-xs mt-1">{errors.phone_number.message}</p>}
            </div>

            {/* license shown but disabled — cannot change after creation */}
            <div>
              <label className="label">License Number</label>
              <input
                className="input-field bg-slate-soft cursor-not-allowed text-ink-400"
                value={modal.data.license_number}
                disabled
              />
              <p className="text-xs text-ink-400 mt-1">License cannot be changed after creation.</p>
            </div>

            <div>
              <label className="label">Primary Vehicle</label>
              <select className="input-field" {...register('primary_vehicle')}>
                <option value="">— None —</option>
                {vehicles.map(v => (
                  <option key={v.id} value={v.id}>
                    {v.registered_number}{v.model ? ` — ${v.model}` : ''}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">{t.status}</label>
              <select className="input-field" {...register('status')}>
                <option value="active">{t.active}</option>
                <option value="inactive">{t.inactive}</option>
              </select>
            </div>

            {apiError && (
              <p className="text-rust font-body text-xs bg-rust/5 border border-rust/20 rounded px-3 py-2">
                {apiError}
              </p>
            )}

            <div className="flex gap-2 pt-2">
              <button type="submit" disabled={isSubmitting} className="btn-primary">{t.save}</button>
              <button type="button" className="btn-secondary" onClick={() => { setModal(null); setApiError('') }}>{t.cancel}</button>
            </div>
          </form>
        </Modal>
      )}

      {/* Delete confirm */}
      {delTarget && (
        <Modal title={t.delete} onClose={() => setDelTarget(null)}>
          <p className="font-body text-sm text-ink-400 mb-4">{t.confirm_del}</p>
          <p className="font-body font-medium text-ink mb-5">{delTarget.name}</p>
          <div className="flex gap-2">
            <button className="btn-danger" onClick={confirmDelete}>{t.delete}</button>
            <button className="btn-secondary" onClick={() => setDelTarget(null)}>{t.cancel}</button>
          </div>
        </Modal>
      )}
    </div>
  )
}

function Modal({ title, onClose, children }) {
  const modalRoot = (
    <div
      className="fixed inset-0 bg-ink/40 flex items-center justify-center z-50 p-4 overflow-y-auto"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg w-full max-w-lg p-6 shadow-xl my-auto"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-display text-lg font-bold tracking-wide uppercase text-ink">{title}</h3>
          <button onClick={onClose} className="text-ink-300 hover:text-ink text-xl leading-none">×</button>
        </div>
        {children}
      </div>
    </div>
  );

  return createPortal(modalRoot, document.body);
}
