import { useState, useEffect, useCallback } from 'react'
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

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm()

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
    reset({ name: '', license_number: '', status: 'active', primary_vehicle: '' })
    setModal({ mode: 'add' })
  }

  function openEdit(d) {
    reset({
      name: d.name,
      status: d.status,
      primary_vehicle: d.primary_vehicle || '',
    })
    setModal({ mode: 'edit', data: d })
  }

  async function onSubmit(data) {
    // strip empty primary_vehicle so backend gets null not ""
    if (!data.primary_vehicle) delete data.primary_vehicle
    if (modal.mode === 'add') {
      await api.post('/drivers/', data)
    } else {
      await api.patch(`/drivers/${modal.data.id}/`, data)
    }
    setModal(null)
    load()
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
                {['Name', 'License', 'Primary Vehicle', t.status, t.actions].map(h => (
                  <th key={h} className="text-left px-4 py-3 font-display text-xs tracking-widest uppercase text-ink-400">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-border">
              {drivers.map(d => (
                <tr key={d.id} className="table-row-hover">
                  <td className="px-4 py-3 font-medium text-ink">{d.name}</td>
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

      {/* Add/Edit Modal */}
      {modal && (
        <Modal title={modal.mode === 'add' ? (t.add_driver || 'Add Driver') : (t.edit_driver || 'Edit Driver')} onClose={() => setModal(null)}>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="label">Full Name</label>
              <input className="input-field" {...register('name', { required: true })} />
              {errors.name && <p className="text-rust text-xs mt-1">Required</p>}
            </div>

            {modal.mode === 'add' && (
              <div>
                <label className="label">License Number</label>
                <input
                  className="input-field"
                  placeholder="e.g. MH0120230001234"
                  {...register('license_number', { required: true })}
                />
                {errors.license_number && <p className="text-rust text-xs mt-1">Required</p>}
              </div>
            )}

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

            <div className="flex gap-2 pt-2">
              <button type="submit" disabled={isSubmitting} className="btn-primary">{t.save}</button>
              <button type="button" className="btn-secondary" onClick={() => setModal(null)}>{t.cancel}</button>
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
  return (
    <div className="fixed inset-0 bg-ink/40 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-lg w-full max-w-md p-6 shadow-xl" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-display text-lg font-bold tracking-wide uppercase text-ink">{title}</h3>
          <button onClick={onClose} className="text-ink-300 hover:text-ink text-xl leading-none">×</button>
        </div>
        {children}
      </div>
    </div>
  )
}
