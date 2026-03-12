import { apiRequest } from "../js/api.js";
import { isAdmin } from "../js/auth.js";

export async function renderVehicles(container) {
  container.innerHTML = "Loading...";

  const { data } = await apiRequest("/api/vehicles/");

  if (!data || !data.results) {
    container.innerHTML = "<p>Failed to load vehicles.</p>";
    return;
  }

  let html = `<h3>Vehicles</h3>`;

  if (isAdmin()) {
    html += `<button id="addVehicleBtn">Add Vehicle</button>`;
  }

  html += `
  <table>
    <tr><th>Model</th><th>Number</th><th>Status</th><th>Actions</th></tr>
  `;

  data.results.forEach(v => {
    html += `
    <tr>
      <td>${v.model || "—"}</td>
      <td>${v.registered_number}</td>
      <td>${v.status}</td>
      <td>${isAdmin() ? `
        <button class="editVehicleBtn"
          data-id="${v.id}" data-model="${v.model || ""}"
          data-number="${v.registered_number}" data-status="${v.status}">Edit</button>
        <button class="deleteVehicleBtn"
          data-id="${v.id}" data-number="${v.registered_number}">Delete</button>
      ` : ""}</td>
    </tr>`;
  });

  html += `</table>

  <div id="vehicleModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:100;">
    <div style="background:white;width:360px;margin:120px auto;padding:24px;border-radius:8px;">
      <h4 id="vehicleModalTitle"></h4>
      <label>Registered Number</label><br>
      <input id="vNumber" placeholder="e.g. MH12AB1234" maxlength="10"
        style="width:100%;margin-bottom:12px;padding:8px;box-sizing:border-box;"><br>
      <label>Model</label><br>
      <input id="vModel" placeholder="e.g. TATA Prima" maxlength="25"
        style="width:100%;margin-bottom:12px;padding:8px;box-sizing:border-box;"><br>
      <label>Status</label><br>
      <select id="vStatus" style="width:100%;margin-bottom:16px;padding:8px;">
        <option value="active">Active</option>
        <option value="inactive">Inactive</option>
      </select><br>
      <button id="vehicleModalSave">Save</button>
      <button id="vehicleModalCancel" style="margin-left:8px;">Cancel</button>
      <p id="vehicleModalError" style="color:red;margin-top:8px;"></p>
    </div>
  </div>

  <div id="vehicleDeleteModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:100;">
    <div style="background:white;width:320px;margin:160px auto;padding:24px;border-radius:8px;">
      <p id="vehicleDeleteMsg" style="margin-bottom:16px;"></p>
      <button id="vehicleDeleteConfirm">Delete</button>
      <button id="vehicleDeleteCancel" style="margin-left:8px;">Cancel</button>
    </div>
  </div>`;

  container.innerHTML = html;

  const modal       = document.getElementById("vehicleModal");
  const deleteModal = document.getElementById("vehicleDeleteModal");
  let editingId     = null;

  function openModal(title, number = "", model = "", status = "active") {
    document.getElementById("vehicleModalTitle").textContent = title;
    document.getElementById("vNumber").value     = number;
    document.getElementById("vNumber").disabled  = editingId !== null;
    document.getElementById("vModel").value      = model;
    document.getElementById("vStatus").value     = status;
    document.getElementById("vehicleModalError").textContent = "";
    modal.style.display = "block";
  }

  function closeModal() {
    modal.style.display = "none";
    editingId = null;
  }

  modal.addEventListener("click", e => { if (e.target === modal) closeModal(); });

  document.getElementById("addVehicleBtn")?.addEventListener("click", () => {
    editingId = null;
    openModal("Add Vehicle");
  });

  document.querySelectorAll(".editVehicleBtn").forEach(btn => {
    btn.addEventListener("click", () => {
      editingId = btn.dataset.id;
      openModal("Edit Vehicle", btn.dataset.number, btn.dataset.model, btn.dataset.status);
    });
  });

  document.getElementById("vehicleModalSave").addEventListener("click", async () => {
    const number  = document.getElementById("vNumber").value.trim().toUpperCase();
    const model   = document.getElementById("vModel").value.trim();
    const status  = document.getElementById("vStatus").value;
    const errEl   = document.getElementById("vehicleModalError");

    if (!number) { errEl.textContent = "Registered number is required."; return; }

    const url     = editingId ? `/api/vehicles/${editingId}/` : "/api/vehicles/";
    const method  = editingId ? "PATCH" : "POST";
    const payload = { registered_number: number, model, status };

    const { response, data } = await apiRequest(url, method, payload);

    if (response.ok) {
      closeModal();
      renderVehicles(container);
    } else {
      errEl.textContent = Object.values(data || {}).flat().join(" ") || "Something went wrong.";
    }
  });

  document.getElementById("vehicleModalCancel").addEventListener("click", closeModal);

  document.querySelectorAll(".deleteVehicleBtn").forEach(btn => {
    btn.addEventListener("click", () => {
      const id     = btn.dataset.id;
      const number = btn.dataset.number;
      document.getElementById("vehicleDeleteMsg").textContent =
        `Delete vehicle "${number}"? This cannot be undone.`;
      deleteModal.style.display = "block";

      document.getElementById("vehicleDeleteConfirm").onclick = async () => {
        const { response } = await apiRequest(`/api/vehicles/${id}/`, "DELETE");
        if (response.ok) {
          deleteModal.style.display = "none";
          renderVehicles(container);
        }
      };
      document.getElementById("vehicleDeleteCancel").onclick = () => {
        deleteModal.style.display = "none";
      };
    });
  });

  deleteModal.addEventListener("click", e => {
    if (e.target === deleteModal) deleteModal.style.display = "none";
  });
}
