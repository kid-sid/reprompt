// chatbot.js
import { API_BASE, ENDPOINTS, STORAGE_KEYS, ROUTES } from "./config.js";

// ===== AUTH CHECK =====
let token = localStorage.getItem(STORAGE_KEYS.TOKEN);
const userEmail = localStorage.getItem(STORAGE_KEYS.USER_EMAIL);

if (!token || !userEmail) {
  alert("❌ Please login first.");
  window.location.href = ROUTES.AUTH;
}

// ===== TOKEN REFRESH FUNCTION =====
async function refreshToken() {
  const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
  
  if (!refreshToken) {
    console.error("No refresh token available");
    redirectToLogin();
    return null;
  }

  try {
    const response = await fetch(`${API_BASE}/auth${ENDPOINTS.REFRESH}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        refresh_token: refreshToken
      })
    });

    if (response.ok) {
      const data = await response.json();
      const newToken = data.access_token;
      
      // Update stored token
      localStorage.setItem(STORAGE_KEYS.TOKEN, newToken);
      token = newToken; // Update the global token variable
      
      console.log("Token refreshed successfully");
      return newToken;
    } else {
      console.error("Token refresh failed:", response.status);
      redirectToLogin();
      return null;
    }
  } catch (error) {
    console.error("Token refresh error:", error);
    redirectToLogin();
    return null;
  }
}

function redirectToLogin() {
  localStorage.clear();
  window.location.href = ROUTES.AUTH;
}

// ===== AUTHENTICATED API CALL HELPER =====
async function makeAuthenticatedRequest(url, options = {}) {
  const defaultOptions = {
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    }
  };

  const requestOptions = {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...options.headers
    }
  };

  try {
    const response = await fetch(url, requestOptions);
    
    // If token is expired, try to refresh and retry
    if (response.status === 401) {
      console.log("Token expired, attempting refresh...");
      const newToken = await refreshToken();
      
      if (newToken) {
        // Retry the request with the new token
        requestOptions.headers.Authorization = `Bearer ${newToken}`;
        return await fetch(url, requestOptions);
      } else {
        throw new Error("Token refresh failed");
      }
    }
    
    return response;
  } catch (error) {
    console.error("API request failed:", error);
    throw error;
  }
}

// ===== NEW CHAT FUNCTION =====
function handleNewChat() {
  // Clear the chat messages
  const chatMessages = document.getElementById("chatMessages");
  if (chatMessages) {
    chatMessages.innerHTML = `
      <div class="welcome-message">
        <div class="welcome-text">
          <h1>What are you working on?</h1>
        </div>
      </div>
    `;
  }
  
  // Clear the input field
  const promptInput = document.getElementById("prompt");
  if (promptInput) {
    promptInput.value = "";
  }
  
  // Re-enable send button
  const sendBtn = document.getElementById("sendBtn");
  if (sendBtn) {
    sendBtn.disabled = false;
  }
  
  // Scroll to top
  if (chatMessages) {
    chatMessages.scrollTop = 0;
  }
}

// ===== LOGOUT FUNCTION =====
async function handleLogout() {
  const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
  
  try {
    if (refreshToken) {
      await fetch(`${API_BASE}/auth${ENDPOINTS.LOGOUT}`, {
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
  // Set user email in both locations
  const userEmailElement = document.getElementById("userEmail");
  const sidebarUserEmailElement = document.getElementById("sidebarUserEmail");
  if (userEmailElement) {
    userEmailElement.textContent = `Welcome, ${userEmail}`;
  }
  if (sidebarUserEmailElement) {
    sidebarUserEmailElement.textContent = userEmail.split('@')[0]; // Show just the username part
  }

  // Attach logout buttons
  const logoutBtn = document.getElementById("logoutBtn");
  const sidebarLogoutBtn = document.getElementById("sidebarLogoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", handleLogout);
  }
  if (sidebarLogoutBtn) {
    sidebarLogoutBtn.addEventListener("click", handleLogout);
  }

  // Attach new chat button
  const newChatBtn = document.getElementById("newChatBtn");
  if (newChatBtn) {
    newChatBtn.addEventListener("click", handleNewChat);
  }

  
  // Initialize inference toggle
  initializeInferenceToggle();
  
  // Attach form listener
  attachFormListener();
  
  // Load prompt history
  loadPromptHistory();
  
  // Initialize vertical scrollbar
  initializeVerticalScrollbar();
  
  // Initialize copy button
  initializeCopyButton();
});


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
  const promptTextarea = document.getElementById("prompt");
  
  if (promptForm) {
    promptForm.addEventListener("submit", handlePromptOptimization);
  }
  
  if (promptTextarea) {
    promptTextarea.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        handlePromptOptimization(event);
      }
    });
  }
}

async function handlePromptOptimization(event) {
  event.preventDefault();

  const prompt = document.getElementById("prompt").value.trim();
  const inferenceType = document.getElementById("inferenceToggle").checked ? "pro" : "lazy";
  const chatMessages = document.getElementById("chatMessages");
  const promptInput = document.getElementById("prompt");
  const sendBtn = document.getElementById("sendBtn");

  if (!prompt) return;

  // Hide welcome message if it exists
  const welcomeMessage = document.querySelector(".welcome-message");
  if (welcomeMessage) {
    welcomeMessage.style.display = "none";
  }

  // Add user message to chat
  addUserMessage(prompt);
  
  // Clear input and disable send button
  promptInput.value = "";
  sendBtn.disabled = true;
  
  // Add loading message
  const loadingId = addLoadingMessage();

  try {
    const response = await makeAuthenticatedRequest(`${API_BASE}${ENDPOINTS.CHAT}`, {
      method: "POST",
      body: JSON.stringify({
        prompt,
        inference_type: inferenceType,
        max_tokens: 512
      })
    });

    const data = await response.json();

    if (response.ok) {
      // Remove loading message and add assistant response
      removeLoadingMessage(loadingId);
      addAssistantMessage(
        data.output || "No optimization available.",
        data.inference_type || inferenceType,
        data.model_used || (inferenceType === "pro" ? "GPT-4" : "GPT-3.5"),
        data.tokens_used || "N/A"
      );
      
      // Reload prompt history to show the new entry
      loadPromptHistory();
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
    
    // Remove loading message and add error message
    removeLoadingMessage(loadingId);
    addAssistantMessage(`Error: ${error.message}`, inferenceType, "Error", "N/A", true);
  } finally {
    // Re-enable send button
    sendBtn.disabled = false;
  }
}

// ===== Chat Message Functions =====
function addUserMessage(text) {
  const chatMessages = document.getElementById("chatMessages");
  const messageDiv = document.createElement("div");
  messageDiv.className = "message user-message";
  messageDiv.innerHTML = `
    <div class="message-avatar">👤</div>
    <div class="message-content">
      <p>${text}</p>
    </div>
  `;
  chatMessages.appendChild(messageDiv);
  scrollToBottom();
}

function addAssistantMessage(text, mode, model, tokens, isError = false) {
  const chatMessages = document.getElementById("chatMessages");
  const messageDiv = document.createElement("div");
  messageDiv.className = "message assistant-message";
  
  const copyButton = isError ? '' : `
    <button class="copy-btn" onclick="copyMessageText(this)" title="Copy to clipboard">
      <span class="copy-icon">📋</span>
      <span class="copy-text">Copy</span>
    </button>
  `;
  
  messageDiv.innerHTML = `
    <div class="message-avatar">🤖</div>
    <div class="message-content">
      <div class="message-header">
        <h3>Optimized Prompt:</h3>
        ${copyButton}
      </div>
      <p>${text}</p>
      <div class="message-meta">
        <strong>Mode:</strong> ${mode} | 
        <strong>Model:</strong> ${model} | 
        <strong>Tokens:</strong> ${tokens}
      </div>
    </div>
  `;
  chatMessages.appendChild(messageDiv);
  scrollToBottom();
}

function addLoadingMessage() {
  const chatMessages = document.getElementById("chatMessages");
  const loadingDiv = document.createElement("div");
  const loadingId = `loading-${Date.now()}`;
  loadingDiv.id = loadingId;
  loadingDiv.className = "loading-message";
  loadingDiv.innerHTML = `
    <div class="loading-avatar">🤖</div>
    <div class="loading-content">
      <div class="loading-spinner"></div>
      <span class="loading-text">Optimizing your prompt...</span>
    </div>
  `;
  chatMessages.appendChild(loadingDiv);
  scrollToBottom();
  return loadingId;
}

function removeLoadingMessage(loadingId) {
  const loadingElement = document.getElementById(loadingId);
  if (loadingElement) {
    loadingElement.remove();
  }
}

function scrollToBottom() {
  const chatMessages = document.getElementById("chatMessages");
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function copyMessageText(button) {
  const messageContent = button.closest('.message-content');
  const textElement = messageContent.querySelector('p');
  const textToCopy = textElement.textContent.trim();
  
  navigator.clipboard.writeText(textToCopy).then(() => {
    const copyText = button.querySelector(".copy-text");
    const originalText = copyText.textContent;
    
    button.classList.add("copied");
    copyText.textContent = "Copied!";
    
    setTimeout(() => {
      button.classList.remove("copied");
      copyText.textContent = originalText;
    }, 2000);
  }).catch(err => {
    console.error("Copy failed:", err);
  });
}

// Make copyMessageText globally available
window.copyMessageText = copyMessageText;

// ===== Token Validation =====
async function validateToken() {
  try {
    const response = await makeAuthenticatedRequest(`${API_BASE}/auth${ENDPOINTS.VALIDATE}`, {
      method: "GET"
    });
    
    if (!response.ok) {
      console.error("Token validation failed:", response.status);
      redirectToLogin();
    }
  } catch (error) {
    console.error("Token validation error:", error);
    redirectToLogin();
  }
}

// ===== Prompt History Functions =====
async function loadPromptHistory() {
  try {
    const response = await makeAuthenticatedRequest(`${API_BASE}/prompt-history?page=1&page_size=20`, {
      method: "GET"
    });

    if (response.ok) {
      const data = await response.json();
      displayPromptHistory(data.items);
    } else {
      console.error("Failed to load prompt history:", response.status);
    }
  } catch (error) {
    console.error("Error loading prompt history:", error);
  }
}

function displayPromptHistory(historyItems) {
  const historyContainer = document.getElementById("sidebarPromptHistory");
  if (!historyContainer) return;

  if (historyItems.length === 0) {
    historyContainer.innerHTML = "<p style='color: #8e8ea0; font-size: 12px;'>No prompt history yet. Start optimizing prompts to see your history here!</p>";
    return;
  }

  const historyHTML = historyItems.map(item => `
    <div class="sidebar-history-item" onclick="loadHistoryItem('${item.id}')">
      <div class="sidebar-history-header">
        <span class="sidebar-history-mode ${item.inference_type}">${item.inference_type.toUpperCase()}</span>
        <span class="sidebar-history-date">${new Date(item.created_at).toLocaleDateString()}</span>
        <button class="sidebar-delete-history-btn" onclick="event.stopPropagation(); deletePromptHistory('${item.id}')">×</button>
      </div>
      <div class="sidebar-history-content">
        <div class="sidebar-history-preview">
          <strong>Original:</strong> ${item.original_prompt.substring(0, 60)}${item.original_prompt.length > 60 ? '...' : ''}
        </div>
        <div class="sidebar-history-preview">
          <strong>Optimized:</strong> ${item.optimized_prompt.substring(0, 60)}${item.optimized_prompt.length > 60 ? '...' : ''}
        </div>
      </div>
    </div>
  `).join('');

  historyContainer.innerHTML = historyHTML;
}

function loadHistoryItem(historyId) {
  // This function can be used to load a specific history item into the main area
  // For now, we'll just show an alert with the ID
  console.log("Loading history item:", historyId);
  // You can implement this to show the full prompt in the main area
}

async function deletePromptHistory(historyId) {
  if (!confirm("Are you sure you want to delete this prompt history entry?")) {
    return;
  }

  try {
    const response = await makeAuthenticatedRequest(`${API_BASE}/prompt-history/${historyId}`, {
      method: "DELETE"
    });

    if (response.ok) {
      loadPromptHistory(); // Reload history
    } else {
      alert("Failed to delete prompt history entry");
    }
  } catch (error) {
    console.error("Error deleting prompt history:", error);
    alert("Error deleting prompt history entry");
  }
}

// ===== Copy Button Functionality =====
function initializeCopyButton() {
  const copyBtn = document.getElementById("copyBtn");
  if (!copyBtn) return;

  copyBtn.addEventListener("click", async function() {
    const optimizedText = document.getElementById("optimizedText");
    if (!optimizedText || !optimizedText.textContent.trim()) {
      return;
    }

    const textToCopy = optimizedText.textContent.trim();
    
    try {
      // Use the modern Clipboard API
      await navigator.clipboard.writeText(textToCopy);
      
      // Show success feedback
      showCopySuccess(copyBtn);
    } catch (err) {
      // Fallback for older browsers
      try {
        const textArea = document.createElement("textarea");
        textArea.value = textToCopy;
        textArea.style.position = "fixed";
        textArea.style.left = "-999999px";
        textArea.style.top = "-999999px";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        const successful = document.execCommand('copy');
        document.body.removeChild(textArea);
        
        if (successful) {
          showCopySuccess(copyBtn);
        } else {
          showCopyError(copyBtn);
        }
      } catch (fallbackErr) {
        console.error("Copy failed:", fallbackErr);
        showCopyError(copyBtn);
      }
    }
  });
}

function showCopySuccess(copyBtn) {
  const copyText = copyBtn.querySelector(".copy-text");
  const originalText = copyText.textContent;
  
  // Update button appearance
  copyBtn.classList.add("copied");
  copyText.textContent = "Copied!";
  
  // Reset after 2 seconds
  setTimeout(() => {
    copyBtn.classList.remove("copied");
    copyText.textContent = originalText;
  }, 2000);
}

function showCopyError(copyBtn) {
  const copyText = copyBtn.querySelector(".copy-text");
  const originalText = copyText.textContent;
  
  // Show error state
  copyText.textContent = "Failed";
  copyBtn.style.background = "#ef4444";
  copyBtn.style.borderColor = "#dc2626";
  
  // Reset after 2 seconds
  setTimeout(() => {
    copyText.textContent = originalText;
    copyBtn.style.background = "";
    copyBtn.style.borderColor = "";
  }, 2000);
}

// Validate token on page load
validateToken();

// ===== Vertical Scrollbar =====
function initializeVerticalScrollbar() {
  const scrollbarThumb = document.querySelector('.scrollbar-thumb');
  const scrollbarTrack = document.querySelector('.scrollbar-track');
  const mainContent = document.querySelector('.main-content');
  
  if (!scrollbarThumb || !scrollbarTrack || !mainContent) return;
  
  let isDragging = false;
  let startY = 0;
  let startScrollTop = 0;
  
  // Update scrollbar position based on content scroll
  function updateScrollbar() {
    const scrollTop = mainContent.scrollTop;
    const scrollHeight = mainContent.scrollHeight;
    const clientHeight = mainContent.clientHeight;
    
    if (scrollHeight <= clientHeight) {
      scrollbarThumb.style.display = 'none';
      return;
    }
    
    scrollbarThumb.style.display = 'block';
    
    const thumbHeight = (clientHeight / scrollHeight) * 100;
    const thumbTop = (scrollTop / (scrollHeight - clientHeight)) * (100 - thumbHeight);
    
    scrollbarThumb.style.height = `${thumbHeight}%`;
    scrollbarThumb.style.top = `${thumbTop}%`;
  }
  
  // Handle mouse down on scrollbar thumb
  scrollbarThumb.addEventListener('mousedown', (e) => {
    isDragging = true;
    startY = e.clientY;
    startScrollTop = mainContent.scrollTop;
    e.preventDefault();
  });
  
  // Handle mouse move
  document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    
    const deltaY = e.clientY - startY;
    const scrollbarHeight = scrollbarTrack.offsetHeight;
    const thumbHeight = scrollbarThumb.offsetHeight;
    const maxScroll = scrollbarHeight - thumbHeight;
    
    const scrollRatio = deltaY / maxScroll;
    const maxScrollTop = mainContent.scrollHeight - mainContent.clientHeight;
    
    mainContent.scrollTop = startScrollTop + (scrollRatio * maxScrollTop);
  });
  
  // Handle mouse up
  document.addEventListener('mouseup', () => {
    isDragging = false;
  });
  
  // Update scrollbar on content scroll
  mainContent.addEventListener('scroll', updateScrollbar);
  
  // Initial update
  updateScrollbar();
}

// Make functions globally available for onclick handlers
window.loadHistoryItem = loadHistoryItem;
window.deletePromptHistory = deletePromptHistory;
