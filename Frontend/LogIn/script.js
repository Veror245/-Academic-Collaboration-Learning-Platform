
const form = document.querySelector("form");
const emailInput = document.querySelector('input[type="email"]');
const passwordInput = document.querySelector('input[type="password"]');

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    username: emailInput.value,   // email mapped to username
    password: passwordInput.value
  };

  try {
    const response = await fetch("http://127.0.0.1:8000/Authentication/login_auth_login_post", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (response.ok) {
      // Save JWT token
      localStorage.setItem("token", data.access_token);

      alert("Login successful ✅");

      // Redirect (optional)
      // window.location.href = "/Frontend/Dashboard/index.html";
    } else {
      alert(data.detail || "Invalid login credentials ❌");
    }

  } catch (error) {
    alert("Backend server not running ❌");
  }
});

