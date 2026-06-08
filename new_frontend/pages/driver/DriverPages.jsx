import { useState, useEffect, useCallback } from 'react'
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
      <div className="grid grid-cols-3 gap-2 pt-1">
        <Stat label="Trips"   value={trip.number_of_trips} />
        <Stat label="Weight"  value={trip.weight            ? `${trip.weight} T`  : '—'} />
        <Stat label="Dist"    value={trip.distance_traveled ? `${trip.distance_traveled} km` : '—'} />
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
  const [vehicles, setVehicles] = useState([])
  const [drivers, setDrivers]   = useState([])
  const [success, setSuccess]   = useState('')
  const [error, setError]       = useState('')

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm()

  useEffect(() => {
    Promise.all([
      api.get('/vehicles/', { params: { status: 'active' } }),
      api.get('/drivers/',  { params: { status: 'active' } }),
    ]).then(([vRes, dRes]) => {
      setVehicles(vRes.data.results || [])
      setDrivers(dRes.data.results  || [])
    })
  }, [])

  async function onSubmit(data) {
    setSuccess('')
    setError('')
    try {
      const payload = {
        date_time:       data.date_time,
        driver:          data.driver,
        number_of_trips: Number(data.number_of_trips),
      }
      if (data.vehicle)           payload.vehicle           = data.vehicle
      if (data.weight)            payload.weight            = data.weight
      if (data.distance_traveled) payload.distance_traveled = data.distance_traveled
      if (data.pick_up)           payload.pick_up           = data.pick_up
      if (data.drop_off)          payload.drop_off          = data.drop_off
      if (data.diesel_fill)       payload.diesel_fill       = data.diesel_fill

      await api.post('/trip-logs/', payload)
      setSuccess('Trip logged successfully!')
      reset()
    } catch (err) {
      const d = err.response?.data
      setError(d ? Object.values(d).flat().join(' ') : 'Something went wrong.')
    }
  }

  return (
    <div className="space-y-5">
      <h2 className="font-display text-2xl font-bold text-ink tracking-wide uppercase">
        {t.log_trip || 'Log Trip'}
      </h2>

      <div className="card space-y-4">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="label">Date & Time *</label>
            <input type="datetime-local" className="input-field"
              {...register('date_time', { required: true })} />
            {errors.date_time && <p className="text-rust text-xs mt-1">Required</p>}
          </div>

          <div>
            <label className="label">Driver *</label>
            <select className="input-field" {...register('driver', { required: true })}>
              <option value="">— Select —</option>
              {drivers.map(d => (
                <option key={d.id} value={d.license_number}>{d.name}</option>
              ))}
            </select>
            {errors.driver && <p className="text-rust text-xs mt-1">Required</p>}
          </div>

          <div>
            <label className="label">Vehicle (leave blank to use primary)</label>
            <select className="input-field" {...register('vehicle')}>
              <option value="">— Primary vehicle —</option>
              {vehicles.map(v => (
                <option key={v.id} value={v.registered_number}>
                  {v.registered_number}{v.model ? ` — ${v.model}` : ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">Number of Trips *</label>
            <input type="number" min="0" className="input-field"
              {...register('number_of_trips', { required: true, min: 1 })} />
            {errors.number_of_trips && <p className="text-rust text-xs mt-1">Required, min 1</p>}
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
            {isSubmitting ? 'Saving…' : t.log_trip || 'Log Trip'}
          </button>
        </form>
      </div>
    </div>
  )
}
