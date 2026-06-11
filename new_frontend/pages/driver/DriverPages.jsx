import { useState, useEffect, useCallback, useRef } from 'react'
import { useForm } from 'react-hook-form'
import { useAuth } from '../../context/AuthContext'
import { useLang } from '../../context/LangContext'
import api from '../../hooks/useApi'

// ──────────────────────────────────────────────
// MyTrips — driver sees only their own trips
// ──────────────────────────────────────────────
export function MyTrips() {
  const { t } = useLang()
  const { user } = useAuth()
  const [trips, setTrips]     = useState([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      // The backend filters by driver linked to the logged-in user automatically
      const res = await api.get('/trip-logs/')
      setTrips(res.data.results || [])
    } finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  return (
    <div className="space-y-4">
      <h2 className="font-display text-2xl font-bold text-ink tracking-wide uppercase">
        {t.my_trips || 'My Trips'}
      </h2>

      {loading ? (
        <p className="text-ink-400 font-body text-sm">{t.loading}</p>
      ) : trips.length === 0 ? (
        <p className="text-ink-400 font-body text-sm">{t.no_data}</p>
      ) : (
        <div className="space-y-3">
          {trips.map(tr => (
            <TripCard key={tr.id} trip={tr} />
          ))}
        </div>
      )}
    </div>
  )
}

function TripCard({ trip }) {
  const { t } = useLang()
  return (
    <div className="card space-y-2">
      <div className="flex justify-between items-start">
        <div>
          <p className="font-display text-sm font-bold text-ink uppercase tracking-wide">
            {trip.vehicle?.registered_number || '—'}
          </p>
          <p className="font-body text-xs text-ink-400">
            {new Date(trip.date_time).toLocaleString('en-IN')}
          </p>
        </div>
        <span className={trip.is_approved ? 'badge-active' : 'badge-inactive'}>
          {trip.is_approved ? 'Approved' : 'Pending'}
        </span>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
        <Stat label={t.trip_count || 'Trips'} value={trip.number_of_trips} />
        <Stat label={t.weight_t || 'Weight (T)'} value={trip.weight ? `${trip.weight} T` : '—'} />
        <Stat label={t.volume_ft || 'Volume (ft)'} value={trip.volume ? `${trip.volume} ft` : '—'} />
        <Stat label={t.distance_short || 'Dist'} value={trip.distance_traveled ? `${trip.distance_traveled} km` : '—'} />
      </div>
      {(trip.pick_up || trip.drop_off) && (
        <p className="font-body text-xs text-ink-400">
          {trip.pick_up || '?'} → {trip.drop_off || '?'}
        </p>
      )}
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div className="text-center bg-slate rounded p-2">
      <p className="font-body text-xs text-ink-400">{label}</p>
      <p className="font-display text-sm font-bold text-ink">{value}</p>
    </div>
  )
}

// ──────────────────────────────────────────────
// LogTrip — driver logs a new trip
// ──────────────────────────────────────────────
export function LogTrip() {
  const { t } = useLang()
  const { user } = useAuth()
  const [vehicles, setVehicles] = useState([])
  const [myDriver, setMyDriver] = useState(null)
  const [loading, setLoading]   = useState(true)
  const [success, setSuccess]   = useState('')
  const [error, setError]       = useState('')
  const canvasRef               = useRef(null)
  const drawing                 = useRef(false)
  const [hasSig, setHasSig]     = useState(false)

  const { register, handleSubmit, reset, setValue, formState: { errors, isSubmitting } } = useForm()

  const userId = user?.id ?? user?.user_id

  useEffect(() => {
    if (!userId) {
      setLoading(false)
      return
    }

    setLoading(true)
    Promise.all([
      api.get('/vehicles/', { params: { status: 'active' } }),
      api.get('/drivers/',  { params: { status: 'active', user: userId } }),
    ]).then(([vRes, dRes]) => {
      const vehicleResults = vRes.data.results || []
      const driverResults = dRes.data.results || []
      const driver = driverResults.find(d => d.user?.id === userId || d.user === userId) || driverResults[0] || null

      setVehicles(vehicleResults)
      setMyDriver(driver)

      if (driver) {
        const primaryVehicle = findPrimaryVehicle(driver, vehicleResults)
        reset({
          date_time: '',
          driver: formatDriver(driver),
          vehicle: primaryVehicle?.registered_number || '',
          number_of_trips: '',
          weight: '',
          volume: '',
          distance_traveled: '',
          pick_up: '',
          drop_off: '',
          diesel_fill: '',
        })
      }
    }).catch(() => {
      setMyDriver(null)
      setError('Unable to load your driver profile.')
    }).finally(() => setLoading(false))
  }, [reset, userId])

  async function onSubmit(data) {
    setSuccess('')
    setError('')
    if (!hasLoadMetric(data)) {
      setError(t.weight_or_volume_required || 'Weight or volume is required.')
      return
    }
    try {
      const payload = {
        date_time:       data.date_time,
        driver:          myDriver?.license_number,
        number_of_trips: Number(data.number_of_trips),
      }
      if (data.vehicle)           payload.vehicle           = data.vehicle
      if (data.weight)            payload.weight            = data.weight
      if (data.volume)            payload.volume            = data.volume
      if (data.distance_traveled) payload.distance_traveled = data.distance_traveled
      if (data.pick_up)           payload.pick_up           = data.pick_up
      if (data.drop_off)          payload.drop_off          = data.drop_off
      if (data.diesel_fill)       payload.diesel_fill       = data.diesel_fill

      await api.post('/trip-logs/', payload)
      if (hasSig && canvasRef.current) downloadSignature(canvasRef.current)
      setSuccess('Trip logged successfully!')
      const primaryVehicle = findPrimaryVehicle(myDriver, vehicles)
      reset({
        date_time: '',
        driver: myDriver ? formatDriver(myDriver) : '',
        vehicle: primaryVehicle?.registered_number || '',
        number_of_trips: '',
        weight: '',
        volume: '',
        distance_traveled: '',
        pick_up: '',
        drop_off: '',
        diesel_fill: '',
      })
      clearSig()
    } catch (err) {
      const d = err.response?.data
      setError(d ? Object.values(d).flat().join(' ') : 'Something went wrong.')
    }
  }

  useEffect(() => {
    if (!myDriver) return
    const primaryVehicle = findPrimaryVehicle(myDriver, vehicles)
    setValue('driver', formatDriver(myDriver))
    setValue('vehicle', primaryVehicle?.registered_number || '')
  }, [myDriver, setValue, vehicles])

  function startDraw(e) {
    e.preventDefault()
    drawing.current = true
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const pos = getCanvasPos(e, canvas)
    ctx.beginPath()
    ctx.moveTo(pos.x, pos.y)
  }

  function draw(e) {
    e.preventDefault()
    if (!drawing.current) return
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const pos = getCanvasPos(e, canvas)
    ctx.lineTo(pos.x, pos.y)
    ctx.strokeStyle = '#0F172A'
    ctx.lineWidth = 2
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
    ctx.stroke()
    setHasSig(true)
  }

  function stopDraw() {
    drawing.current = false
  }

  function clearSig() {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    setHasSig(false)
  }

  if (loading) {
    return <p className="text-ink-400 font-body text-sm">{t.loading}</p>
  }

  return (
    <div className="space-y-5">
      <h2 className="font-display text-2xl font-bold text-ink tracking-wide uppercase">
        {t.log_trip || 'Log Trip'}
      </h2>

      {!myDriver && (
        <p className="text-rust font-body text-sm bg-rust/5 border border-rust/20 rounded px-3 py-2">
          Your account is not linked to an active driver profile.
        </p>
      )}

      <div className="card space-y-4">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="label">{t.date_time || 'Date & Time'} *</label>
            <input type="datetime-local" className="input-field"
              {...register('date_time', { required: true })} />
            {errors.date_time && <p className="text-rust text-xs mt-1">{t.required || 'Required'}</p>}
          </div>

          <div>
            <label className="label">{t.driver || 'Driver'} *</label>
            <input
              className="input-field bg-slate border-slate-border cursor-not-allowed text-ink-400 font-medium"
              readOnly
              {...register('driver', { required: true })}
            />
            {errors.driver && <p className="text-rust text-xs mt-1">{t.required || 'Required'}</p>}
          </div>

          <div>
            <label className="label">{t.vehicle || 'Vehicle'}</label>
            <select className="input-field" {...register('vehicle')}>
              <option value="">— {t.none || 'None'} —</option>
              {vehicles.map(v => (
                <option key={v.id} value={v.registered_number}>
                  {v.registered_number}{v.model ? ` — ${v.model}` : ''}
                  {isPrimaryVehicle(myDriver, v) ? ` (${t.primary || 'primary'})` : ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">{t.number_of_trips || 'Number of Trips'} *</label>
            <input type="number" min="0" className="input-field"
              {...register('number_of_trips', { required: true, min: 1 })} />
            {errors.number_of_trips && <p className="text-rust text-xs mt-1">{t.required_min_1 || 'Required, min 1'}</p>}
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
              {...register('distance_traveled', { required: true })}
            />
            {errors.distance_traveled && <p className="text-rust text-xs mt-1">{t.required || 'Required'}</p>}
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

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="label mb-0">{t.other_party_signature || 'Other Party Signature'}</label>
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
                width={520}
                height={150}
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

          <button type="submit" disabled={isSubmitting || !myDriver} className="btn-primary w-full">
            {isSubmitting ? 'Saving…' : t.log_trip || 'Log Trip'}
          </button>
        </form>
      </div>
    </div>
  )
}

function formatDriver(driver) {
  return driver ? `${driver.name} (${driver.license_number})` : ''
}

function getPrimaryVehicleNumber(driver) {
  const detail = driver?.primary_vehicle_detail
  if (detail?.registered_number) return detail.registered_number
  if (typeof driver?.primary_vehicle === 'object') return driver.primary_vehicle?.registered_number || ''
  return driver?.primary_vehicle || ''
}

function findPrimaryVehicle(driver, vehicles) {
  const primary = getPrimaryVehicleNumber(driver)
  return vehicles.find(v => String(v.id) === String(driver?.primary_vehicle) || v.registered_number === primary)
}

function isPrimaryVehicle(driver, vehicle) {
  return findPrimaryVehicle(driver, [vehicle])?.id === vehicle.id
}

function getCanvasPos(e, canvas) {
  const rect = canvas.getBoundingClientRect()
  const touch = e.touches?.[0]
  const clientX = touch ? touch.clientX : e.clientX
  const clientY = touch ? touch.clientY : e.clientY
  return {
    x: (clientX - rect.left) * (canvas.width / rect.width),
    y: (clientY - rect.top) * (canvas.height / rect.height),
  }
}

function downloadSignature(canvas) {
  const link = document.createElement('a')
  link.href = getOpaqueSignatureDataUrl(canvas)
  link.download = `signature_${Date.now()}.png`
  link.click()
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
