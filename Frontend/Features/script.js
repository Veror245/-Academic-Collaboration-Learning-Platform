const name = localStorage.getItem("user_name");
const email = localStorage.getItem("user_email");

document.getElementById("user-name").innerText = "Welcome, " + name;
document.getElementById("email").innerText = email;