import {apiRequest} from "./api.js";

export async function login(email,password){

const {data,response}=await apiRequest("/api/login/","POST",{
email,
password
});

if(response.ok){

localStorage.setItem("auth",JSON.stringify(data));
return true;

}

return false;

}

export function logout(){

localStorage.removeItem("auth");
location.reload();

}

export function getAuth(){

return JSON.parse(localStorage.getItem("auth")||"{}");

}

export function isAdmin(){

const auth=getAuth();
return auth.is_staff===true;

}
