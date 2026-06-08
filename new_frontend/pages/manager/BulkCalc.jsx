import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useLang } from '../../context/LangContext'
import api from '../../hooks/useApi'

export default function BulkCalc() {
  const { t } = useLang()
  const [result, setResult]   = useState(null)
  const [error, setError]     = useState('')
  const { register, handleSubmit, formState: { isSubmitting } } = useForm()

  async function onSubmit(data) {
    setResult(null)
    setError('')
    try {
      const payload = {
        start_date: data.start_date,
        end_date:   data.end_date,
        calc_type:  data.calc_type,
        rate:       data.rate,
      }
      if (data.vehicle?.trim()) payload.vehicle = data.vehicle.trim().toUpperCase()
      const res = await api.post('/trip-logs/calculate-bulk/', payload)
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.error || 'Something went wrong.')
    }
  }

  const qtyKey   = result?.calc_type === 'weight' ? 'total_weight' : 'total_distance'
  const qtyLabel = result?.calc_type === 'weight' ? 'Total Weight (T)' : 'Total Distance (km)'

  return (
    <div className="space-y-6 max-w-lg">
      <h2 className="font-display text-3xl font-bold text-ink tracking-wide uppercase">
        {t.bulk_calc || 'Bulk Calculate'}
      </h2>

      <div className="card space-y-4">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Start Date</label>
              <input type="date" className="input-field" {...register('start_date', { required: true })} />
            </div>
            <div>
              <label className="label">End Date</label>
              <input type="date" className="input-field" {...register('end_date', { required: true })} />
            </div>
          </div>

          <div>
            <label className="label">Calc Type</label>
            <select className="input-field" {...register('calc_type', { required: true })}>
              <option value="weight">Weight</option>
              <option value="distance">Distance</option>
            </select>
          </div>

          <div>
            <label className="label">Rate (₹ per unit)</label>
            <input
              type="number"
              step="0.01"
              className="input-field"
              placeholder="e.g. 500"
              {...register('rate', { required: true })}
            />
          </div>

          <div>
            <label className="label">Vehicle Reg No. (optional)</label>
            <input
              className="input-field"
              placeholder="e.g. CG07XY1234"
              {...register('vehicle')}
            />
          </div>

          <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
            {isSubmitting ? 'Calculating…' : 'Calculate'}
          </button>
        </form>
      </div>

      {error && (
        <div className="card border border-rust/30 bg-rust/5">
          <p className="text-rust font-body text-sm">{error}</p>
        </div>
      )}

      {result && (
        <div className="card space-y-2">
          <h3 className="font-display text-lg font-bold text-ink uppercase tracking-wide mb-3">Result</h3>
          <Row label="Period"       value={`${result.start_date} → ${result.end_date}`} />
          {result.vehicle && <Row label="Vehicle" value={result.vehicle} />}
          <Row label="Total Trips"  value={result.total_trips} />
          <Row label="Calc Type"    value={result.calc_type} />
          <Row label={qtyLabel}     value={result[qtyKey]} />
          <Row label="Rate"         value={`₹ ${result.rate}`} />
          <div className="pt-2 border-t border-slate-border">
            <Row
              label="Total Amount"
              value={`₹ ${Number(result.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
              bold
            />
          </div>
        </div>
      )}
    </div>
  )
}

function Row({ label, value, bold = false }) {
  return (
    <div className="flex justify-between font-body text-sm">
      <span className="text-ink-400">{label}</span>
      <span className={bold ? 'font-bold text-ink' : 'text-ink'}>{value}</span>
    </div>
  )
}
