import {apiRequest} from "../js/api.js";
import {isAdmin} from "../js/auth.js";

export async function renderVehicles(container){

container.innerHTML="Loading...";

const {data}=await apiRequest("/api/vehicles");

let html="<h3>Vehicles</h3>";

if(isAdmin()){
html+=`<button id="createVehicle">Add Vehicle</button>`;
}

html+=`

<table>
<tr>
<th>Model</th>
<th>Number</th>
<th>Status</th>
<th>Actions</th>
</tr>
`;

data.results.forEach(v=>{

html+=`

<tr>
<td>${v.model}</td>
<td>${v.registered_number}</td>
<td>${v.status}</td>
<td>
${isAdmin()?`<button>Edit</button><button>Delete</button>`:""}
</td>
</tr>
`;

});

html+="</table>";

container.innerHTML=html;

}
