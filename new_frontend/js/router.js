import {renderVehicles} from "../pages/vehicles.js";
import {renderDrivers} from "../pages/drivers.js";
import {renderTrips} from "../pages/trips.js";
import {renderBulk} from "../pages/bulk.js";

export function loadPage(page){

const content=document.getElementById("content");

if(page==="vehicles") renderVehicles(content);
if(page==="drivers") renderDrivers(content);
if(page==="trips") renderTrips(content);
if(page==="bulk") renderBulk(content);

}
