// auth.js
import { API_BASE, ENDPOINTS, STORAGE_KEYS, ROUTES } from "./config.js";

// ===== SIGNUP =====
async function handleSignup(event) {
  event.preventDefault();

  const email = document.getElementById("signupEmail").value.trim();
  const password = document.getElementById("signupPassword").value;
  const confirmPassword = document.getElementById("signupConfirmPassword").value;
  const messageDiv = document.getElementById("signupMessage");

  if (password !== confirmPassword) {
    showMessage(messageDiv, "❌ Passwords do not match!", "error");
    return;
  }

  try {
    const response = await fetch(`${API_BASE}${ENDPOINTS.REGISTER}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, confirm_password: confirmPassword }),
    });

    const data = await response.json();

    if (response.ok) {
      showMessage(messageDiv, "✅ Signup successful! Please login now.", "success");
      setTimeout(() => {
        showLoginForm();
        clearMessage(messageDiv);
      }, 1500);
    } else {
      showMessage(messageDiv, "❌ " + (data.detail || "Signup failed."), "error");
    }
  } catch (error) {
    console.error("Signup error:", error);
    showMessage(messageDiv, "❌ Something went wrong during signup.", "error");
  }
}

// ===== LOGIN =====
async function handleLogin(event) {
  event.preventDefault();

  const email = document.getElementById("loginEmail").value.trim();
  const password = document.getElementById("loginPassword").value;
  const messageDiv = document.getElementById("loginMessage");

  try {
    const response = await fetch(`${API_BASE}${ENDPOINTS.LOGIN}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();
    console.log("Login response:", data);

    if (response.ok) {
      // Save tokens in localStorage
      localStorage.setItem(STORAGE_KEYS.TOKEN, data.access_token);
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, data.refresh_token);
      localStorage.setItem(STORAGE_KEYS.USER_EMAIL, email);

      showMessage(messageDiv, "✅ Login successful! Redirecting...", "success");
      
      // Redirect to chatbot page after a short delay
      setTimeout(() => {
        window.location.href = ROUTES.CHATBOT;
      }, 1000);
    } else {
      showMessage(messageDiv, "❌ " + (data.detail || "Login failed."), "error");
    }
  } catch (error) {
    console.error("Login error:", error);
    showMessage(messageDiv, "❌ Something went wrong during login.", "error");
  }
}

// ===== LOGOUT =====
async function handleLogout() {
  const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
  
  try {
    if (refreshToken) {
      await fetch(`${API_BASE}${ENDPOINTS.LOGOUT}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    }
  } catch (error) {
    console.error("Logout error:", error);
  } finally {
    // Clear all stored data
    localStorage.removeItem(STORAGE_KEYS.TOKEN);
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.USER_EMAIL);
    
    // Redirect to auth page
    window.location.href = ROUTES.AUTH;
  }
}

// ===== Toggle between forms =====
function showSignupForm() {
  document.getElementById("loginForm").classList.add("hidden");
  document.getElementById("signupForm").classList.remove("hidden");
  clearMessage(document.getElementById("loginMessage"));
}

function showLoginForm() {
  document.getElementById("signupForm").classList.add("hidden");
  document.getElementById("loginForm").classList.remove("hidden");
  clearMessage(document.getElementById("signupMessage"));
}

// Make functions globally available for onclick handlers
window.showSignupForm = showSignupForm;
window.showLoginForm = showLoginForm;

// ===== Message handling =====
function showMessage(element, message, type) {
  element.textContent = message;
  element.className = type;
}

function clearMessage(element) {
  element.textContent = "";
  element.className = "";
}

// ===== Attach listeners =====
document.addEventListener("DOMContentLoaded", () => {
  // Check if already logged in
  const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
  if (token && window.location.pathname === "/auth") {
    window.location.href = ROUTES.CHATBOT;
    return;
  }

  // Attach form listeners
  const signupForm = document.getElementById("signupForm");
  const loginForm = document.getElementById("loginForm");
  
  if (signupForm) {
    signupForm.addEventListener("submit", handleSignup);
  }
  
  if (loginForm) {
    loginForm.addEventListener("submit", handleLogin);
  }
});