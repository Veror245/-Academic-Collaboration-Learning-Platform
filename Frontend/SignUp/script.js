
const form = document.querySelector("form");

const nameInput = document.querySelector('input[placeholder="Name"]');
const emailInput = document.querySelector('input[type="email"]');
const passwordInput = document.querySelector('input[type="password"]');

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    email: emailInput.value, // email used as username
    password: passwordInput.value,
    full_name: nameInput.value,
    role: "student",
  };

  try {
    const response = await fetch("http://127.0.0.1:8000/auth/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (response.ok) {
      alert("Account created successfully ✅");

      // Redirect to login
      window.location.href = "/Frontend/LogIn/LogIn.html";
    } else {
      alert(data.detail || "Registration failed ❌");
    }

  } catch (error) {
    alert("Backend server not running ❌");
  }
});

