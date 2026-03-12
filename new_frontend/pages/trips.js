import {apiRequest} from "../js/api.js";

export async function renderTrips(container){

container.innerHTML="Loading...";

const {data}=await apiRequest("/api/trip-logs");

let html="<h3>Trips</h3>";

html+=`

<table>
<tr>
<th>Date</th>
<th>Vehicle</th>
<th>Driver</th>
<th>Trips</th>
<th>Quantity</th>
<th>Diesel</th>
</tr>
`;

data.results.forEach(t=>{

let quantity="";

if(t.weight){
quantity=t.weight+" kg";
}

if(t.distance_traveled){
quantity=t.distance_traveled+" km";
}

html+=`

<tr>
<td>${t.date_time}</td>
<td>${t.vehicle_number}</td>
<td>${t.driver_name}</td>
<td>${t.number_of_trips}</td>
<td>${quantity}</td>
<td>${t.diesel_fill||""}</td>
</tr>
`;

});

html+="</table>";

container.innerHTML=html;

}
