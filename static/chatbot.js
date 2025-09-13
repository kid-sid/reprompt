// chatbot.js - Modern Chatbot Interface
import { API_BASE, ENDPOINTS, STORAGE_KEYS, ROUTES } from "./config.js";

// ===== GLOBAL STATE =====
let token = localStorage.getItem(STORAGE_KEYS.TOKEN);
let userEmail = localStorage.getItem(STORAGE_KEYS.USER_EMAIL);
let currentInferenceMode = localStorage.getItem("inferenceMode") || "lazy";
let isLoading = false;
let chatHistory = [];
let currentChatId = null;
let refreshTimer = null;
let sessionWarningTimer = null;

// ===== AUTHENTICATION CHECK =====
if (!token || !userEmail) {
  console.log("No authentication found, redirecting to login...");
  window.location.href = ROUTES.AUTH;
  throw new Error("Not authenticated");
}

// ===== UTILITY FUNCTIONS =====
function showToast(message, type = "info", duration = 3000) {
  // Create toast element
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  toast.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: ${type === "error" ? "#ef4444" : type === "success" ? "#10b981" : "#3b82f6"};
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 10000;
    animation: slideIn 0.3s ease;
  `;
  
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.style.animation = "slideOut 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ===== JWT TOKEN UTILITIES =====
function parseJWT(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Error parsing JWT:', error);
    return null;
  }
}

function getTokenExpiration(token) {
  const payload = parseJWT(token);
  if (!payload || !payload.exp) {
    return null;
  }
  return payload.exp * 1000; // Convert to milliseconds
}

function getTokenTimeUntilExpiry(token) {
  const expiration = getTokenExpiration(token);
  if (!expiration) {
    return null;
  }
  return expiration - Date.now();
}

function isTokenExpired(token) {
  const timeUntilExpiry = getTokenTimeUntilExpiry(token);
  return timeUntilExpiry === null || timeUntilExpiry <= 0;
}

function isTokenExpiringSoon(token, thresholdMinutes = 5) {
  const timeUntilExpiry = getTokenTimeUntilExpiry(token);
  if (timeUntilExpiry === null) {
    return false;
  }
  const thresholdMs = thresholdMinutes * 60 * 1000;
  return timeUntilExpiry <= thresholdMs && timeUntilExpiry > 0;
}

function getInitials(email) {
  return email.split('@')[0].substring(0, 2).toUpperCase();
}

function formatTimestamp(timestamp) {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

// ===== TOKEN MANAGEMENT =====
async function refreshToken(isProactive = false) {
  const refreshTokenValue = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
  
  if (!refreshTokenValue) {
    console.error("No refresh token available");
    if (!isProactive) {
    redirectToLogin();
    }
    return null;
  }

  try {
    console.log(`Token refresh ${isProactive ? '(proactive)' : '(reactive)'} initiated`);
    
    const response = await fetch(`${API_BASE}/auth${ENDPOINTS.REFRESH}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshTokenValue })
    });

    if (response.ok) {
      const data = await response.json();
      const newToken = data.access_token;
      
      localStorage.setItem(STORAGE_KEYS.TOKEN, newToken);
      token = newToken;
      
      console.log("Token refreshed successfully");
      
      // Restart proactive refresh timer with new token
      if (isProactive) {
        startProactiveTokenRefresh();
        showToast("Session refreshed automatically", "success", 2000);
      }
      
      return newToken;
    } else {
      console.error("Token refresh failed:", response.status);
      if (!isProactive) {
      redirectToLogin();
      }
      return null;
    }
  } catch (error) {
    console.error("Token refresh error:", error);
    if (!isProactive) {
    redirectToLogin();
    }
    return null;
  }
}

// ===== PROACTIVE TOKEN REFRESH =====
function startProactiveTokenRefresh() {
  // Clear existing timers
  if (refreshTimer) {
    clearTimeout(refreshTimer);
  }
  if (sessionWarningTimer) {
    clearTimeout(sessionWarningTimer);
  }
  
  if (!token) {
    console.log("No token available for proactive refresh");
    return;
  }
  
  const timeUntilExpiry = getTokenTimeUntilExpiry(token);
  if (!timeUntilExpiry || timeUntilExpiry <= 0) {
    console.log("Token already expired, skipping proactive refresh");
    return;
  }
  
  // Set refresh timer to refresh 5 minutes before expiry
  const refreshThreshold = 5 * 60 * 1000; // 5 minutes in milliseconds
  const refreshTime = Math.max(timeUntilExpiry - refreshThreshold, 30000); // At least 30 seconds
  
  console.log(`Token expires in ${Math.round(timeUntilExpiry / 60000)} minutes. Will refresh in ${Math.round(refreshTime / 60000)} minutes.`);
  
  refreshTimer = setTimeout(async () => {
    console.log("Proactive token refresh triggered");
    await refreshToken(true);
  }, refreshTime);
  
  // Set warning timer to show notification 2 minutes before expiry
  const warningThreshold = 2 * 60 * 1000; // 2 minutes in milliseconds
  const warningTime = Math.max(timeUntilExpiry - warningThreshold, 10000); // At least 10 seconds
  
  if (warningTime < refreshTime) {
    sessionWarningTimer = setTimeout(() => {
      showSessionExpirationWarning();
    }, warningTime);
  }
}

function showSessionExpirationWarning() {
  const timeUntilExpiry = getTokenTimeUntilExpiry(token);
  if (!timeUntilExpiry || timeUntilExpiry <= 0) {
    return;
  }
  
  const minutesLeft = Math.round(timeUntilExpiry / 60000);
  showToast(
    `Your session will expire in ${minutesLeft} minute${minutesLeft !== 1 ? 's' : ''}. Refreshing automatically...`,
    "warning",
    5000
  );
}

function stopProactiveTokenRefresh() {
  if (refreshTimer) {
    clearTimeout(refreshTimer);
    refreshTimer = null;
  }
  if (sessionWarningTimer) {
    clearTimeout(sessionWarningTimer);
    sessionWarningTimer = null;
  }
}

// ===== PAGE VISIBILITY HANDLING =====
function handlePageVisibilityChange() {
  if (document.hidden) {
    console.log("Page hidden, pausing proactive refresh");
    // Don't stop timers completely, just log for debugging
  } else {
    console.log("Page visible, checking token status");
    // Check if token needs refresh when page becomes visible
    if (token && isTokenExpiringSoon(token, 10)) { // 10 minutes threshold
      console.log("Token expiring soon, refreshing proactively");
      refreshToken(true);
    }
  }
}

// Add page visibility change listener
document.addEventListener('visibilitychange', handlePageVisibilityChange);

function redirectToLogin() {
  localStorage.clear();
  window.location.href = ROUTES.AUTH;
}

// ===== API COMMUNICATION =====
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
    
    if (response.status === 401) {
      console.log("Token expired, attempting refresh...");
      const newToken = await refreshToken();
      
      if (newToken) {
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

// ===== UI INITIALIZATION =====
document.addEventListener("DOMContentLoaded", async () => {
  try {
    console.log("Initializing chatbot...");
    
    // Validate authentication
    await validateToken();
    
    // Start proactive token refresh
    startProactiveTokenRefresh();
    
    // Initialize UI components
    initializeUserProfile();
    initializeInferenceToggle();
    initializeEventListeners();
    initializeInputHandling();
    initializeScrollHandling();
    
    // Load initial data
    await loadChatHistory();
    
    console.log("Chatbot initialized successfully");
  } catch (error) {
    console.error("Failed to initialize chatbot:", error);
    showToast("Failed to initialize chatbot", "error");
    redirectToLogin();
  }
});

// ===== USER PROFILE =====
function initializeUserProfile() {
  const userAvatar = document.getElementById("userAvatar");
  const userName = document.getElementById("userName");
  const userEmailElement = document.getElementById("userEmail");
  
  if (userAvatar) {
    const initials = getInitials(userEmail);
    userAvatar.querySelector("#userInitials").textContent = initials;
  }
  
  if (userName) {
    userName.textContent = userEmail.split('@')[0];
  }
  
  if (userEmailElement) {
    userEmailElement.textContent = userEmail;
  }
  
  // Add session status indicator
  updateSessionStatus();
}

function updateSessionStatus() {
  if (!token) return;
  
  const timeUntilExpiry = getTokenTimeUntilExpiry(token);
  if (!timeUntilExpiry || timeUntilExpiry <= 0) return;
  
  const minutesLeft = Math.round(timeUntilExpiry / 60000);
  const hoursLeft = Math.round(timeUntilExpiry / 3600000);
  
  // Create or update session status element
  let sessionStatus = document.getElementById("sessionStatus");
  if (!sessionStatus) {
    sessionStatus = document.createElement("div");
    sessionStatus.id = "sessionStatus";
    sessionStatus.style.cssText = `
      position: fixed;
      top: 10px;
      left: 10px;
      background: rgba(0, 0, 0, 0.8);
      color: white;
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 12px;
      z-index: 1000;
      display: none;
    `;
    document.body.appendChild(sessionStatus);
  }
  
  // Show status if session expires within 30 minutes
  if (timeUntilExpiry <= 30 * 60 * 1000) {
    const timeText = hoursLeft > 0 ? `${hoursLeft}h ${minutesLeft % 60}m` : `${minutesLeft}m`;
    sessionStatus.textContent = `Session expires in ${timeText}`;
    sessionStatus.style.display = 'block';
    
    // Change color based on urgency
    if (timeUntilExpiry <= 5 * 60 * 1000) {
      sessionStatus.style.background = 'rgba(239, 68, 68, 0.9)'; // Red
    } else if (timeUntilExpiry <= 15 * 60 * 1000) {
      sessionStatus.style.background = 'rgba(245, 158, 11, 0.9)'; // Orange
    } else {
      sessionStatus.style.background = 'rgba(59, 130, 246, 0.9)'; // Blue
    }
  } else {
    sessionStatus.style.display = 'none';
  }
  
  // Update every minute
  setTimeout(updateSessionStatus, 60000);
}

// ===== INFERENCE MODE TOGGLE =====
function initializeInferenceToggle() {
  const toggle = document.getElementById("inferenceToggle");
  const modeLabel = document.getElementById("modeLabel");
  const modeDescription = document.getElementById("modeDescription");
  
  if (!toggle) return;
  
  // Set initial state
  toggle.classList.toggle("active", currentInferenceMode === "pro");
  updateModeDisplay();
  
  toggle.addEventListener("click", () => {
    currentInferenceMode = currentInferenceMode === "lazy" ? "pro" : "lazy";
    localStorage.setItem("inferenceMode", currentInferenceMode);
    
    toggle.classList.toggle("active", currentInferenceMode === "pro");
    updateModeDisplay();
    
    showToast(`Switched to ${currentInferenceMode} mode`, "success", 2000);
  });
  
  function updateModeDisplay() {
    if (modeLabel) {
      modeLabel.textContent = currentInferenceMode.charAt(0).toUpperCase() + currentInferenceMode.slice(1);
    }
    if (modeDescription) {
      modeDescription.textContent = currentInferenceMode === "pro" ? "(GPT-4)" : "(GPT-3.5)";
    }
  }
}

// ===== EVENT LISTENERS =====
function initializeEventListeners() {
  // New chat button
  const newChatBtn = document.getElementById("newChatBtn");
  if (newChatBtn) {
    newChatBtn.addEventListener("click", handleNewChat);
  }

  // Logout button
  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", handleLogout);
  }
  
  // Settings button
  const settingsBtn = document.getElementById("settingsBtn");
  if (settingsBtn) {
    settingsBtn.addEventListener("click", handleSettings);
  }
  
  // Scroll to bottom button
  const scrollToBottomBtn = document.getElementById("scrollToBottom");
  if (scrollToBottomBtn) {
    scrollToBottomBtn.addEventListener("click", scrollToBottom);
  }
}

// ===== INPUT HANDLING =====
function initializeInputHandling() {
  const form = document.getElementById("promptForm");
  const input = document.getElementById("promptInput");
  
  if (form) {
    form.addEventListener("submit", handleSubmit);
  }
  
  if (input) {
    // Auto-resize textarea
    input.addEventListener("input", autoResizeTextarea);
    
    // Keyboard shortcuts
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit(e);
      }
    });
    
    // Focus on load
    input.focus();
  }
}

function autoResizeTextarea() {
  const textarea = document.getElementById("promptInput");
  if (!textarea) return;
  
  textarea.style.height = "auto";
  textarea.style.height = Math.min(textarea.scrollHeight, 120) + "px";
}

// ===== SCROLL HANDLING =====
function initializeScrollHandling() {
  const chatMessages = document.getElementById("chatMessages");
  const scrollToBottomBtn = document.getElementById("scrollToBottom");
  
  if (chatMessages && scrollToBottomBtn) {
    chatMessages.addEventListener("scroll", () => {
      const isAtBottom = chatMessages.scrollTop + chatMessages.clientHeight >= chatMessages.scrollHeight - 10;
      scrollToBottomBtn.classList.toggle("visible", !isAtBottom);
    });
  }
}

function scrollToBottom() {
  const chatMessages = document.getElementById("chatMessages");
  if (chatMessages) {
    chatMessages.scrollTo({
      top: chatMessages.scrollHeight,
      behavior: "smooth"
    });
  }
}

// ===== CHAT FUNCTIONS =====
async function handleSubmit(event) {
  event.preventDefault();

  if (isLoading) return;
  
  const input = document.getElementById("promptInput");
  const prompt = input.value.trim();
  
  if (!prompt) {
    showToast("Please enter a message", "error");
    return;
  }
  
  console.log("Submitting prompt:", prompt, "Mode:", currentInferenceMode);
  
  // Clear input and disable send button
  input.value = "";
  autoResizeTextarea();
  setLoadingState(true);
  
  // Hide welcome message
  hideWelcomeMessage();
  
  // Add user message
  addUserMessage(prompt);
  
  // Add loading message
  const loadingId = addLoadingMessage();

  try {
    const response = await makeAuthenticatedRequest(`${API_BASE}${ENDPOINTS.CHAT}`, {
      method: "POST",
      body: JSON.stringify({
        prompt,
        inference_type: currentInferenceMode,
        max_tokens: 512
      })
    });

    const data = await response.json();

    if (response.ok) {
      // Remove loading message
      removeLoadingMessage(loadingId);
      
      // Add assistant message
      addAssistantMessage(
        data.output || "No optimization available.",
        data.inference_type || currentInferenceMode,
        data.model_used || (currentInferenceMode === "pro" ? "GPT-4" : "GPT-3.5"),
        data.tokens_used || "N/A"
      );
      
      // Reload chat history
      await loadChatHistory();
      
      showToast("Response received!", "success", 2000);
    } else {
      throw new Error(data.detail || `HTTP ${response.status}`);
    }
  } catch (error) {
    console.error("Error:", error);
    removeLoadingMessage(loadingId);
    addErrorMessage(error.message);
    showToast("Failed to get response", "error");
  } finally {
    setLoadingState(false);
    input.focus();
  }
}

function setLoadingState(loading) {
  isLoading = loading;
  const sendBtn = document.getElementById("sendBtn");
  const input = document.getElementById("promptInput");
  
  if (sendBtn) {
    sendBtn.disabled = loading;
    sendBtn.innerHTML = loading ? 
      '<span class="loading-spinner"></span><span>Sending...</span>' : 
      '<span>📤</span><span>Send</span>';
  }
  
  if (input) {
    input.disabled = loading;
  }
}

function hideWelcomeMessage() {
  const welcomeMessage = document.getElementById("welcomeMessage");
  if (welcomeMessage) {
    welcomeMessage.style.display = "none";
  }
}

// ===== MESSAGE DISPLAY =====
function addUserMessage(text) {
  const chatMessages = document.getElementById("chatMessages");
  const messageDiv = document.createElement("div");
  messageDiv.className = "message user-message";
  messageDiv.innerHTML = `
    <div class="message-avatar">👤</div>
    <div class="message-content">
      <div class="message-header">
        <span class="message-role">You</span>
      </div>
      <div class="message-text">${escapeHtml(text)}</div>
    </div>
  `;
  chatMessages.appendChild(messageDiv);
  scrollToBottom();
}

function addAssistantMessage(text, mode, model, tokens) {
  const chatMessages = document.getElementById("chatMessages");
  const messageDiv = document.createElement("div");
  messageDiv.className = "message assistant-message";
  messageDiv.innerHTML = `
    <div class="message-avatar">🤖</div>
    <div class="message-content">
      <div class="message-header">
        <span class="message-role">Assistant</span>
      </div>
      <div class="message-text">
        <pre><code>${escapeHtml(text)}</code></pre>
      </div>
      <div class="message-actions bottom-actions">
        <button class="message-action-btn" onclick="copyMessageText(this)" title="Copy message">
          <span>📋</span>
          <span>Copy</span>
        </button>
        <button class="message-action-btn like-btn" onclick="likeMessage(this)" title="Like message">
          <span>❤️</span>
        </button>
      </div>
      <div class="message-meta">
        <div class="meta-item">
          <span>Mode:</span>
          <span class="chat-history-mode ${mode}">${mode.toUpperCase()}</span>
        </div>
        <div class="meta-item">
          <span>Model:</span>
          <span>${model}</span>
        </div>
        <div class="meta-item">
          <span>Tokens:</span>
          <span>${tokens}</span>
        </div>
      </div>
    </div>
  `;
  chatMessages.appendChild(messageDiv);
  scrollToBottom();
}

function addErrorMessage(message) {
  const chatMessages = document.getElementById("chatMessages");
  const messageDiv = document.createElement("div");
  messageDiv.className = "message assistant-message";
  messageDiv.innerHTML = `
    <div class="message-avatar">⚠️</div>
    <div class="message-content">
      <div class="message-header">
        <span class="message-role">Error</span>
      </div>
      <div class="message-text" style="color: var(--danger-color);">
        ${escapeHtml(message)}
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

// ===== CHAT HISTORY =====
async function loadChatHistory() {
  try {
    const response = await makeAuthenticatedRequest(`${API_BASE}/prompt-history?page=1&page_size=20`, {
      method: "GET"
    });
    
    if (response.ok) {
      const data = await response.json();
      chatHistory = data.items || [];
      displayChatHistory();
    } else {
      console.error("Failed to load chat history:", response.status);
    }
  } catch (error) {
    console.error("Error loading chat history:", error);
  }
}

function displayChatHistory() {
  const historyList = document.getElementById("chatHistoryList");
  if (!historyList) return;
  
  if (chatHistory.length === 0) {
    historyList.innerHTML = `
      <div style="text-align: center; color: var(--text-muted); padding: 2rem 1rem; font-size: 0.875rem;">
        No chat history yet.<br>
        Start a conversation to see your history here!
      </div>
    `;
    return;
  }
  
  const historyHTML = chatHistory.map(item => `
    <div class="chat-history-item" onclick="loadChatHistoryItem('${item.id}')" role="listitem">
      <div class="chat-history-preview">
        ${escapeHtml(item.original_prompt.substring(0, 60))}${item.original_prompt.length > 60 ? '...' : ''}
      </div>
      <div class="chat-history-meta">
        <span class="chat-history-mode ${item.inference_type}">${item.inference_type.toUpperCase()}</span>
        <span>${formatTimestamp(item.created_at)}</span>
      </div>
    </div>
  `).join('');
  
  historyList.innerHTML = historyHTML;
}

async function loadChatHistoryItem(historyId) {
  try {
    const response = await makeAuthenticatedRequest(`${API_BASE}/prompt-history/${historyId}`, {
      method: "GET"
    });
    
    if (response.ok) {
      const data = await response.json();
      
      // Clear current chat
      const chatMessages = document.getElementById("chatMessages");
      if (chatMessages) {
        chatMessages.innerHTML = "";
      }
      
      // Add history messages
      addUserMessage(data.original_prompt);
      addAssistantMessage(
        data.optimized_prompt,
        data.inference_type,
        data.model_used,
        data.tokens_used
      );
      
      // Set input to original prompt
      const input = document.getElementById("promptInput");
      if (input) {
        input.value = data.original_prompt;
        autoResizeTextarea();
      }
      
      showToast("Chat history loaded", "success", 2000);
    } else {
      showToast("Failed to load chat history", "error");
    }
  } catch (error) {
    console.error("Error loading chat history item:", error);
    showToast("Error loading chat history", "error");
  }
}

// ===== ACTION HANDLERS =====
function handleNewChat() {
  console.log("Starting new chat...");
  
  // Clear chat messages
  const chatMessages = document.getElementById("chatMessages");
  if (chatMessages) {
    chatMessages.innerHTML = `
      <div class="welcome-message" id="welcomeMessage">
        <div class="welcome-content">
          <h1 class="welcome-title">What are you working on?</h1>
          <p class="welcome-subtitle">
            Start a new conversation by typing your prompt below.
          </p>
        </div>
      </div>
    `;
  }
  
  // Clear input
  const input = document.getElementById("promptInput");
  if (input) {
    input.value = "";
    autoResizeTextarea();
    input.focus();
  }
  
  // Reset current chat ID
  currentChatId = null;
  
  showToast("New chat started", "success", 2000);
}

async function handleLogout() {
  const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
  
  try {
    // Stop proactive refresh timers
    stopProactiveTokenRefresh();
    
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
    localStorage.clear();
    window.location.href = ROUTES.AUTH;
  }
}

function handleSettings() {
  showToast("Settings feature coming soon!", "info");
}

// ===== UTILITY FUNCTIONS =====
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function copyMessageText(button) {
  const messageContent = button.closest('.message-content');
  const textElement = messageContent.querySelector('.message-text');
  const textToCopy = textElement.textContent.trim();
  
  navigator.clipboard.writeText(textToCopy).then(() => {
    const copyText = button.querySelector("span:last-child");
    const originalText = copyText.textContent;
    
    button.classList.add("copied");
    copyText.textContent = "Copied!";
    
    setTimeout(() => {
      button.classList.remove("copied");
      copyText.textContent = originalText;
    }, 2000);
    
  }).catch(err => {
    console.error("Copy failed:", err);
    showToast("Failed to copy message", "error");
  });
}

function likeMessage(button) {
  const heartIcon = button.querySelector("span");
  const originalIcon = heartIcon.textContent;
  
  button.classList.add("liked");
  heartIcon.textContent = "💖"; // Filled heart when liked
  
  setTimeout(() => {
    button.classList.remove("liked");
    heartIcon.textContent = originalIcon;
  }, 2000);
  
  showToast("Thanks for the feedback!", "success", 2000);
}

// ===== TOKEN VALIDATION =====
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

// ===== GLOBAL FUNCTIONS =====
window.copyMessageText = copyMessageText;
window.likeMessage = likeMessage;
window.loadChatHistoryItem = loadChatHistoryItem;

// ===== CSS ANIMATIONS =====
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(100%);
      opacity: 0;
    }
  }
`;
document.head.appendChild(style);