import {apiRequest} from "../js/api.js";
import {isAdmin} from "../js/auth.js";

export async function renderDrivers(container){

container.innerHTML="Loading...";

const {data}=await apiRequest("/api/drivers");

let html="<h3>Drivers</h3>";

html+=`

<table>
<tr>
<th>Name</th>
<th>License</th>
<th>Status</th>
<th>Actions</th>
</tr>
`;

data.results.forEach(d=>{

html+=`

<tr>
<td>${d.name}</td>
<td>${d.license_number}</td>
<td>${d.status}</td>
<td>
${isAdmin()?`<button>Edit</button><button>Delete</button>`:""}
</td>
</tr>
`;

});

html+="</table>";

container.innerHTML=html;

}
