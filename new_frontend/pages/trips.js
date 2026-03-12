import { apiRequest } from "../js/api.js";

export async function renderTrips(container) {
  container.innerHTML = "Loading...";

  const { data } = await apiRequest("/api/trip-logs/");

  if (!data || !data.results) {
    container.innerHTML = "<p>Failed to load trips.</p>";
    return;
  }

  let html = "<h3>Trips</h3>";
  html += '<button id="addTripBtn">Log Trip</button>';
  html += "<table><tr><th>Date</th><th>Vehicle</th><th>Driver</th><th>Trips</th><th>Weight</th><th>Dist</th><th>Pickup</th><th>Dropoff</th><th>Diesel</th><th>Actions</th></tr>";

  data.results.forEach(t => {
    html += "<tr>";
    html += "<td>" + new Date(t.date_time).toLocaleString("en-IN") + "</td>";
    html += "<td>" + t.vehicle + "</td>";
    html += "<td>" + t.driver  + "</td>";
    html += "<td>" + t.number_of_trips + "</td>";
    html += "<td>" + (t.weight            || "-") + "</td>";
    html += "<td>" + (t.distance_traveled || "-") + "</td>";
    html += "<td>" + (t.pick_up           || "-") + "</td>";
    html += "<td>" + (t.drop_off          || "-") + "</td>";
    html += "<td>" + (t.diesel_fill       || "-") + "</td>";
    html += "<td>";
    html += '<button class="editTripBtn"'
      + ' data-id="'       + t.id                        + '"'
      + ' data-datetime="' + t.date_time.slice(0, 16)    + '"'
      + ' data-vehicle="'  + t.vehicle                   + '"'
      + ' data-driver="'   + t.driver                    + '"'
      + ' data-trips="'    + t.number_of_trips            + '"'
      + ' data-weight="'   + (t.weight            || "") + '"'
      + ' data-distance="' + (t.distance_traveled || "") + '"'
      + ' data-pickup="'   + (t.pick_up           || "") + '"'
      + ' data-dropoff="'  + (t.drop_off          || "") + '"'
      + ' data-diesel="'   + (t.diesel_fill       || "") + '">Edit</button> ';
    html += '<button class="deleteTripBtn" data-id="' + t.id + '">Delete</button>';
    html += "</td></tr>";
  });

  html += "</table>";
  html += '<div id="tripModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:100;overflow-y:auto;">'
    + '<div style="background:white;width:400px;margin:60px auto;padding:24px;border-radius:8px;">'
    + '<h4 id="tripModalTitle"></h4>'
    + '<label>Date and Time *</label><br>'
    + '<input id="tDatetime" type="datetime-local" style="width:100%;margin-bottom:10px;padding:8px;box-sizing:border-box;"><br>'
    + '<label>Vehicle *</label><br>'
    + '<select id="tVehicle" style="width:100%;margin-bottom:10px;padding:8px;box-sizing:border-box;"><option value="">Loading...</option></select><br>'
    + '<label>Driver *</label><br>'
    + '<select id="tDriver" style="width:100%;margin-bottom:10px;padding:8px;box-sizing:border-box;"><option value="">Loading...</option></select><br>'
    + '<label>Number of Trips *</label><br>'
    + '<input id="tTrips" type="number" min="0" style="width:100%;margin-bottom:10px;padding:8px;box-sizing:border-box;"><br>'
    + '<label>Weight (tonnes)</label><br>'
    + '<input id="tWeight" type="number" step="0.01" placeholder="optional" style="width:100%;margin-bottom:10px;padding:8px;box-sizing:border-box;"><br>'
    + '<label>Distance (km)</label><br>'
    + '<input id="tDistance" type="number" step="0.01" placeholder="optional" style="width:100%;margin-bottom:10px;padding:8px;box-sizing:border-box;"><br>'
    + '<label>Pick Up</label><br>'
    + '<input id="tPickup" placeholder="optional" style="width:100%;margin-bottom:10px;padding:8px;box-sizing:border-box;"><br>'
    + '<label>Drop Off</label><br>'
    + '<input id="tDropoff" placeholder="optional" style="width:100%;margin-bottom:10px;padding:8px;box-sizing:border-box;"><br>'
    + '<label>Diesel Fill (L)</label><br>'
    + '<input id="tDiesel" type="number" step="0.01" placeholder="optional" style="width:100%;margin-bottom:16px;padding:8px;box-sizing:border-box;"><br>'
    + '<button id="tripModalSave">Save</button> <button id="tripModalCancel">Cancel</button>'
    + '<p id="tripModalError" style="color:red;margin-top:8px;"></p>'
    + '</div></div>';

  html += '<div id="tripDeleteModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:100;">'
    + '<div style="background:white;width:320px;margin:160px auto;padding:24px;border-radius:8px;">'
    + '<p id="tripDeleteMsg" style="margin-bottom:16px;"></p>'
    + '<button id="tripDeleteConfirm">Delete</button> <button id="tripDeleteCancel">Cancel</button>'
    + '</div></div>';

  container.innerHTML = html;

  const modal       = document.getElementById("tripModal");
  const deleteModal = document.getElementById("tripDeleteModal");
  let editingId     = null;

  async function populateDropdowns(selectedVehicle, selectedDriver) {
    const vSelect = document.getElementById("tVehicle");
    const dSelect = document.getElementById("tDriver");

    const [vRes, dRes] = await Promise.all([
      apiRequest("/api/vehicles/"),
      apiRequest("/api/drivers/"),
    ]);

    if (vRes.data && vRes.data.results) {
      vSelect.innerHTML = '<option value="">-- Select Vehicle --</option>';
      vRes.data.results.forEach(function(v) {
        const opt = document.createElement("option");
        opt.value = v.registered_number;
        opt.textContent = v.registered_number + (v.model ? " - " + v.model : "") + (v.status === "inactive" ? " (inactive)" : "");
        if (v.registered_number === selectedVehicle) opt.selected = true;
        vSelect.appendChild(opt);
      });
    } else {
      vSelect.innerHTML = '<option value="">Failed to load vehicles</option>';
    }

    if (dRes.data && dRes.data.results) {
      dSelect.innerHTML = '<option value="">-- Select Driver --</option>';
      dRes.data.results.forEach(function(d) {
        const opt = document.createElement("option");
        opt.value = d.license_number;
        opt.textContent = d.name + " - " + d.license_number + (d.status === "inactive" ? " (inactive)" : "");
        if (d.license_number === selectedDriver) opt.selected = true;
        dSelect.appendChild(opt);
      });
    } else {
      dSelect.innerHTML = '<option value="">Failed to load drivers</option>';
    }
  }

  async function openModal(title, d) {
    d = d || {};
    document.getElementById("tripModalTitle").textContent = title;
    document.getElementById("tDatetime").value = d.datetime || "";
    document.getElementById("tTrips").value    = d.trips    || "";
    document.getElementById("tWeight").value   = d.weight   || "";
    document.getElementById("tDistance").value = d.distance || "";
    document.getElementById("tPickup").value   = d.pickup   || "";
    document.getElementById("tDropoff").value  = d.dropoff  || "";
    document.getElementById("tDiesel").value   = d.diesel   || "";
    document.getElementById("tripModalError").textContent = "";
    modal.style.display = "block";
    await populateDropdowns(d.vehicle || "", d.driver || "");
  }

  function closeModal() {
    modal.style.display = "none";
    editingId = null;
  }

  modal.addEventListener("click", function(e) { if (e.target === modal) closeModal(); });

  document.getElementById("addTripBtn").addEventListener("click", function() {
    editingId = null;
    openModal("Log Trip");
  });

  document.querySelectorAll(".editTripBtn").forEach(function(btn) {
    btn.addEventListener("click", function() {
      editingId = btn.dataset.id;
      openModal("Edit Trip", {
        datetime: btn.dataset.datetime,
        vehicle:  btn.dataset.vehicle,
        driver:   btn.dataset.driver,
        trips:    btn.dataset.trips,
        weight:   btn.dataset.weight,
        distance: btn.dataset.distance,
        pickup:   btn.dataset.pickup,
        dropoff:  btn.dataset.dropoff,
        diesel:   btn.dataset.diesel,
      });
    });
  });

  document.getElementById("tripModalSave").addEventListener("click", async function() {
    var errEl    = document.getElementById("tripModalError");
    var datetime = document.getElementById("tDatetime").value;
    var vehicle  = document.getElementById("tVehicle").value;
    var driver   = document.getElementById("tDriver").value;
    var trips    = document.getElementById("tTrips").value;

    if (!datetime || !vehicle || !driver || !trips) {
      errEl.textContent = "Date, vehicle, driver, and number of trips are required.";
      return;
    }

    var payload = {
      date_time:       datetime,
      vehicle:         vehicle,
      driver:          driver,
      number_of_trips: parseInt(trips),
    };

    var weight   = document.getElementById("tWeight").value;
    var distance = document.getElementById("tDistance").value;
    var pickup   = document.getElementById("tPickup").value.trim();
    var dropoff  = document.getElementById("tDropoff").value.trim();
    var diesel   = document.getElementById("tDiesel").value;

    if (weight)   payload.weight            = parseFloat(weight);
    if (distance) payload.distance_traveled = parseFloat(distance);
    if (pickup)   payload.pick_up           = pickup;
    if (dropoff)  payload.drop_off          = dropoff;
    if (diesel)   payload.diesel_fill       = parseFloat(diesel);

    var url    = editingId ? "/api/trip-logs/" + editingId + "/" : "/api/trip-logs/";
    var method = editingId ? "PATCH" : "POST";

    var result = await apiRequest(url, method, payload);

    if (result.response.ok) {
      closeModal();
      renderTrips(container);
    } else {
      errEl.textContent = Object.values(result.data || {}).flat().join(" ") || "Something went wrong.";
    }
  });

  document.getElementById("tripModalCancel").addEventListener("click", closeModal);

  document.querySelectorAll(".deleteTripBtn").forEach(function(btn) {
    btn.addEventListener("click", function() {
      var id = btn.dataset.id;
      document.getElementById("tripDeleteMsg").textContent = "Delete Trip #" + id + "? This cannot be undone.";
      deleteModal.style.display = "block";

      document.getElementById("tripDeleteConfirm").onclick = async function() {
        var result = await apiRequest("/api/trip-logs/" + id + "/", "DELETE");
        if (result.response.ok) {
          deleteModal.style.display = "none";
          renderTrips(container);
        }
      };

      document.getElementById("tripDeleteCancel").onclick = function() {
        deleteModal.style.display = "none";
      };
    });
  });

  deleteModal.addEventListener("click", function(e) {
    if (e.target === deleteModal) deleteModal.style.display = "none";
  });
}
