import { apiRequest } from "../js/api.js";
import { isAdmin } from "../js/auth.js";

export async function renderDrivers(container) {
  container.innerHTML = "Loading...";

  const { data } = await apiRequest("/api/drivers/");

  if (!data || !data.results) {
    container.innerHTML = "<p>Failed to load drivers.</p>";
    return;
  }

  let html = "<h3>Drivers</h3>";

  if (isAdmin()) {
    html += '<button id="addDriverBtn">Add Driver</button>';
  }

  html += "<table><tr><th>Name</th><th>License</th><th>Status</th><th>Actions</th></tr>";

  data.results.forEach(d => {
    html += "<tr>";
    html += "<td>" + d.name + "</td>";
    html += "<td>" + d.license_number + "</td>";
    html += "<td>" + d.status + "</td>";
    html += "<td>";
    if (isAdmin()) {
      html += '<button class="editDriverBtn" data-id="' + d.id + '" data-name="' + d.name + '" data-license="' + d.license_number + '" data-status="' + d.status + '">Edit</button> ';
      html += '<button class="deleteDriverBtn" data-id="' + d.id + '" data-name="' + d.name + '">Delete</button>';
    }
    html += "</td></tr>";
  });

  html += "</table>";

  // edit modal
  html += '<div id="driverModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:100;">';
  html += '<div style="background:white;width:360px;margin:120px auto;padding:24px;border-radius:8px;">';
  html += '<h4 id="driverModalTitle"></h4>';
  html += '<label>Full Name</label><br><input id="dName" placeholder="e.g. Ramesh Kumar" maxlength="100" style="width:100%;margin-bottom:12px;padding:8px;box-sizing:border-box;"><br>';
  html += '<label>License Number</label><br><input id="dLicense" placeholder="e.g. MH0120230001234" maxlength="15" style="width:100%;margin-bottom:12px;padding:8px;box-sizing:border-box;"><br>';
  html += '<label>Status</label><br><select id="dStatus" style="width:100%;margin-bottom:16px;padding:8px;"><option value="active">Active</option><option value="inactive">Inactive</option></select><br>';
  html += '<button id="driverModalSave">Save</button> <button id="driverModalCancel">Cancel</button>';
  html += '<p id="driverModalError" style="color:red;margin-top:8px;"></p>';
  html += '</div></div>';

  // delete confirm modal
  html += '<div id="driverDeleteModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:100;">';
  html += '<div style="background:white;width:320px;margin:160px auto;padding:24px;border-radius:8px;">';
  html += '<p id="driverDeleteMsg" style="margin-bottom:16px;"></p>';
  html += '<button id="driverDeleteConfirm">Delete</button> <button id="driverDeleteCancel">Cancel</button>';
  html += '</div></div>';

  container.innerHTML = html;

  const modal       = document.getElementById("driverModal");
  const deleteModal = document.getElementById("driverDeleteModal");
  let editingId     = null;

  function openModal(title, name, license, status) {
    document.getElementById("driverModalTitle").textContent = title;
    document.getElementById("dName").value       = name    || "";
    document.getElementById("dLicense").value    = license || "";
    document.getElementById("dLicense").disabled = editingId !== null;
    document.getElementById("dStatus").value     = status  || "active";
    document.getElementById("driverModalError").textContent = "";
    modal.style.display = "block";
  }

  function closeModal() {
    modal.style.display = "none";
    editingId = null;
  }

  modal.addEventListener("click", e => { if (e.target === modal) closeModal(); });

  const addBtn = document.getElementById("addDriverBtn");
  if (addBtn) {
    addBtn.addEventListener("click", () => {
      editingId = null;
      openModal("Add Driver", "", "", "active");
    });
  }

  document.querySelectorAll(".editDriverBtn").forEach(btn => {
    btn.addEventListener("click", () => {
      editingId = btn.dataset.id;
      openModal("Edit Driver", btn.dataset.name, btn.dataset.license, btn.dataset.status);
    });
  });

  document.getElementById("driverModalSave").addEventListener("click", async () => {
    const name    = document.getElementById("dName").value.trim();
    const license = document.getElementById("dLicense").value.trim().toUpperCase();
    const status  = document.getElementById("dStatus").value;
    const errEl   = document.getElementById("driverModalError");

    if (!name || !license) { errEl.textContent = "Name and license are required."; return; }

    const url     = editingId ? `/api/drivers/${editingId}/` : "/api/drivers/";
    const method  = editingId ? "PATCH" : "POST";
    const payload = { name, license_number: license, status };

    const { response, data } = await apiRequest(url, method, payload);

    if (response.ok) {
      closeModal();
      renderDrivers(container);
    } else {
      errEl.textContent = Object.values(data || {}).flat().join(" ") || "Something went wrong.";
    }
  });

  document.getElementById("driverModalCancel").addEventListener("click", closeModal);

  document.querySelectorAll(".deleteDriverBtn").forEach(btn => {
    btn.addEventListener("click", () => {
      const id   = btn.dataset.id;
      const name = btn.dataset.name;
      document.getElementById("driverDeleteMsg").textContent =
        `Delete driver "${name}"? This cannot be undone.`;
      deleteModal.style.display = "block";

      document.getElementById("driverDeleteConfirm").onclick = async () => {
        const { response } = await apiRequest(`/api/drivers/${id}/`, "DELETE");
        if (response.ok) {
          deleteModal.style.display = "none";
          renderDrivers(container);
        }
      };

      document.getElementById("driverDeleteCancel").onclick = () => {
        deleteModal.style.display = "none";
      };
    });
  });

  deleteModal.addEventListener("click", e => {
    if (e.target === deleteModal) deleteModal.style.display = "none";
  });
}
