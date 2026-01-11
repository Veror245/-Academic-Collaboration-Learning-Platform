const name = localStorage.getItem("user_name");
const email = localStorage.getItem("user_email");

document.getElementById("user-name").innerText = "Welcome, " + name;
document.getElementById("email").innerText = email;


document.getElementById('logout-btn').addEventListener('click', function (e) {
  e.preventDefault(); // Stop the link from jumping immediately

  // 1. Confirm Logout (Optional, remove if you want instant logout)
  if (confirm("Are you sure you want to disconnect from UniMind?")) {

    // 2. Clear stored user data (Session/Local Storage)
    localStorage.removeItem('userToken');
    localStorage.removeItem('userName');
    sessionStorage.clear();

    // 3. Visual Feedback (Optional console log)
    console.log("System shutdown... Logging out.");

    // 4. Redirect to Login Page
    // REPLACE '/index.html' with your actual Login Page path
    window.location.href = '/Frontend/LogIn/LogIn.html';
  }
});
