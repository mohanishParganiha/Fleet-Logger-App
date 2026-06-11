import { useState, useEffect, useCallback, useRef } from 'react'
import { createPortal } from 'react-dom'
import { useForm } from 'react-hook-form'
import { useLang } from '../../context/LangContext'
import { useAuth } from '../../context/AuthContext'
import api from '../../hooks/useApi'

export default function Trips() {
  const { t } = useLang()
  const { user } = useAuth()

  const [trips, setTrips]             = useState([])
  const [vehicles, setVehicles]       = useState([])
  const [myDriver, setMyDriver]       = useState(null)   // driver profile of logged-in user
  const [loading, setLoading]         = useState(true)
  const [driverLoading, setDriverLoading] = useState(true)
  const [modal, setModal]             = useState(null)
  const [delTarget, setDelTarget]     = useState(null)
  const [calcModal, setCalcModal]     = useState(null)
  const [filters, setFilters]         = useState({ start_date: '', end_date: '', vehicle: '' })
  const [apiError, setApiError]       = useState('')

  const { register, handleSubmit, reset, setValue, formState: { errors, isSubmitting } } = useForm()
  const calcForm = useForm()
  const userId = user?.id ?? user?.user_id

  // ── fetch logged-in user's driver profile ──
  useEffect(() => {
    if (!userId) return
    setDriverLoading(true)
    // drivers list filtered by the linked user — backend returns driver linked to this user
    api.get('/drivers/', { params: { user: userId } })
      .then(res => {
        const results = res.data.results || []
        // find driver whose user matches logged-in user id
        const found = results.find(d => d.user?.id === userId || d.user === userId) || results[0]
        setMyDriver(found || null)
      })
      .catch(() => setMyDriver(null))
      .finally(() => setDriverLoading(false))
  }, [userId])

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = {}
      if (filters.start_date) params.start_date = filters.start_date
      if (filters.end_date)   params.end_date   = filters.end_date
      if (filters.vehicle)    params.vehicle     = filters.vehicle
      const [tRes, vRes] = await Promise.all([
        api.get('/trip-logs/', { params }),
        api.get('/vehicles/', { params: { status: 'active' } }),
      ])
      setTrips(tRes.data.results    || [])
      setVehicles(vRes.data.results || [])
    } finally { setLoading(false) }
  }, [filters])

  useEffect(() => { load() }, [load])

  function openAdd() {
    setApiError('')

    // 1. Find the actual database ID of your primary vehicle from the active vehicles array
    const primaryRegNum = myDriver?.primary_vehicle_detail?.registered_number || myDriver?.primary_vehicle || ''
    const matchingVehicle = vehicles.find(v => String(v.id) === String(myDriver?.primary_vehicle) || v.registered_number === primaryRegNum)
    const primaryVehicleId = matchingVehicle ? matchingVehicle.id : ''

    // 2. Format the driver string
    const driverLabel = myDriver ? `${myDriver.name} (${myDriver.license_number})` : 'Loading driver profile...'

    reset({
      date_time:         '',
      driver:            driverLabel, // Changed key name to match your Modal form register
      vehicle:           primaryVehicleId, // Sets the ID so the dropdown matches perfectly
      number_of_trips:   '',
      weight:            '',
      volume:            '',
      distance_traveled: '',
      pick_up:           '',
      drop_off:          '',
      diesel_fill:       '',
      last_reason_to_change: '',
    })
    setModal({ mode: 'add' })
  }

  function openEdit(trip) {
  setApiError('')
  reset({
    date_time:         trip.date_time?.slice(0, 16) || '',
    vehicle:           trip.vehicle?.id || '', // Changed from trip.vehicle?.registered_number
    number_of_trips:   trip.number_of_trips,
    weight:            trip.weight            || '',
    volume:            trip.volume            || '',
    distance_traveled: trip.distance_traveled || '',
    pick_up:           trip.pick_up           || '',
    drop_off:          trip.drop_off          || '',
    diesel_fill:       trip.diesel_fill       || '',
    last_reason_to_change: '',
  })
  setModal({ mode: 'edit', data: trip })
}

  async function onSubmit(data, signatureDataUrl) {
    setApiError('')
    if (!hasLoadMetric(data)) {
      setApiError(t.weight_or_volume_required || 'Weight or volume is required.')
      return
    }

    // Find the real registration number based on the selected vehicle ID dropdown
    const selectedVehicle = vehicles.find(v => String(v.id) === String(data.vehicle))

    const payload = {
      date_time:       data.date_time,
      driver:          myDriver?.license_number, // Sends raw license number to API
      number_of_trips: Number(data.number_of_trips),
    }

    if (selectedVehicle)         payload.vehicle           = selectedVehicle.registered_number
    if (data.weight)            payload.weight            = data.weight
    if (data.volume)            payload.volume            = data.volume
    if (data.distance_traveled) payload.distance_traveled = data.distance_traveled
    if (data.pick_up)           payload.pick_up           = data.pick_up
    if (data.drop_off)          payload.drop_off          = data.drop_off
    if (data.diesel_fill)       payload.diesel_fill       = data.diesel_fill
    if (modal.mode === 'edit')  payload.last_reason_to_change = data.last_reason_to_change?.trim()

    try {
      if (modal.mode === 'add') {
        await api.post('/trip-logs/', payload)
      } else {
        await api.patch(`/trip-logs/${modal.data.id}/`, payload)
      }
      if (signatureDataUrl) {
        const link = document.createElement('a')
        link.href = signatureDataUrl
        link.download = `signature_${Date.now()}.png`
        link.click()
      }
      setModal(null)
      load()
    } catch (err) {
      const d = err.response?.data
      setApiError(d ? Object.values(d).flat().join(' ') : 'Something went wrong.')
    }
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
        <button
          className="btn-primary"
          onClick={openAdd}
          disabled={driverLoading || !myDriver}
          title={!myDriver ? 'No driver profile linked to your account' : ''}
        >
          + Log Trip
        </button>
      </div>

      {!driverLoading && !myDriver && (
        <div className="card border border-amber/30 bg-amber/5">
          <p className="text-amber font-body text-sm">
            ⚠ Your account is not linked to a driver profile. Ask an admin to link your account.
          </p>
        </div>
      )}

      {/* Filters */}
      <div className="card flex flex-wrap gap-3 items-end">
        <div>
          <label className="label">{t.start_date || 'From'}</label>
          <input type="date" className="input-field w-40" value={filters.start_date}
            onChange={e => setFilters(f => ({ ...f, start_date: e.target.value }))} />
        </div>
        <div>
          <label className="label">{t.end_date || 'To'}</label>
          <input type="date" className="input-field w-40" value={filters.end_date}
            onChange={e => setFilters(f => ({ ...f, end_date: e.target.value }))} />
        </div>
        <div>
          <label className="label">{t.vehicle || 'Vehicle'}</label>
          <input className="input-field w-36" placeholder={t.reg_no_placeholder || 'Reg no.'} value={filters.vehicle}
            onChange={e => setFilters(f => ({ ...f, vehicle: e.target.value }))} />
        </div>
        <button className="btn-secondary" onClick={() => setFilters({ start_date: '', end_date: '', vehicle: '' })}>{t.clear || 'Clear'}</button>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-x-auto">
        {loading ? (
          <p className="p-5 text-ink-400 font-body text-sm">{t.loading}</p>
        ) : trips.length === 0 ? (
          <p className="p-5 text-ink-400 font-body text-sm">{t.no_data}</p>
        ) : (
          <table className="w-full text-sm font-body min-w-[980px]">
            <thead className="bg-slate border-b border-slate-border">
              <tr>
                {[t.date, t.vehicle, t.driver, t.trip_count, t.weight_t, t.volume_ft, t.distance_km, t.approved, t.actions].map(h => (
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
                  <td className="px-4 py-3 text-ink-400">{tr.volume            ?? '—'}</td>
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
        <TripModal
          mode={modal.mode}
          trip={modal.data}
          myDriver={myDriver}
          vehicles={vehicles}
          register={register}
          handleSubmit={handleSubmit}
          setValue={setValue} // <-- Add this line here
          errors={errors}
          isSubmitting={isSubmitting}
          apiError={apiError}
          onSubmit={onSubmit}
          onClose={() => { setModal(null); setApiError('') }}
          t={t}
        />
      )}

      {/* Calculate Modal */}
      {calcModal && (
        <Modal title="Calculate Rate" onClose={() => setCalcModal(null)}>
          <form onSubmit={calcForm.handleSubmit(onCalcSubmit)} className="space-y-4">
            <div>
              <label className="label">{t.calc_type || 'Calc Type'}</label>
              <select className="input-field" {...calcForm.register('calc_type')}>
                <option value="weight">{t.weight_t || 'Weight (T)'}</option>
                <option value="distance">{t.distance_km || 'Distance (km)'}</option>
              </select>
            </div>
            <div>
              <label className="label">{t.rate || 'Rate'} (₹ per unit)</label>
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

// ── Trip Add/Edit Modal with signature pad ──
// ── Trip Add/Edit Modal with signature pad ──
function TripModal({ mode, trip, myDriver, vehicles, register, handleSubmit, errors, isSubmitting, apiError, onSubmit, onClose, t, setValue }) { // <-- Added setValue to props
  const canvasRef  = useRef(null)
  const drawing    = useRef(false)
  const [hasSig, setHasSig] = useState(false)

  // Force autofill when the modal mounts
  useEffect(() => {
    if (mode === 'add' && myDriver) {
      // 1. Format Driver text
      const driverLabel = `${myDriver.name} (${myDriver.license_number})`
      setValue('driver', driverLabel)

      // 2. Find and set Primary Vehicle ID
      const primaryRegNum = myDriver?.primary_vehicle_detail?.registered_number || myDriver?.primary_vehicle || ''
      const matchingVehicle = vehicles.find(v => String(v.id) === String(myDriver?.primary_vehicle) || v.registered_number === primaryRegNum)
      if (matchingVehicle) {
        setValue('vehicle', matchingVehicle.id)
      }
    }
  }, [mode, myDriver, vehicles, setValue])

  function startDraw(e) {
    e.preventDefault()
    drawing.current = true
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const pos = getPos(e, canvas)
    ctx.beginPath()
    ctx.moveTo(pos.x, pos.y)
  }

  function draw(e) {
    e.preventDefault()
    if (!drawing.current) return
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const pos = getPos(e, canvas)
    ctx.lineTo(pos.x, pos.y)
    ctx.strokeStyle = '#0F172A'
    ctx.lineWidth   = 2
    ctx.lineCap     = 'round'
    ctx.lineJoin    = 'round'
    ctx.stroke()
    setHasSig(true)
  }

  function stopDraw() { drawing.current = false }

  function clearSig() {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    setHasSig(false)
  }

  function handleFormSubmit(data) {
    const canvas = canvasRef.current
    const sigDataUrl = hasSig ? getOpaqueSignatureDataUrl(canvas) : null
    onSubmit(data, sigDataUrl)
  }

  // primary vehicle registered_number for default
  const defaultVehicle = myDriver?.primary_vehicle_detail?.registered_number || ''

  const modalRoot = (
    <div
      className="fixed inset-0 bg-ink/40 flex items-center justify-center z-50 p-4 overflow-y-auto"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg w-full max-w-lg shadow-xl flex flex-col my-auto"
        style={{ maxHeight: '90vh' }}
        onClick={e => e.stopPropagation()}
      >
        {/* Modal header */}
        <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b border-slate-border shrink-0">
          <h3 className="font-display text-lg font-bold tracking-wide uppercase text-ink">
            {mode === 'add' ? 'Log Trip' : 'Edit Trip'}
          </h3>
          <button onClick={onClose} className="text-ink-300 hover:text-ink text-xl leading-none">×</button>
        </div>

        {/* Scrollable body */}
        <div className="overflow-y-auto flex-1 px-6 py-4">
          <form id="trip-form" onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">

            <div>
              <label className="label">{t.date_time || 'Date & Time'} *</label>
              <input type="datetime-local" className="input-field"
                {...register('date_time', { required: t.required || 'Required' })} />
              {errors.date_time && <p className="text-rust text-xs mt-1">{errors.date_time.message}</p>}
            </div>

            {/* Driver — readOnly ensures it submits data while remaining un-editable */}
            <div>
              <label className="label">{t.driver || 'Driver'}</label>
              <input
                type="text"
                className="input-field bg-slate border-slate-border cursor-not-allowed text-ink-400 font-medium"
                readOnly
                {...register('driver')}
              />
              <p className="text-xs text-ink-400 mt-1">{t.auto_filled_profile || 'Auto-filled from your profile.'}</p>
            </div>

            {/* Vehicle — Dropdown autofills primary, but remains fully customizable */}
            <div>
              <label className="label">{t.vehicle || 'Vehicle'}</label>
              <select
              className="input-field"
              {...register('vehicle')}
            >
              <option value="">— {t.none || 'None'} —</option>
              {vehicles.map(v => (
                /* Change value from v.registered_number to v.id */
                <option key={v.id} value={v.id}>
                  {v.registered_number}{v.model ? ` — ${v.model}` : ''}
                  {v.registered_number === defaultVehicle ? ` (${t.primary || 'primary'})` : ''}
                </option>
              ))}
            </select>
            </div>

            <div>
              <label className="label">{t.number_of_trips || 'Number of Trips'} *</label>
              <input type="number" min="1" className="input-field"
                {...register('number_of_trips', { required: t.required || 'Required', min: { value: 1, message: t.required_min_1 || 'Min 1' } })} />
              {errors.number_of_trips && <p className="text-rust text-xs mt-1">{errors.number_of_trips.message}</p>}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">{t.weight_t || 'Weight (T)'}</label>
                <input
                  type="number"
                  step="0.01"
                  className="input-field"
                  {...register('weight')}
                />
              </div>
              <div>
                <label className="label">{t.volume_ft || 'Volume (ft)'}</label>
                <input
                  type="number"
                  step="0.01"
                  className="input-field"
                  {...register('volume')}
                />
              </div>
            </div>

            <div>
              <label className="label">{t.distance_km || 'Distance (km)'} *</label>
              <input
                type="number"
                step="0.01"
                className="input-field"
                {...register('distance_traveled', { required: t.required || 'Required' })}
              />
              {errors.distance_traveled && <p className="text-rust text-xs mt-1">{errors.distance_traveled.message}</p>}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">{t.pick_up || 'Pick Up'}</label>
                <input className="input-field" {...register('pick_up')} />
              </div>
              <div>
                <label className="label">{t.drop_off || 'Drop Off'}</label>
                <input className="input-field" {...register('drop_off')} />
              </div>
            </div>

            <div>
              <label className="label">{t.diesel_fill_l || 'Diesel Fill (L)'}</label>
              <input type="number" step="0.01" className="input-field" {...register('diesel_fill')} />
            </div>

            {mode === 'edit' && (
              <div>
                <label className="label">{t.reason_for_change || 'Reason for Change'} *</label>
                <textarea
                  rows={3}
                  className="input-field resize-none"
                  placeholder={t.reason_for_change_placeholder || 'Explain why this trip log is being updated'}
                  {...register('last_reason_to_change', {
                    required: mode === 'edit' ? (t.required || 'Required') : false,
                    validate: value => mode !== 'edit' || Boolean(value?.trim()) || (t.required || 'Required'),
                  })}
                />
                {errors.last_reason_to_change && (
                  <p className="text-rust text-xs mt-1">{errors.last_reason_to_change.message}</p>
                )}
              </div>
            )}

            {/* ── Signature Pad ── */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="label mb-0">{t.signature || 'Signature'}</label>
                <button
                  type="button"
                  onClick={clearSig}
                  className="text-xs text-ink-400 hover:text-rust transition-colors"
                >
                  Clear
                </button>
              </div>
              <div className="border border-slate-border rounded bg-slate-soft">
                <canvas
                  ref={canvasRef}
                  width={440}
                  height={120}
                  className="w-full touch-none cursor-crosshair rounded"
                  onMouseDown={startDraw}
                  onMouseMove={draw}
                  onMouseUp={stopDraw}
                  onMouseLeave={stopDraw}
                  onTouchStart={startDraw}
                  onTouchMove={draw}
                  onTouchEnd={stopDraw}
                />
              </div>
            </div>

            {apiError && (
              <p className="text-rust font-body text-xs bg-rust/5 border border-rust/20 rounded px-3 py-2">
                {apiError}
              </p>
            )}
          </form>
        </div>

        {/* Footer buttons — always visible */}
        <div className="flex gap-2 px-6 py-4 border-t border-slate-border shrink-0">
          <button type="submit" form="trip-form" disabled={isSubmitting} className="btn-primary">
            {isSubmitting ? 'Saving…' : t.save}
          </button>
          <button type="button" className="btn-secondary" onClick={onClose}>{t.cancel}</button>
        </div>
      </div>
    </div>
  );

  return createPortal(modalRoot, document.body);
}

function Modal({ title, onClose, children }) {
  const modalRoot = (
    <div
      className="fixed inset-0 bg-ink/40 flex items-center justify-center z-50 p-4 overflow-y-auto"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg w-full max-w-md p-6 shadow-xl my-auto"
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

function getPos(e, canvas) {
  const rect = canvas.getBoundingClientRect()
  const touch = e.touches?.[0]
  const clientX = touch ? touch.clientX : e.clientX
  const clientY = touch ? touch.clientY : e.clientY
  return {
    x: (clientX - rect.left) * (canvas.width / rect.width),
    y: (clientY - rect.top) * (canvas.height / rect.height),
  }
}

function getOpaqueSignatureDataUrl(canvas) {
  const out = document.createElement('canvas')
  out.width = canvas.width
  out.height = canvas.height
  const ctx = out.getContext('2d')
  ctx.fillStyle = '#FFFFFF'
  ctx.fillRect(0, 0, out.width, out.height)
  ctx.drawImage(canvas, 0, 0)
  return out.toDataURL('image/png')
}

function hasLoadMetric(data) {
  return String(data.weight ?? '').trim() !== '' || String(data.volume ?? '').trim() !== ''
}
