import { apiRequest } from "../js/api.js";

export function renderBulk(container) {
  container.innerHTML = `
    <h3>Bulk Calculate</h3>

    <form id="bulkForm">
      <label>Start Date</label><br>
      <input name="start_date" type="date" style="margin-bottom:10px;padding:8px;width:220px;"><br>

      <label>End Date</label><br>
      <input name="end_date" type="date" style="margin-bottom:10px;padding:8px;width:220px;"><br>

      <label>Calc Type</label><br>
      <select name="calc_type" style="margin-bottom:10px;padding:8px;width:220px;">
        <option value="weight">Weight</option>
        <option value="distance">Distance</option>
      </select><br>

      <label>Rate (per unit)</label><br>
      <input name="rate" type="number" step="0.01" placeholder="e.g. 500"
        style="margin-bottom:10px;padding:8px;width:220px;"><br>

      <label>Vehicle (optional — reg number)</label><br>
      <input name="vehicle" placeholder="e.g. MH12AB1234"
        style="margin-bottom:16px;padding:8px;width:220px;"><br>

      <button type="submit">Calculate</button>
    </form>

    <div id="bulkResult" style="margin-top:20px;"></div>
  `;

  document.getElementById("bulkForm").onsubmit = async e => {
    e.preventDefault();

    const form      = new FormData(e.target);
    const resultEl  = document.getElementById("bulkResult");

    // Build JSON payload — only include vehicle if filled in
    const payload = {
      start_date: form.get("start_date"),
      end_date:   form.get("end_date"),
      calc_type:  form.get("calc_type"),
      rate:       form.get("rate"),
    };

    const vehicle = form.get("vehicle").trim();
    if (vehicle) payload.vehicle = vehicle.toUpperCase();

    // Validate required fields on frontend before hitting API
    if (!payload.start_date || !payload.end_date || !payload.rate) {
      resultEl.innerHTML = '<p style="color:red;">Start date, end date, and rate are required.</p>';
      return;
    }

    resultEl.innerHTML = "<p>Calculating...</p>";

    // POST with JSON body — not GET with query params
    const { response, data } = await apiRequest("/api/trip-logs/calculate-bulk/", "POST", payload);

    if (response.ok) {
      const qtyKey   = payload.calc_type === "weight" ? "total_weight" : "total_distance";
      const qtyLabel = payload.calc_type === "weight" ? "Total Weight (T)" : "Total Distance (km)";

      resultEl.innerHTML = `
        <table>
          <tr><th>Field</th><th>Value</th></tr>
          <tr><td>Period</td><td>${data.start_date} → ${data.end_date}</td></tr>
          ${data.vehicle ? `<tr><td>Vehicle</td><td>${data.vehicle}</td></tr>` : ""}
          <tr><td>Total Trips</td><td>${data.total_trips}</td></tr>
          <tr><td>Calc Type</td><td>${data.calc_type}</td></tr>
          <tr><td>${qtyLabel}</td><td>${data[qtyKey]}</td></tr>
          <tr><td>Rate</td><td>₹ ${data.rate}</td></tr>
          <tr><td><strong>Total Amount</strong></td><td><strong>₹ ${Number(data.total_amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</strong></td></tr>
        </table>
      `;
    } else {
      const msg = data?.error || Object.values(data || {}).flat().join(" ") || "Something went wrong.";
      resultEl.innerHTML = `<p style="color:red;">Error: ${msg}</p>`;
    }
  };
}
