import { useState, useEffect, useCallback } from 'react'
import { useForm } from 'react-hook-form'
import { useLang } from '../../context/LangContext'
import api from '../../hooks/useApi'
import { createPortal } from 'react-dom'

export default function Vehicles() {
  const { t } = useLang()
  const [vehicles, setVehicles] = useState([])
  const [loading, setLoading]   = useState(true)
  const [modal, setModal]       = useState(null) // null | { mode: 'add'|'edit', data? }
  const [delTarget, setDelTarget] = useState(null)
  const [filters, setFilters]   = useState({ status: '', registered_number: '' })

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm()

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = {}
      if (filters.status) params.status = filters.status
      if (filters.registered_number) params.registered_number = filters.registered_number
      const res = await api.get('/vehicles/', { params })
      setVehicles(res.data.results || [])
    } finally { setLoading(false) }
  }, [filters])

  useEffect(() => { load() }, [load])

  function openAdd() {
    reset({ registered_number: '', model: '', status: 'active' })
    setModal({ mode: 'add' })
  }

  function openEdit(v) {
    reset({ model: v.model, status: v.status })
    setModal({ mode: 'edit', data: v })
  }

  async function onSubmit(data) {
    if (modal.mode === 'add') {
      await api.post('/vehicles/', data)
    } else {
      await api.patch(`/vehicles/${modal.data.id}/`, data)
    }
    setModal(null)
    load()
  }

  async function confirmDelete() {
    await api.delete(`/vehicles/${delTarget.id}/`)
    setDelTarget(null)
    load()
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="font-display text-3xl font-bold text-ink tracking-wide uppercase">
          {t.vehicles}
        </h2>
        <button className="btn-primary" onClick={openAdd}>
          + {t.add_vehicle}
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
          <label className="label">{t.reg_number}</label>
          <input
            className="input-field w-44"
            placeholder="e.g. CG07XY1234"
            value={filters.registered_number}
            onChange={e => setFilters(f => ({ ...f, registered_number: e.target.value }))}
          />
        </div>
        <button className="btn-secondary" onClick={() => setFilters({ status: '', registered_number: '' })}>
          Clear
        </button>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        {loading ? (
          <p className="p-5 text-ink-400 font-body text-sm">{t.loading}</p>
        ) : vehicles.length === 0 ? (
          <p className="p-5 text-ink-400 font-body text-sm">{t.no_data}</p>
        ) : (
          <table className="w-full text-sm font-body">
            <thead className="bg-slate border-b border-slate-border">
              <tr>
                {[t.reg_number, t.model, t.status, t.actions].map(h => (
                  <th key={h} className="text-left px-4 py-3 font-display text-xs tracking-widest uppercase text-ink-400">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-border">
              {vehicles.map(v => (
                <tr key={v.id} className="table-row-hover">
                  <td className="px-4 py-3 font-medium text-ink">{v.registered_number}</td>
                  <td className="px-4 py-3 text-ink-400">{v.model || '—'}</td>
                  <td className="px-4 py-3">
                    <span className={v.status === 'active' ? 'badge-active' : 'badge-inactive'}>
                      {v.status === 'active' ? t.active : t.inactive}
                    </span>
                  </td>
                  <td className="px-4 py-3 flex gap-2">
                    <button className="btn-secondary text-xs py-1 px-3" onClick={() => openEdit(v)}>{t.edit}</button>
                    <button className="btn-danger text-xs py-1 px-3" onClick={() => setDelTarget(v)}>{t.delete}</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Add/Edit Modal */}
      {modal && (
        <Modal title={modal.mode === 'add' ? t.add_vehicle : t.edit_vehicle} onClose={() => setModal(null)}>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {modal.mode === 'add' && (
              <div>
                <label className="label">{t.reg_number}</label>
                <input className="input-field" {...register('registered_number', { required: true })} />
                {errors.registered_number && <p className="text-rust text-xs mt-1">Required</p>}
              </div>
            )}
            <div>
              <label className="label">{t.model}</label>
              <input className="input-field" {...register('model')} />
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
          <p className="font-body font-medium text-ink mb-5">{delTarget.registered_number}</p>
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
    <div className="fixed inset-0 bg-ink/40 flex items-center justify-center z-50 p-4 overflow-y-auto" onClick={onClose}>
      <div className="bg-white rounded-lg w-full max-w-lg p-6 shadow-xl my-auto" onClick={e => e.stopPropagation()}>
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
