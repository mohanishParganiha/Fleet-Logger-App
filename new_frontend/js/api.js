export async function apiRequest(url, method="GET", body=null){

const auth = JSON.parse(localStorage.getItem("auth") || "{}");

const options={
method,
headers:{
"Content-Type":"application/json"
}
};

if(auth.token){
options.headers["Authorization"]="Token "+auth.token;
}

if(body){
options.body=JSON.stringify(body);
}

const response = await fetch(url, options);

if(response.status===401){
localStorage.removeItem("auth");
location.reload();
}

let data=null;

try{
data=await response.json();
}catch(e){}

return {response,data};

}
