const form = document.querySelector("form");
const emailInput = document.querySelector('input[type="email"]');
const passwordInput = document.querySelector('input[type="password"]');

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const formData = new URLSearchParams();
  formData.append("username", emailInput.value); // email → username
  formData.append("password", passwordInput.value);

  try {
    const response = await fetch("http://127.0.0.1:8000/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body: formData.toString()
    });

    const data = await response.json();

    if (response.ok) {

      localStorage.setItem("token", data.access_token);

      // Store user info
      localStorage.setItem("user_name", data.user.full_name);
      localStorage.setItem("user_email", data.user.email);
      localStorage.setItem("user_role", data.user.role);
      localStorage.setItem("user_id", data.user.id);

      console.log("Stored User:", data.user);

      alert("Login successful ✅");
      window.location.href = "/Frontend/Features/FeaturesPage.html";
    } else {
      alert(data.detail || "Invalid login credentials ❌");
    }

  } catch (error) {
    alert("Backend server not running ❌");
  }
});





