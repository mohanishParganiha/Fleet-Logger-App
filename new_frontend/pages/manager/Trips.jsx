import { useState, useEffect, useCallback } from 'react'
import { useForm } from 'react-hook-form'
import { useLang } from '../../context/LangContext'
import api from '../../hooks/useApi'

export default function Trips() {
  const { t } = useLang()
  const [trips, setTrips]       = useState([])
  const [vehicles, setVehicles] = useState([])
  const [drivers, setDrivers]   = useState([])
  const [loading, setLoading]   = useState(true)
  const [modal, setModal]       = useState(null)
  const [delTarget, setDelTarget] = useState(null)
  const [calcModal, setCalcModal] = useState(null) // { trip }
  const [filters, setFilters]   = useState({ start_date: '', end_date: '', vehicle: '' })

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm()
  const calcForm = useForm()

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = {}
      if (filters.start_date) params.start_date = filters.start_date
      if (filters.end_date)   params.end_date   = filters.end_date
      if (filters.vehicle)    params.vehicle     = filters.vehicle
      const [tRes, vRes, dRes] = await Promise.all([
        api.get('/trip-logs/', { params }),
        api.get('/vehicles/'),
        api.get('/drivers/'),
      ])
      setTrips(tRes.data.results    || [])
      setVehicles(vRes.data.results || [])
      setDrivers(dRes.data.results  || [])
    } finally { setLoading(false) }
  }, [filters])

  useEffect(() => { load() }, [load])

  function openAdd() {
    reset({ date_time: '', vehicle: '', driver: '', number_of_trips: '', weight: '', distance_traveled: '', pick_up: '', drop_off: '', diesel_fill: '' })
    setModal({ mode: 'add' })
  }

  function openEdit(trip) {
    reset({
      date_time:         trip.date_time?.slice(0, 16) || '',
      vehicle:           trip.vehicle?.registered_number || '',
      driver:            trip.driver?.license_number    || '',
      number_of_trips:   trip.number_of_trips,
      weight:            trip.weight            || '',
      distance_traveled: trip.distance_traveled || '',
      pick_up:           trip.pick_up           || '',
      drop_off:          trip.drop_off          || '',
      diesel_fill:       trip.diesel_fill       || '',
    })
    setModal({ mode: 'edit', data: trip })
  }

  async function onSubmit(data) {
    const payload = {
      date_time:       data.date_time,
      vehicle:         data.vehicle   || undefined,
      driver:          data.driver,
      number_of_trips: Number(data.number_of_trips),
    }
    if (data.weight)            payload.weight            = data.weight
    if (data.distance_traveled) payload.distance_traveled = data.distance_traveled
    if (data.pick_up)           payload.pick_up           = data.pick_up
    if (data.drop_off)          payload.drop_off          = data.drop_off
    if (data.diesel_fill)       payload.diesel_fill       = data.diesel_fill

    if (modal.mode === 'add') {
      await api.post('/trip-logs/', payload)
    } else {
      await api.patch(`/trip-logs/${modal.data.id}/`, payload)
    }
    setModal(null)
    load()
  }

  async function approveTrip(trip) {
    await api.post(`/trip-logs/${trip.id}/approve/`)
    load()
  }

  async function onCalcSubmit(data) {
    const res = await api.post(`/trip-logs/${calcModal.trip.id}/calculate/`, {
      rate:      data.rate,
      calc_type: data.calc_type,
    })
    alert(`Amount: ₹ ${Number(res.data.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`)
    setCalcModal(null)
  }

  async function confirmDelete() {
    await api.delete(`/trip-logs/${delTarget.id}/`)
    setDelTarget(null)
    load()
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-3xl font-bold text-ink tracking-wide uppercase">
          {t.trips || 'Trips'}
        </h2>
        <button className="btn-primary" onClick={openAdd}>+ Log Trip</button>
      </div>

      {/* Filters */}
      <div className="card flex flex-wrap gap-3 items-end">
        <div>
          <label className="label">From</label>
          <input type="date" className="input-field w-40" value={filters.start_date}
            onChange={e => setFilters(f => ({ ...f, start_date: e.target.value }))} />
        </div>
        <div>
          <label className="label">To</label>
          <input type="date" className="input-field w-40" value={filters.end_date}
            onChange={e => setFilters(f => ({ ...f, end_date: e.target.value }))} />
        </div>
        <div>
          <label className="label">Vehicle</label>
          <input className="input-field w-36" placeholder="Reg no." value={filters.vehicle}
            onChange={e => setFilters(f => ({ ...f, vehicle: e.target.value }))} />
        </div>
        <button className="btn-secondary" onClick={() => setFilters({ start_date: '', end_date: '', vehicle: '' })}>Clear</button>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-x-auto">
        {loading ? (
          <p className="p-5 text-ink-400 font-body text-sm">{t.loading}</p>
        ) : trips.length === 0 ? (
          <p className="p-5 text-ink-400 font-body text-sm">{t.no_data}</p>
        ) : (
          <table className="w-full text-sm font-body min-w-[900px]">
            <thead className="bg-slate border-b border-slate-border">
              <tr>
                {['Date', 'Vehicle', 'Driver', 'Trips', 'Weight(T)', 'Dist(km)', 'Approved', t.actions].map(h => (
                  <th key={h} className="text-left px-4 py-3 font-display text-xs tracking-widest uppercase text-ink-400">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-border">
              {trips.map(tr => (
                <tr key={tr.id} className="table-row-hover">
                  <td className="px-4 py-3 text-ink whitespace-nowrap">
                    {new Date(tr.date_time).toLocaleDateString('en-IN')}
                  </td>
                  <td className="px-4 py-3 text-ink-400">{tr.vehicle?.registered_number || '—'}</td>
                  <td className="px-4 py-3 text-ink-400">{tr.driver?.name || '—'}</td>
                  <td className="px-4 py-3 text-ink">{tr.number_of_trips}</td>
                  <td className="px-4 py-3 text-ink-400">{tr.weight            ?? '—'}</td>
                  <td className="px-4 py-3 text-ink-400">{tr.distance_traveled ?? '—'}</td>
                  <td className="px-4 py-3">
                    {tr.is_approved
                      ? <span className="badge-active">Yes</span>
                      : <span className="badge-inactive">No</span>}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1 flex-wrap">
                      <button className="btn-secondary text-xs py-1 px-2" onClick={() => openEdit(tr)}>{t.edit}</button>
                      {!tr.is_approved && (
                        <button className="btn-primary text-xs py-1 px-2" onClick={() => approveTrip(tr)}>Approve</button>
                      )}
                      <button className="btn-secondary text-xs py-1 px-2" onClick={() => { calcForm.reset({ calc_type: 'weight', rate: '' }); setCalcModal({ trip: tr }) }}>Calc</button>
                      <button className="btn-danger text-xs py-1 px-2" onClick={() => setDelTarget(tr)}>{t.delete}</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Add/Edit Modal */}
      {modal && (
        <Modal title={modal.mode === 'add' ? 'Log Trip' : 'Edit Trip'} onClose={() => setModal(null)}>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-3 max-h-[70vh] overflow-y-auto pr-1">
            <div>
              <label className="label">Date & Time *</label>
              <input type="datetime-local" className="input-field" {...register('date_time', { required: true })} />
              {errors.date_time && <p className="text-rust text-xs mt-1">Required</p>}
            </div>
            <div>
              <label className="label">Vehicle</label>
              <select className="input-field" {...register('vehicle')}>
                <option value="">— None —</option>
                {vehicles.map(v => (
                  <option key={v.id} value={v.registered_number}>{v.registered_number}{v.model ? ` — ${v.model}` : ''}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Driver *</label>
              <select className="input-field" {...register('driver', { required: true })}>
                <option value="">— Select —</option>
                {drivers.map(d => (
                  <option key={d.id} value={d.license_number}>{d.name} ({d.license_number})</option>
                ))}
              </select>
              {errors.driver && <p className="text-rust text-xs mt-1">Required</p>}
            </div>
            <div>
              <label className="label">Number of Trips *</label>
              <input type="number" min="0" className="input-field" {...register('number_of_trips', { required: true })} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Weight (T)</label>
                <input type="number" step="0.01" className="input-field" {...register('weight')} />
              </div>
              <div>
                <label className="label">Distance (km)</label>
                <input type="number" step="0.01" className="input-field" {...register('distance_traveled')} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Pick Up</label>
                <input className="input-field" {...register('pick_up')} />
              </div>
              <div>
                <label className="label">Drop Off</label>
                <input className="input-field" {...register('drop_off')} />
              </div>
            </div>
            <div>
              <label className="label">Diesel Fill (L)</label>
              <input type="number" step="0.01" className="input-field" {...register('diesel_fill')} />
            </div>
            <div className="flex gap-2 pt-2">
              <button type="submit" disabled={isSubmitting} className="btn-primary">{t.save}</button>
              <button type="button" className="btn-secondary" onClick={() => setModal(null)}>{t.cancel}</button>
            </div>
          </form>
        </Modal>
      )}

      {/* Calculate Modal */}
      {calcModal && (
        <Modal title="Calculate Rate" onClose={() => setCalcModal(null)}>
          <form onSubmit={calcForm.handleSubmit(onCalcSubmit)} className="space-y-4">
            <div>
              <label className="label">Calc Type</label>
              <select className="input-field" {...calcForm.register('calc_type')}>
                <option value="weight">Weight</option>
                <option value="distance">Distance</option>
              </select>
            </div>
            <div>
              <label className="label">Rate (₹ per unit)</label>
              <input type="number" step="0.01" className="input-field" placeholder="e.g. 500"
                {...calcForm.register('rate', { required: true })} />
            </div>
            <div className="flex gap-2 pt-2">
              <button type="submit" className="btn-primary">Calculate</button>
              <button type="button" className="btn-secondary" onClick={() => setCalcModal(null)}>{t.cancel}</button>
            </div>
          </form>
        </Modal>
      )}

      {/* Delete confirm */}
      {delTarget && (
        <Modal title={t.delete} onClose={() => setDelTarget(null)}>
          <p className="font-body text-sm text-ink-400 mb-4">{t.confirm_del}</p>
          <p className="font-body font-medium text-ink mb-5">Trip #{delTarget.id?.slice(0, 8)}…</p>
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
