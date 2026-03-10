/* ═══════════════════════════════════════════════
   FLEET LOGGER — app.js
═══════════════════════════════════════════════ */

// ── STATE ──────────────────────────────────────
const AUTH = {
  token:    null,
  username: '',
  is_staff: false,
};

let API_BASE = 'http://3.110.86.158'

// ── DEBOUNCE ───────────────────────────────────
const _debounceTimers = {};
function debounceLoad(fnName) {
  clearTimeout(_debounceTimers[fnName]);
  _debounceTimers[fnName] = setTimeout(() => window[fnName](), 380);
}

// ── TOAST ──────────────────────────────────────
function toast(msg, type = 'success', duration = 3500) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `show ${type}`;
  clearTimeout(el._timer);
  el._timer = setTimeout(() => { el.className = ''; }, duration);
}

// ── HELPERS ────────────────────────────────────
function fmt(val, fallback = '—') {
  return (val !== null && val !== undefined && val !== '') ? val : fallback;
}

function fmtDate(dt) {
  if (!dt) return '—';
  return new Date(dt).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
}

function statusBadge(s) {
  const cls = s === 'active' ? 'badge-green' : 'badge-red';
  return `<span class="badge ${cls}">${s}</span>`;
}

function loadingRow(cols) {
  return `<tr class="table-loading"><td colspan="${cols}"><span class="spinner"></span>Loading...</td></tr>`;
}

function emptyRow(cols, msg = 'No records found') {
  return `<tr class="table-empty"><td colspan="${cols}">${msg}</td></tr>`;
}

// ── API ────────────────────────────────────────
async function api(path, method = 'GET', body = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (AUTH.token) headers['Authorization'] = `Token ${AUTH.token}`;

  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(`${API_BASE}${path}`, opts);

  // 401 means token expired or revoked — force logout
  if (res.status === 401 && path !== '/api/login/') {
  // Only logout if not already on login request
  AUTH.token = null;
  showLoginScreen();
  toast('Session expired. Please log in again.', 'error');
  return { ok: false, status: 401, data: null };
}

  let data = null;
  try {
  const data = await res.json();
} catch (error) {
  console.error('Failed to parse response:', error);
  return { ok: false, data: [] };
}
  return { ok: res.ok, status: res.status, data };
}

// Fetches ALL pages from a paginated DRF endpoint and returns a flat array.
// DRF pagination returns { count, next, previous, results: [...] }
async function apiGetAll(path) {
  let results = [];
  // path already has query params, append page param correctly
  const sep = path.includes('?') ? '&' : '?';
  let url = `${path}${sep}page=1&page_size=1000`; // request large page to minimise round trips

  while (url) {
    const res = await fetch(url.startsWith('http') ? url : `${API_BASE}${url}`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${AUTH.token}`,
      },
    });

    if (res.status === 401) {
      doLogout();
      toast('Session expired. Please log in again.', 'error');
      return { ok: false, data: [] };
    }

    const data = await res.json();

    if (!res.ok) return { ok: false, data: [] };

    // If paginated, accumulate results and follow next link
    if (data.results !== undefined) {
      results = results.concat(data.results);
      // data.next is a full URL or null
      url = data.next || null;
    } else {
      // Non-paginated response — plain array
      results = Array.isArray(data) ? data : [];
      url = null;
    }
  }

  return { ok: true, data: results };
}

function updateBase(val) {
  API_BASE = val.replace(/\/$/, '');
}

// ── LOGIN ──────────────────────────────────────
async function doLogin() {
  const btn      = document.getElementById('login-btn');
  const errEl    = document.getElementById('login-error');
  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value;

  errEl.style.display = 'none';

  if (!username || !password) {
    errEl.textContent = 'Username and password are required.';
    errEl.style.display = 'block';
    return;
  }

  btn.textContent = 'Authenticating...';
  btn.disabled    = true;

  try {
    const res = await fetch(`${API_BASE}/api/login/`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ username, password }),
    });

    const data = await res.json();

    if (res.ok) {
      AUTH.token    = data.token;
      AUTH.username = data.username;
      AUTH.is_staff = data.is_staff;
      _onLoginSuccess();
    } else {
      errEl.textContent = data?.error || 'Invalid credentials.';
      errEl.style.display = 'block';
    }
  } catch (_) {
    errEl.textContent = 'Cannot reach server. Make sure your Django server is running.';
    errEl.style.display = 'block';
  }

  btn.textContent = 'Log In';
  btn.disabled    = false;
}

function _onLoginSuccess() {
  document.getElementById('header-username').textContent = AUTH.username;
  document.getElementById('header-role').textContent     = AUTH.is_staff ? 'Admin' : 'Staff';
  document.getElementById('api-base-input').value        = API_BASE;

  // Admin-only buttons: Add Vehicle, Add Driver
  ['btn-add-vehicle', 'btn-add-driver'].forEach(id => {
    document.getElementById(id).style.display = AUTH.is_staff ? '' : 'none';
  });

  document.getElementById('login-screen').style.display = 'none';
  document.getElementById('app').style.display          = 'flex';
  loadVehicles();
}

document.getElementById('login-password').addEventListener('keydown', e => {
  if (e.key === 'Enter') doLogin();
});

function doLogout() {
  AUTH.token    = null;
  AUTH.username = '';
  AUTH.is_staff = false;

  document.getElementById('login-screen').style.display = 'flex';
  document.getElementById('app').style.display          = 'none';
  document.getElementById('login-username').value       = '';
  document.getElementById('login-password').value       = '';
}

// ── TABS ───────────────────────────────────────
function switchTab(btn) {
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  btn.classList.add('active');
  const tab = btn.dataset.tab;
  document.getElementById(`section-${tab}`).classList.add('active');
  if (tab === 'vehicles')  loadVehicles();
  if (tab === 'drivers')   loadDrivers();
  if (tab === 'trips')     loadTrips();
}

// ── MODALS ─────────────────────────────────────
function openModal(id)  { document.getElementById(id).classList.add('show'); }
function closeModal(id) { document.getElementById(id).classList.remove('show'); }

document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', e => {
    if (e.target === overlay) overlay.classList.remove('show');
  });
});

// ── VEHICLES ───────────────────────────────────
async function loadVehicles() {
  const tbody = document.getElementById('vehicle-tbody');
  tbody.innerHTML = loadingRow(6);

  let url = '/api/vehicles/?';
  const status = document.getElementById('vehicle-status-filter').value;
  const reg    = document.getElementById('vehicle-reg-filter').value.trim();
  if (status) url += `status=${encodeURIComponent(status)}&`;
  if (reg)    url += `registered_number=${encodeURIComponent(reg)}&`;

  const { ok, data } = await apiGetAll(url);
  if (!ok) {
    tbody.innerHTML = `<tr><td colspan="6" style="color:var(--red);padding:20px 16px;">Failed to load vehicles.</td></tr>`;
    return;
  }

  const vehicles = data;
  document.getElementById('vehicle-count').textContent = `${vehicles.length} vehicle(s)`;

  if (!vehicles.length) { tbody.innerHTML = emptyRow(6, 'No vehicles found'); return; }

  tbody.innerHTML = vehicles.map(v => `
    <tr>
      <td class="td-mono">${v.id}</td>
      <td class="td-mono td-amber">${v.registered_number}</td>
      <td>${fmt(v.model)}</td>
      <td>${statusBadge(v.status)}</td>
      <td class="td-muted">${fmtDate(v.date_created)}</td>
      <td class="td-actions">
        ${AUTH.is_staff
          ? `<button class="btn btn-sm" onclick="editVehicle(${v.id})">Edit</button>
             <button class="btn btn-sm btn-danger" onclick="confirmDelete('vehicle',${v.id},'${v.registered_number}')">Delete</button>`
          : '<span class="td-muted">—</span>'}
      </td>
    </tr>
  `).join('');
}

function openVehicleModal(v = null) {
  document.getElementById('vehicle-id').value  = v?.id                ?? '';
  document.getElementById('v-reg').value       = v?.registered_number ?? '';
  document.getElementById('v-model').value     = v?.model             ?? '';
  document.getElementById('v-status').value    = v?.status            ?? 'active';
  document.getElementById('vehicle-modal-title').textContent = v ? 'Edit Vehicle' : 'Add Vehicle';
  openModal('vehicle-modal');
}

async function editVehicle(id) {
  const { ok, data } = await api(`/api/vehicles/${id}/`);
  if (ok) openVehicleModal(data);
  else toast('Could not load vehicle', 'error');
}

async function saveVehicle() {
  const id      = document.getElementById('vehicle-id').value;
  const payload = {
    registered_number: document.getElementById('v-reg').value.trim().toUpperCase(),
    model:             document.getElementById('v-model').value.trim(),
    status:            document.getElementById('v-status').value,
  };

  if (!payload.registered_number) { toast('Registered number is required', 'error'); return; }

  const { ok, data } = await api(
    id ? `/api/vehicles/${id}/` : '/api/vehicles/',
    id ? 'PATCH' : 'POST',
    payload
  );

  if (ok) {
    toast(id ? 'Vehicle updated' : 'Vehicle added', 'success');
    closeModal('vehicle-modal');
    loadVehicles();
  } else {
    const msg = Object.values(data || {}).flat().join(' ') || 'Something went wrong';
    toast(`Error: ${msg}`, 'error', 5000);
  }
}

function clearVehicleFilters() {
  document.getElementById('vehicle-status-filter').value = '';
  document.getElementById('vehicle-reg-filter').value    = '';
  loadVehicles();
}

// ── DRIVERS ────────────────────────────────────
async function loadDrivers() {
  const tbody = document.getElementById('driver-tbody');
  tbody.innerHTML = loadingRow(6);

  let url = '/api/drivers/?';
  const status = document.getElementById('driver-status-filter').value;
  const name   = document.getElementById('driver-name-filter').value.trim();
  if (status) url += `status=${encodeURIComponent(status)}&`;
  if (name)   url += `name=${encodeURIComponent(name)}&`;

  const { ok, data } = await apiGetAll(url);
  if (!ok) {
    tbody.innerHTML = `<tr><td colspan="6" style="color:var(--red);padding:20px 16px;">Failed to load drivers.</td></tr>`;
    return;
  }

  const drivers = data;
  document.getElementById('driver-count').textContent = `${drivers.length} driver(s)`;

  if (!drivers.length) { tbody.innerHTML = emptyRow(6, 'No drivers found'); return; }

  tbody.innerHTML = drivers.map(d => `
    <tr>
      <td class="td-mono">${d.id}</td>
      <td>${d.name}</td>
      <td class="td-mono td-amber">${d.license_number}</td>
      <td>${statusBadge(d.status)}</td>
      <td class="td-muted">${fmtDate(d.date_created)}</td>
      <td class="td-actions">
        ${AUTH.is_staff
          ? `<button class="btn btn-sm" onclick="editDriver(${d.id})">Edit</button>
             <button class="btn btn-sm btn-danger" onclick="confirmDelete('driver',${d.id},'${d.name}')">Delete</button>`
          : '<span class="td-muted">—</span>'}
      </td>
    </tr>
  `).join('');
}

function openDriverModal(d = null) {
  document.getElementById('driver-id').value   = d?.id             ?? '';
  document.getElementById('d-name').value      = d?.name           ?? '';
  document.getElementById('d-license').value   = d?.license_number ?? '';
  document.getElementById('d-status').value    = d?.status         ?? 'active';
  document.getElementById('driver-modal-title').textContent = d ? 'Edit Driver' : 'Add Driver';
  openModal('driver-modal');
}

async function editDriver(id) {
  const { ok, data } = await api(`/api/drivers/${id}/`);
  if (ok) openDriverModal(data);
  else toast('Could not load driver', 'error');
}

async function saveDriver() {
  const id      = document.getElementById('driver-id').value;
  const payload = {
    name:           document.getElementById('d-name').value.trim(),
    license_number: document.getElementById('d-license').value.trim().toUpperCase(),
    status:         document.getElementById('d-status').value,
  };

  if (!payload.name || !payload.license_number) {
    toast('Name and License are required', 'error');
    return;
  }

  const { ok, data } = await api(
    id ? `/api/drivers/${id}/` : '/api/drivers/',
    id ? 'PATCH' : 'POST',
    payload
  );

  if (ok) {
    toast(id ? 'Driver updated' : 'Driver added', 'success');
    closeModal('driver-modal');
    loadDrivers();
  } else {
    const msg = Object.values(data || {}).flat().join(' ') || 'Something went wrong';
    toast(`Error: ${msg}`, 'error', 5000);
  }
}

function clearDriverFilters() {
  document.getElementById('driver-status-filter').value = '';
  document.getElementById('driver-name-filter').value   = '';
  loadDrivers();
}

// ── TRIPS ──────────────────────────────────────
async function loadTrips() {
  const tbody = document.getElementById('trip-tbody');
  tbody.innerHTML = loadingRow(11);

  let url = '/api/trip-logs/?';
  const vehicle = document.getElementById('trip-vehicle-filter').value.trim();
  const driver  = document.getElementById('trip-driver-filter').value.trim();
  const from    = document.getElementById('trip-date-from').value;
  const to      = document.getElementById('trip-date-to').value;
  if (vehicle) url += `vehicle=${encodeURIComponent(vehicle)}&`;
  if (driver)  url += `driver=${encodeURIComponent(driver)}&`;
  if (from)    url += `date_time__date__gte=${from}&`;
  if (to)      url += `date_time__date__lte=${to}&`;

  const { ok, data } = await apiGetAll(url);
  if (!ok) {
    tbody.innerHTML = `<tr><td colspan="11" style="color:var(--red);padding:20px 16px;">Failed to load trips.</td></tr>`;
    return;
  }

  const trips = data;
  document.getElementById('trip-count').textContent = `${trips.length} record(s)`;

  if (!trips.length) { tbody.innerHTML = emptyRow(11, 'No trip logs found'); return; }

  tbody.innerHTML = trips.map(t => `
    <tr>
      <td class="td-mono">${t.id}</td>
      <td class="td-muted" style="white-space:nowrap;">${fmtDate(t.date_time)}</td>
      <td class="td-mono td-amber">${t.vehicle}</td>
      <td>${t.driver}</td>
      <td class="td-mono" style="text-align:center;">${t.number_of_trips}</td>
      <td class="td-mono">${fmt(t.weight)}</td>
      <td class="td-mono">${fmt(t.distance_traveled)}</td>
      <td class="td-muted">${fmt(t.pick_up)}</td>
      <td class="td-muted">${fmt(t.drop_off)}</td>
      <td class="td-mono">${fmt(t.diesel_fill)}</td>
      <td class="td-actions">
        <button class="btn btn-sm" onclick="editTrip(${t.id})">Edit</button>
        <button class="btn btn-sm btn-danger" onclick="confirmDelete('trip',${t.id},'Trip #${t.id}')">Delete</button>
      </td>
    </tr>
  `).join('');
}

function openTripModal(t = null) {
  document.getElementById('trip-id').value    = t?.id                ?? '';
  document.getElementById('t-datetime').value = t?.date_time         ? t.date_time.slice(0, 16) : '';
  document.getElementById('t-vehicle').value  = t?.vehicle           ?? '';
  document.getElementById('t-driver').value   = t?.driver            ?? '';
  document.getElementById('t-trips').value    = t?.number_of_trips   ?? '';
  document.getElementById('t-weight').value   = t?.weight            ?? '';
  document.getElementById('t-distance').value = t?.distance_traveled ?? '';
  document.getElementById('t-pickup').value   = t?.pick_up           ?? '';
  document.getElementById('t-dropoff').value  = t?.drop_off          ?? '';
  document.getElementById('t-diesel').value   = t?.diesel_fill       ?? '';
  document.getElementById('trip-modal-title').textContent = t ? 'Edit Trip' : 'Log Trip';
  openModal('trip-modal');
}

async function editTrip(id) {
  const { ok, data } = await api(`/api/trip-logs/${id}/`);
  if (ok) openTripModal(data);
  else toast('Could not load trip', 'error');
}

async function saveTrip() {
  const id      = document.getElementById('trip-id').value;
  const payload = {
    date_time:       document.getElementById('t-datetime').value,
    vehicle:         document.getElementById('t-vehicle').value.trim().toUpperCase(),
    driver:          document.getElementById('t-driver').value.trim().toUpperCase(),
    number_of_trips: parseInt(document.getElementById('t-trips').value),
  };

  if (!payload.date_time || !payload.vehicle || !payload.driver || isNaN(payload.number_of_trips)) {
    toast('Date, Vehicle, Driver, and # of Trips are required', 'error');
    return;
  }

  const weight   = document.getElementById('t-weight').value;
  const distance = document.getElementById('t-distance').value;
  const pickup   = document.getElementById('t-pickup').value.trim();
  const dropoff  = document.getElementById('t-dropoff').value.trim();
  const diesel   = document.getElementById('t-diesel').value;

  if (weight)   payload.weight            = parseFloat(weight);
  if (distance) payload.distance_traveled = parseFloat(distance);
  if (pickup)   payload.pick_up           = pickup;
  if (dropoff)  payload.drop_off          = dropoff;
  if (diesel)   payload.diesel_fill       = parseFloat(diesel);

  const { ok, data } = await api(
    id ? `/api/trip-logs/${id}/` : '/api/trip-logs/',
    id ? 'PATCH' : 'POST',
    payload
  );

  if (ok) {
    toast(id ? 'Trip updated' : 'Trip logged', 'success');
    closeModal('trip-modal');
    loadTrips();
  } else {
    const msg = Object.values(data || {}).flat().join(' ') || 'Something went wrong';
    toast(`Error: ${msg}`, 'error', 6000);
  }
}

function clearTripFilters() {
  document.getElementById('trip-vehicle-filter').value = '';
  document.getElementById('trip-driver-filter').value  = '';
  document.getElementById('trip-date-from').value      = '';
  document.getElementById('trip-date-to').value        = '';
  loadTrips();
}

// ── DELETE ─────────────────────────────────────
function confirmDelete(type, id, label) {
  document.getElementById('delete-msg').textContent     = `Delete "${label}"?`;
  document.getElementById('delete-confirm-btn').onclick = () => doDelete(type, id);
  openModal('delete-modal');
}

async function doDelete(type, id) {
  const urlMap = {
    vehicle: `/api/vehicles/${id}/`,
    driver:  `/api/drivers/${id}/`,
    trip:    `/api/trip-logs/${id}/`,
  };

  const { ok } = await api(urlMap[type], 'DELETE');

  if (ok) {
    toast('Deleted successfully', 'success');
    closeModal('delete-modal');
    if (type === 'vehicle') loadVehicles();
    if (type === 'driver')  loadDrivers();
    if (type === 'trip')    loadTrips();
  } else {
    toast('Delete failed', 'error');
  }
}

// ── CALCULATE ──────────────────────────────────
async function calcSingle() {
  const id        = document.getElementById('calc-trip-id').value;
  const rate      = document.getElementById('calc-rate').value;
  const calc_type = document.getElementById('calc-type').value;
  const resultEl  = document.getElementById('single-result');

  if (!id || !rate) { toast('Trip ID and Rate are required', 'error'); return; }

  const { ok, data } = await api(`/api/trip-logs/${id}/calculate/`, 'POST', { rate, calc_type });
  resultEl.classList.add('show');

  if (ok) {
    resultEl.innerHTML = `
      <div class="calc-row"><span class="calc-label">Trip ID</span>        <span class="calc-val">#${data.trip_id}</span></div>
      <div class="calc-row"><span class="calc-label">Calc Type</span>      <span class="calc-val">${data.calc_type}</span></div>
      <div class="calc-row"><span class="calc-label">Rate</span>           <span class="calc-val">₹ ${data.rate}</span></div>
      <div class="calc-row"><span class="calc-label">Qty / Trip</span>     <span class="calc-val">${data.quantity_per_trip}</span></div>
      <div class="calc-row"><span class="calc-label">Total Quantity</span> <span class="calc-val">${data.total_quantity}</span></div>
      <div class="calc-row"><span class="calc-label">Total Amount</span>   <span class="calc-total">₹ ${Number(data.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span></div>
    `;
  } else {
    resultEl.innerHTML = `<div style="color:var(--red);font-size:13px;">Error: ${data?.error || 'Something went wrong'}</div>`;
  }
}

async function calcBulk() {
  const start_date = document.getElementById('bulk-start').value;
  const end_date   = document.getElementById('bulk-end').value;
  const rate       = document.getElementById('bulk-rate').value;
  const calc_type  = document.getElementById('bulk-type').value;
  const vehicle    = document.getElementById('bulk-vehicle').value.trim().toUpperCase();
  const resultEl   = document.getElementById('bulk-result');

  if (!start_date || !end_date || !rate) {
    toast('Start date, End date, and Rate are required', 'error');
    return;
  }

  const payload = { start_date, end_date, rate, calc_type };
  if (vehicle) payload.vehicle = vehicle;

  const { ok, data } = await api('/api/trip-logs/calculate-bulk/', 'POST', payload);
  resultEl.classList.add('show');

  if (ok) {
    const qty_key   = calc_type === 'weight' ? 'total_weight' : 'total_distance';
    const qty_label = calc_type === 'weight' ? 'Total Weight (T)' : 'Total Distance (km)';
    resultEl.innerHTML = `
      <div class="calc-row"><span class="calc-label">Period</span>         <span class="calc-val">${data.start_date} → ${data.end_date}</span></div>
      ${data.vehicle ? `<div class="calc-row"><span class="calc-label">Vehicle</span><span class="calc-val">${data.vehicle}</span></div>` : ''}
      <div class="calc-row"><span class="calc-label">Total Trips</span>    <span class="calc-val">${data.total_trips}</span></div>
      <div class="calc-row"><span class="calc-label">Calc Type</span>      <span class="calc-val">${data.calc_type}</span></div>
      <div class="calc-row"><span class="calc-label">${qty_label}</span>   <span class="calc-val">${data[qty_key]}</span></div>
      <div class="calc-row"><span class="calc-label">Rate</span>           <span class="calc-val">₹ ${data.rate}</span></div>
      <div class="calc-row"><span class="calc-label">Total Amount</span>   <span class="calc-total">₹ ${Number(data.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span></div>
    `;
  } else {
    resultEl.innerHTML = `<div style="color:var(--red);font-size:13px;">Error: ${data?.error || 'Something went wrong'}</div>`;
  }
}
