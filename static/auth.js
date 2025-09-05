const API_BASE = "http://localhost:8001/api/v1/auth";

// ===== SIGNUP =====
document.getElementById("signup-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("signup-email").value;
  const password = document.getElementById("signup-password").value;
  const confirm = document.getElementById("signup-confirm").value;
  const msgDiv = document.getElementById("signup-message");

  if (password !== confirm) {
    msgDiv.textContent = "❌ Passwords do not match!";
    msgDiv.className = "error";
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, confirm_password: confirm }),
    });

    const data = await res.json();
    if (!res.ok) {
      msgDiv.textContent = "❌ " + (data.detail || "Signup failed");
      msgDiv.className = "error";
      return;
    }

    msgDiv.textContent = "✅ Signup successful!";
    msgDiv.className = "success";
  } catch (err) {
    msgDiv.textContent = "❌ Error: " + err.message;
    msgDiv.className = "error";
  }
});

// ===== LOGIN =====
document.getElementById("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;
  const msgDiv = document.getElementById("login-message");

  try {
    const res = await fetch(`${API_BASE}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await res.json();
    if (!res.ok) {
      msgDiv.textContent = "❌ " + (data.detail || "Login failed");
      msgDiv.className = "error";
      return;
    }

    // Save tokens to localStorage
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);

    msgDiv.textContent = "✅ Login successful!";
    msgDiv.className = "success";
  } catch (err) {
    msgDiv.textContent = "❌ Error: " + err.message;
    msgDiv.className = "error";
  }
});

// ===== LOGOUT =====
document.getElementById("logout-btn").addEventListener("click", async () => {
  const refreshToken = localStorage.getItem("refresh_token");
  const msgDiv = document.getElementById("logout-message");

  if (!refreshToken) {
    msgDiv.textContent = "❌ No active session found!";
    msgDiv.className = "error";
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/logout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    const data = await res.json();
    if (!res.ok) {
      msgDiv.textContent = "❌ " + (data.detail || "Logout failed");
      msgDiv.className = "error";
      return;
    }

    // Clear tokens from localStorage
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");

    msgDiv.textContent = "✅ Logout successful!";
    msgDiv.className = "success";
  } catch (err) {
    msgDiv.textContent = "❌ Error: " + err.message;
    msgDiv.className = "error";
  }
});
