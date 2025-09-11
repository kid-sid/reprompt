// chatbot.js
import { API_BASE, ENDPOINTS, STORAGE_KEYS, ROUTES } from "./config.js";

// ===== AUTH CHECK =====
const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
const userEmail = localStorage.getItem(STORAGE_KEYS.USER_EMAIL);

if (!token || !userEmail) {
  alert("❌ Please login first.");
  window.location.href = ROUTES.AUTH;
}

// ===== LOGOUT FUNCTION =====
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
    console.log("Redirecting to:", ROUTES.AUTH); // Debug log
    window.location.href = ROUTES.AUTH;
  }
}

// ===== Initialize UI =====
document.addEventListener("DOMContentLoaded", () => {
  // Set user email
  const userEmailElement = document.getElementById("userEmail");
  if (userEmailElement) {
    userEmailElement.textContent = `Welcome, ${userEmail}`;
  }

  // Attach logout button
  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", handleLogout);
  }

  // Initialize theme toggle
  initializeThemeToggle();
  
  // Initialize inference toggle
  initializeInferenceToggle();
  
  // Attach form listener
  attachFormListener();
});

// ===== Theme Toggle =====
function initializeThemeToggle() {
  const themeToggle = document.getElementById("themeToggle");
  const html = document.documentElement;
  const savedTheme = localStorage.getItem("theme") || "light";
  
  html.setAttribute("data-theme", savedTheme);
  themeToggle.checked = savedTheme === "dark";
  
  themeToggle.addEventListener("change", function () {
    const theme = this.checked ? "dark" : "light";
    html.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  });
}

// ===== Inference Toggle =====
function initializeInferenceToggle() {
  const inferenceToggle = document.getElementById("inferenceToggle");
  const inferenceInfo = document.getElementById("inferenceInfo");
  const savedInference = localStorage.getItem("inferenceType") || "lazy";
  
  inferenceToggle.checked = savedInference === "pro";
  updateInferenceInfo(savedInference);
  
  inferenceToggle.addEventListener("change", function () {
    const type = this.checked ? "pro" : "lazy";
    updateInferenceInfo(type);
    localStorage.setItem("inferenceType", type);
  });
}

function updateInferenceInfo(type) {
  const inferenceInfo = document.getElementById("inferenceInfo");
  
  if (type === "pro") {
    inferenceInfo.innerHTML = `
      <h4>⚡ Pro Mode <span class="model-badge pro">GPT-4</span></h4>
      <p>Advanced prompt optimization with sophisticated techniques like chain-of-thought reasoning and role-based prompting.</p>
    `;
    inferenceInfo.className = "inference-info pro";
  } else {
    inferenceInfo.innerHTML = `
      <h4>🐌 Lazy Mode <span class="model-badge lazy">GPT-3.5</span></h4>
      <p>Simple and efficient prompt optimization with basic clarity and specificity improvements.</p>
    `;
    inferenceInfo.className = "inference-info";
  }
}

// ===== Form Handling =====
function attachFormListener() {
  const promptForm = document.getElementById("promptForm");
  if (promptForm) {
    promptForm.addEventListener("submit", handlePromptOptimization);
  }
}

async function handlePromptOptimization(event) {
  event.preventDefault();

  const prompt = document.getElementById("prompt").value.trim();
  const inferenceType = document.getElementById("inferenceToggle").checked ? "pro" : "lazy";
  const submitBtn = document.getElementById("submitBtn");
  const resultDiv = document.getElementById("result");
  const optimizedText = document.getElementById("optimizedText");
  const resultMeta = document.getElementById("resultMeta");

  if (!prompt) return;

  // Update UI
  submitBtn.disabled = true;
  submitBtn.textContent = `Optimizing with ${inferenceType} mode...`;
  resultDiv.classList.add("hidden");

  try {
    const response = await fetch(`http://localhost:8001/api/v1${ENDPOINTS.CHAT}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({
        prompt,
        inference_type: inferenceType,
        max_tokens: 512
      })
    });

    const data = await response.json();

    if (response.ok) {
      optimizedText.textContent = data.output || "No optimization available.";
      resultMeta.innerHTML = `
        <strong>Mode:</strong> ${data.inference_type || inferenceType} | 
        <strong>Model:</strong> ${data.model_used || (inferenceType === "pro" ? "GPT-4" : "GPT-3.5")} | 
        <strong>Tokens:</strong> ${data.tokens_used || "N/A"}
      `;
      resultDiv.classList.remove("hidden", "error");
    } else {
      if (response.status === 401) {
        localStorage.clear();
        window.location.href = ROUTES.AUTH;
        return;
      }
      throw new Error(data.detail || `HTTP ${response.status}`);
    }
  } catch (error) {
    console.error("Optimization error:", error);
    optimizedText.textContent = `Error: ${error.message}`;
    resultDiv.classList.remove("hidden");
    resultDiv.classList.add("error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Optimize Prompt";
  }
}

// ===== Token Validation =====
async function validateToken() {
  try {
    const response = await fetch(`${API_BASE}${ENDPOINTS.VALIDATE}`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` }
    });
    
    if (!response.ok) {
      localStorage.clear();
      window.location.href = ROUTES.AUTH;
    }
  } catch (error) {
    console.error("Token validation error:", error);
    localStorage.clear();
    window.location.href = ROUTES.AUTH;
  }
}

// Validate token on page load
validateToken();
