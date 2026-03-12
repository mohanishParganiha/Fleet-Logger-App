import {apiRequest} from "../js/api.js";

export function renderBulk(container){

container.innerHTML=`

<h3>Bulk Calculate</h3>

<form id="bulkForm">

<label>Start Date</label> <input name="start_date" type="date">

<label>End Date</label> <input name="end_date" type="date">

<label>Calc Type</label> <select name="calc_type">

<option value="weight">Weight</option>
<option value="distance">Distance</option>
</select>

<label>Rate</label> <input name="rate" type="number" step="0.01">

<button>Calculate</button>

</form>

<div id="result"></div>
`;

document.getElementById("bulkForm").onsubmit=async e=>{

e.preventDefault();

const form=new FormData(e.target);

const params=new URLSearchParams(form);

const {data}=await apiRequest(
"/api/trip-logs/calculate-bulk?"+params.toString()
);

document.getElementById("result").innerHTML=
`<p>Total Trips: ${data.total_trips}</p>

<p>Total Amount: ${data.total_amount}</p>`;

};

}
