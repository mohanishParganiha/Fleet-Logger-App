import {login,logout,getAuth} from "./auth.js";
import {loadPage} from "./router.js";

const loginView=document.getElementById("loginView");
const navbar=document.getElementById("navbar");
const content=document.getElementById("content");

function startApp(){

const auth=getAuth();

if(auth.token){

loginView.classList.add("hidden");
navbar.classList.remove("hidden");

loadPage("vehicles");

}else{

loginView.classList.remove("hidden");
navbar.classList.add("hidden");
content.innerHTML="";

}

}

document.getElementById("loginForm").onsubmit=async e=>{

e.preventDefault();

const form=new FormData(e.target);

const ok=await login(form.get("username"),form.get("password"));

if(ok){
startApp();
}else{
document.getElementById("loginError").textContent="Invalid login";
}

};

document.getElementById("logoutBtn").onclick=logout;

document.querySelectorAll("#navbar button[data-page]").forEach(btn=>{
btn.onclick=()=>loadPage(btn.dataset.page);
});

startApp();
