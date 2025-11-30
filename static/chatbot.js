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
let currentUserProfile = null;
let activePrompt = null;
let activeCollaboration = null;
let collaborationMembers = [];
let collaborationComments = [];
let pendingCommentSelection = null;
let editingCommentId = null;
let collaborationOnlyMode = false;

// ===== AUTHENTICATION CHECK =====
function checkAuthentication() {
  console.log("Checking authentication...");
  console.log("Token:", token ? "exists" : "missing");
  console.log("User email:", userEmail ? "exists" : "missing");
  console.log("Current path:", window.location.pathname);
  
  if (!token || !userEmail) {
    console.log("No authentication found, redirecting to login...");
    console.log("Redirecting to:", ROUTES.AUTH);
    window.location.href = ROUTES.AUTH;
    return false;
  }
  console.log("Authentication check passed");
  return true;
}

// ===== UTILITY FUNCTIONS =====
function showToast(message, type = "info", duration = 3200) {
  const palette = {
    success: {
      bg: "rgba(34, 197, 94, 0.16)",
      border: "rgba(34, 197, 94, 0.45)",
      icon: "✅"
    },
    error: {
      bg: "rgba(239, 68, 68, 0.16)",
      border: "rgba(239, 68, 68, 0.45)",
      icon: "⚠️"
    },
    warning: {
      bg: "rgba(245, 158, 11, 0.18)",
      border: "rgba(245, 158, 11, 0.45)",
      icon: "⚡"
    },
    info: {
      bg: "rgba(99, 102, 241, 0.18)",
      border: "rgba(129, 140, 248, 0.45)",
      icon: "💡"
    }
  };

  const config = palette[type] || palette.info;
  const toast = document.createElement("div");
  toast.className = `reprompt-toast toast-${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${config.icon}</span>
    <span class="toast-message">${message}</span>
  `;

  const existingToasts = document.querySelectorAll(".reprompt-toast").length;
  toast.style.cssText = `
    position: fixed;
    right: 24px;
    bottom: ${24 + existingToasts * 72}px;
    display: inline-flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.85rem 1.2rem;
    background: ${config.bg};
    border: 1px solid ${config.border};
    color: #e2e8f0;
    border-radius: 14px;
    backdrop-filter: blur(12px);
    box-shadow: 0 24px 48px -20px rgba(15, 23, 42, 0.65);
    z-index: 10000;
    font-size: 0.9rem;
    font-weight: 500;
    min-width: 240px;
    animation: slideIn 0.3s ease;
  `;

  document.body.appendChild(toast);

  const iconEl = toast.querySelector(".toast-icon");
  if (iconEl) {
    iconEl.style.cssText = `
      font-size: 1.05rem;
      display: inline-flex;
      align-items: center;
    `;
  }

  const messageEl = toast.querySelector(".toast-message");
  if (messageEl) {
    messageEl.style.cssText = `
      flex: 1;
      line-height: 1.5;
    `;
  }
  
  setTimeout(() => {
    toast.style.animation = "slideOut 0.3s ease";
    setTimeout(() => {
      toast.remove();
      const remainingToasts = document.querySelectorAll(".reprompt-toast");
      remainingToasts.forEach((el, index) => {
        el.style.bottom = `${24 + index * 72}px`;
      });
    }, 280);
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

// ===== USER PROFILE =====
async function getUserProfile() {
  try {
    const response = await makeAuthenticatedRequest(`${API_BASE}/auth${ENDPOINTS.PROFILE}`, {
      method: "GET"
    });
    
    if (response.ok) {
      const profile = await response.json();
      return profile;
    } else {
      console.error("Failed to get user profile:", response.status);
      return null;
    }
  } catch (error) {
    console.error("Error getting user profile:", error);
    return null;
  }
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

    // Capture share token from query parameters or session
    const urlParams = new URLSearchParams(window.location.search);
    let shareToken = urlParams.get("share") || sessionStorage.getItem("pendingShareToken");
    if (shareToken) {
      sessionStorage.setItem("pendingShareToken", shareToken);
      if (!token || !userEmail) {
        sessionStorage.setItem("pendingShareRedirect", `/chatbot?share=${shareToken}`);
      }
    }

    // Check authentication first
    if (!checkAuthentication()) {
      return; // Exit if not authenticated
    }

    // Validate authentication
    await validateToken();

    // Fetch profile for collaborator context
    currentUserProfile = await getUserProfile();

    // Start proactive token refresh
    startProactiveTokenRefresh();

    // Initialize UI components
    initializeUserProfile();
    initializeInferenceToggle();
    initializeEventListeners();
    initializeInputHandling();
    initializeScrollHandling();
    initializeCollaborationListeners();

    // Load initial data
    await loadChatHistory();
    updateShareButtonState();

    if (shareToken) {
      await processShareToken(shareToken);
      sessionStorage.removeItem("pendingShareToken");
      sessionStorage.removeItem("pendingShareRedirect");
      removeShareTokenFromUrl();
    }

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

  if (currentUserProfile && currentUserProfile.email) {
    userEmail = currentUserProfile.email;
    localStorage.setItem(STORAGE_KEYS.USER_EMAIL, userEmail);
  }
  
  if (userAvatar) {
    const initials = getInitials(userEmail);
    userAvatar.querySelector("#userInitials").textContent = initials;
  }
  
  if (userName) {
    const displayName = currentUserProfile?.email?.split('@')[0] || userEmail.split('@')[0];
    userName.textContent = displayName;
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
      top: 22px;
      right: 24px;
      background: rgba(99, 102, 241, 0.16);
      color: #e2e8f0;
      padding: 0.45rem 0.9rem;
      border-radius: 999px;
      font-size: 0.72rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      border: 1px solid rgba(129, 140, 248, 0.32);
      box-shadow: 0 18px 36px -22px rgba(15, 23, 42, 0.65);
      backdrop-filter: blur(12px);
      z-index: 1200;
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
      sessionStatus.style.background = 'rgba(239, 68, 68, 0.2)';
      sessionStatus.style.border = '1px solid rgba(239, 68, 68, 0.45)';
    } else if (timeUntilExpiry <= 15 * 60 * 1000) {
      sessionStatus.style.background = 'rgba(245, 158, 11, 0.18)';
      sessionStatus.style.border = '1px solid rgba(245, 158, 11, 0.45)';
    } else {
      sessionStatus.style.background = 'rgba(99, 102, 241, 0.16)';
      sessionStatus.style.border = '1px solid rgba(129, 140, 248, 0.32)';
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

// ===== COLLABORATION SUPPORT =====
function initializeCollaborationListeners() {
  const shareBtn = document.getElementById("shareBtn");
  if (shareBtn) {
    shareBtn.addEventListener("click", () => {
      if (!activePrompt) {
        showToast("Load a prompt before sharing.", "warning");
        return;
      }
      if (!isPromptOwner()) {
        showToast("Only the prompt owner can manage share links.", "error");
        return;
      }
      populateShareModalDefaults();
      openShareModal();
    });
  }

  const shareModal = document.getElementById("shareModal");
  const closeShareModalBtn = document.getElementById("closeShareModalBtn");
  if (closeShareModalBtn) {
    closeShareModalBtn.addEventListener("click", closeShareModal);
  }
  if (shareModal) {
    shareModal.addEventListener("click", (event) => {
      if (event.target === shareModal) {
        closeShareModal();
      }
    });
  }

  const shareForm = document.getElementById("shareForm");
  if (shareForm) {
    shareForm.addEventListener("submit", handleShareFormSubmit);
  }

  const copyShareUrlBtn = document.getElementById("copyShareUrlBtn");
  if (copyShareUrlBtn) {
    copyShareUrlBtn.addEventListener("click", copyShareUrlToClipboard);
  }

  const refreshBtn = document.getElementById("collaborationRefreshBtn");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", async () => {
      if (activeCollaboration) {
        await hydrateCollaborationById(activeCollaboration.id);
        showToast("Collaboration refreshed", "success", 1800);
      } else if (activePrompt) {
        await hydrateCollaborationForHistory(activePrompt.id);
      }
    });
  }

  const saveHandoffBtn = document.getElementById("saveHandoffBtn");
  if (saveHandoffBtn) {
    saveHandoffBtn.addEventListener("click", saveHandoffNotes);
  }

  const toggleComposerBtn = document.getElementById("toggleCommentComposerBtn");
  if (toggleComposerBtn) {
    toggleComposerBtn.addEventListener("click", () => {
      if (!activeCollaboration) {
        showToast("Create a share link to start collaborating.", "warning");
        return;
      }
      if (!canComment()) {
        showToast("You need comment access to add notes.", "warning");
        return;
      }
      const composer = document.getElementById("commentComposer");
      if (composer) {
        if (composer.style.display === "flex") {
          closeCommentComposer();
        } else {
          pendingCommentSelection = null;
          openCommentComposer();
        }
      }
    });
  }

  const cancelCommentBtn = document.getElementById("cancelCommentBtn");
  if (cancelCommentBtn) {
    cancelCommentBtn.addEventListener("click", () => closeCommentComposer());
  }

  const submitCommentBtn = document.getElementById("submitCommentBtn");
  if (submitCommentBtn) {
    submitCommentBtn.addEventListener("click", submitComment);
  }

  const commentsList = document.getElementById("commentsList");
  if (commentsList) {
    commentsList.addEventListener("click", handleCommentListClick);
  }

  document.addEventListener("mouseup", handleCommentSelection);
  document.addEventListener("keyup", (event) => {
    if (event.key === "Escape") {
      closeShareModal();
      closeCommentComposer();
    }
  });
}

function removeShareTokenFromUrl() {
  const url = new URL(window.location.href);
  if (url.searchParams.has("share")) {
    url.searchParams.delete("share");
    const newSearch = url.searchParams.toString();
    const newUrl = newSearch ? `${url.pathname}?${newSearch}` : url.pathname;
    window.history.replaceState({}, document.title, newUrl);
  }
}

async function processShareToken(shareToken) {
  try {
    const response = await makeAuthenticatedRequest(`${API_BASE}/collaboration/share/${shareToken}/accept`, {
      method: "POST",
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Unable to join collaboration");
    }

    showToast("Joined collaboration link", "success", 2200);
    renderPromptConversation(data.prompt);
    await hydrateCollaborationById(data.collaboration_id);
    collaborationOnlyMode = activeCollaboration ? !isPromptOwner() : false;
    await loadChatHistory();
  } catch (error) {
    console.error("Failed to process share token:", error);
    showToast(error.message || "Unable to open shared prompt", "error");
  }
}

async function hydrateCollaborationById(collaborationId) {
  try {
    const response = await makeAuthenticatedRequest(`${API_BASE}/collaboration/${collaborationId}`, {
      method: "GET",
    });

    if (response.status === 404) {
      clearCollaborationState();
      return;
    }

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to load collaboration details");
    }

    const data = await response.json();
    activeCollaboration = data;
    collaborationMembers = data.members || [];

    await loadComments(data.id);
    updateCollaborationPanel();
    if (activePrompt) {
      collaborationOnlyMode = !isPromptOwner();
      await loadChatHistory();
    }
  } catch (error) {
    console.error("Failed to hydrate collaboration:", error);
    showToast(error.message || "Collaboration unavailable", "error");
    clearCollaborationState();
  }
}

async function hydrateCollaborationForHistory(historyId) {
  if (!historyId) {
    clearCollaborationState();
    return;
  }
  try {
    const response = await makeAuthenticatedRequest(`${API_BASE}/collaboration/history/${historyId}`, {
      method: "GET",
    });

    if (response.status === 404) {
      clearCollaborationState();
      return;
    }

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to load collaboration");
    }

    const data = await response.json();
    if (!data) {
      clearCollaborationState();
      return;
    }

    activeCollaboration = data;
    collaborationMembers = data.members || [];
    await loadComments(data.id);
    updateCollaborationPanel();
  } catch (error) {
    console.error("Failed to fetch collaboration by history:", error);
    clearCollaborationState();
  }
}

function clearCollaborationState() {
  activeCollaboration = null;
  collaborationMembers = [];
  collaborationComments = [];
  pendingCommentSelection = null;
  editingCommentId = null;
  collaborationOnlyMode = false;
  updateCollaborationPanel();
}

function setActivePrompt(promptData) {
  activePrompt = promptData;
  currentChatId = promptData?.id || null;
}

function renderPromptConversation(promptData) {
  const chatMessages = document.getElementById("chatMessages");
  if (!chatMessages || !promptData) return;

  chatMessages.innerHTML = "";
  hideWelcomeMessage();
  setActivePrompt(promptData);

  addUserMessage(promptData.original_prompt);
  addAssistantMessage(
    promptData.optimized_prompt,
    promptData.inference_type,
    promptData.model_used,
    promptData.tokens_used,
    promptData.id
  );
  scrollToBottom();
  renderHandoffSection();
}

async function loadPromptDetails(historyId) {
  try {
    const response = await makeAuthenticatedRequest(`${API_BASE}/prompt-history/${historyId}`, {
      method: "GET",
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to load prompt");
    }

    const promptData = await response.json();
    renderPromptConversation(promptData);
    await hydrateCollaborationForHistory(historyId);
    if (!activeCollaboration || isPromptOwner()) {
      collaborationOnlyMode = false;
      await loadChatHistory();
    }
  } catch (error) {
    console.error("Failed to load prompt details:", error);
  }
}

function updateCollaborationPanel() {
  const panel = document.getElementById("collaborationPanel");
  if (!panel) return;

  if (!activePrompt || !activeCollaboration) {
    panel.style.display = "none";
    updateShareButtonState();
    updatePermissionBadge();
    renderCollaborationSummary();
    renderHandoffSection();
    renderCommentsList();
    updateCommentComposerState();
    return;
  }

  panel.style.display = "flex";
  updateShareButtonState();
  updatePermissionBadge();
  renderCollaborationSummary();
  renderHandoffSection();
  renderCommentsList();
  updateCommentComposerState();
}

function updateShareButtonState() {
  const shareBtn = document.getElementById("shareBtn");
  if (!shareBtn) return;

  if (!activePrompt) {
    shareBtn.disabled = true;
    shareBtn.title = "Load a prompt to create a share link";
    return;
  }

  const knownOwnerFromCollab =
    activeCollaboration && currentUserProfile && activeCollaboration.owner_id !== currentUserProfile.id;
  const knownOwnerFromPrompt =
    activePrompt && currentUserProfile && activePrompt.user_id && activePrompt.user_id !== currentUserProfile.id;

  if (knownOwnerFromCollab || (!activeCollaboration && knownOwnerFromPrompt)) {
    shareBtn.disabled = true;
    shareBtn.title = "Only the prompt owner can manage the share link";
    return;
  }

  shareBtn.disabled = false;
  shareBtn.title = "";
}

function updatePermissionBadge() {
  const badge = document.getElementById("collabPermissionBadge");
  if (!badge) return;

  const permission = getActivePermission();
  if (activeCollaboration && permission) {
    badge.textContent = permission.toUpperCase();
    badge.style.display = "inline-flex";
  } else {
    badge.style.display = "none";
  }
}

function renderCollaborationSummary() {
  const summary = document.getElementById("collaborationSummary");
  if (!summary) return;

  if (!activeCollaboration) {
    summary.textContent = "Invite teammates to review this prompt.";
    return;
  }

  const activeMembers = (collaborationMembers || []).filter((member) => member.status === "active");
  const collaboratorCount = activeMembers.length;
  const permissionLabel = activeCollaboration.base_permission?.toUpperCase() || "VIEW";

  const ownerLabel = isPromptOwner() ? "You" : "Owner";
  const collaboratorPhrase = collaboratorCount === 1 ? "1 collaborator" : `${collaboratorCount} collaborators`;

  summary.textContent = `${ownerLabel} + ${collaboratorPhrase} • Link grants ${permissionLabel} access`;
}

function renderHandoffSection() {
  const textarea = document.getElementById("handoffTextarea");
  const hint = document.getElementById("handoffHintText");
  const statusHint = document.getElementById("handoffStatusHint");
  const saveBtn = document.getElementById("saveHandoffBtn");

  if (!textarea || !hint || !saveBtn) return;

  const notes = activePrompt?.handoff_notes || "";
  textarea.value = notes;

  if (!activeCollaboration) {
    textarea.disabled = true;
    saveBtn.disabled = true;
    hint.textContent = "Create a share link to enable handoff notes.";
    if (statusHint) statusHint.textContent = "";
    return;
  }

  const canEdit = canEditCollaboration();
  textarea.disabled = !canEdit;
  saveBtn.disabled = !canEdit;

  if (canEdit) {
    hint.textContent = "Add guidance for the next teammate. Notes are shared with all collaborators.";
  } else {
    hint.textContent = "You have read-only access to handoff notes.";
  }

  if (statusHint) {
    if (notes) {
      const updatedAt = activePrompt?.updated_at ? formatTimestamp(activePrompt.updated_at) : "recently";
      statusHint.textContent = `Last updated ${updatedAt}`;
    } else {
      statusHint.textContent = "";
    }
  }
}

async function saveHandoffNotes() {
  if (!activeCollaboration || !canEditCollaboration()) {
    showToast("You need edit access to update handoff notes.", "warning");
    return;
  }

  const textarea = document.getElementById("handoffTextarea");
  const saveBtn = document.getElementById("saveHandoffBtn");
  if (!textarea || !saveBtn) return;

  const notes = textarea.value.trim();
  saveBtn.disabled = true;
  try {
    const response = await makeAuthenticatedRequest(`${API_BASE}/collaboration/${activeCollaboration.id}/handoff`, {
      method: "PUT",
      body: JSON.stringify({ handoff_notes: notes || null }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to save notes");
    }

    const updatedPrompt = await response.json();
    activePrompt = updatedPrompt;
    renderHandoffSection();
    showToast("Handoff notes saved", "success", 2000);
  } catch (error) {
    console.error("Failed to save handoff notes:", error);
    showToast(error.message || "Unable to save notes", "error");
  } finally {
    saveBtn.disabled = !canEditCollaboration();
  }
}

async function loadComments(collaborationId) {
  if (!collaborationId) return;
  try {
    const response = await makeAuthenticatedRequest(`${API_BASE}/collaboration/${collaborationId}/comments`, {
      method: "GET",
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to load comments");
    }

    collaborationComments = await response.json();
    renderCommentsList();
  } catch (error) {
    console.error("Failed to load comments:", error);
    collaborationComments = [];
    renderCommentsList();
  }
}

function renderCommentsList() {
  const commentsList = document.getElementById("commentsList");
  const emptyState = document.getElementById("commentsEmptyState");
  if (!commentsList) return;

  commentsList.querySelectorAll(".comment-card").forEach((node) => node.remove());

  if (!activeCollaboration || collaborationComments.length === 0) {
    if (emptyState) emptyState.style.display = "block";
    updateCommentComposerState();
    return;
  }

  if (emptyState) emptyState.style.display = "none";

  collaborationComments.forEach((comment) => {
    const card = buildCommentCard(comment);
    commentsList.appendChild(card);
  });
  updateCommentComposerState();
}

function buildCommentCard(comment) {
  const card = document.createElement("div");
  card.className = `comment-card${comment.resolved ? " resolved" : ""}`;
  card.dataset.commentId = comment.id;

  const header = document.createElement("div");
  header.className = "comment-header";

  const meta = document.createElement("div");
  meta.className = "comment-meta";

  const authorSpan = document.createElement("span");
  authorSpan.textContent = getCommentAuthorLabel(comment);
  meta.appendChild(authorSpan);

  const targetSpan = document.createElement("span");
  targetSpan.textContent = comment.target_type === "original" ? "Original" : "Optimized";
  meta.appendChild(targetSpan);

  const timeSpan = document.createElement("span");
  timeSpan.textContent = formatTimestamp(comment.created_at);
  meta.appendChild(timeSpan);

  if (comment.resolved) {
    const resolvedSpan = document.createElement("span");
    resolvedSpan.textContent = "Resolved";
    meta.appendChild(resolvedSpan);
  }

  header.appendChild(meta);

  const actions = document.createElement("div");
  actions.className = "comment-actions";

  const isAuthor = currentUserProfile && comment.author_id === currentUserProfile.id;
  if (canEditCollaboration() || isAuthor) {
    const resolveBtn = document.createElement("button");
    resolveBtn.dataset.action = "toggle-resolve";
    resolveBtn.dataset.commentId = comment.id;
    resolveBtn.textContent = comment.resolved ? "Reopen" : "Resolve";
    actions.appendChild(resolveBtn);
  }

  if (isAuthor) {
    const editBtn = document.createElement("button");
    editBtn.dataset.action = "edit";
    editBtn.dataset.commentId = comment.id;
    editBtn.textContent = "Edit";
    actions.appendChild(editBtn);
  }

  if (canEditCollaboration() || isAuthor) {
    const deleteBtn = document.createElement("button");
    deleteBtn.dataset.action = "delete";
    deleteBtn.dataset.commentId = comment.id;
    deleteBtn.textContent = "Delete";
    actions.appendChild(deleteBtn);
  }

  if (actions.childElementCount > 0) {
    header.appendChild(actions);
  }

  const body = document.createElement("div");
  body.className = "comment-body";
  body.textContent = comment.body;

  card.appendChild(header);
  card.appendChild(body);

  const quote = getCommentQuote(comment);
  if (quote) {
    const quoteEl = document.createElement("div");
    quoteEl.className = "comment-quote";
    quoteEl.textContent = quote;
    card.appendChild(quoteEl);
  }

  return card;
}

function getCommentAuthorLabel(comment) {
  const member = (collaborationMembers || []).find((entry) => entry.user_id === comment.author_id);
  if (member?.email) {
    return member.email.split("@")[0];
  }
  return comment.author_id.slice(0, 6);
}

function getCommentQuote(comment) {
  if (!activePrompt) return null;
  if (typeof comment.anchor_start !== "number" || typeof comment.anchor_end !== "number") {
    return null;
  }

  const sourceText =
    comment.target_type === "original" ? activePrompt.original_prompt : activePrompt.optimized_prompt;
  if (!sourceText) return null;

  return sourceText.substring(comment.anchor_start, comment.anchor_end).trim();
}

async function submitComment() {
  if (!activeCollaboration) {
    showToast("No collaboration open for this prompt.", "warning");
    return;
  }

  if (!canComment()) {
    showToast("You need comment access to post feedback.", "warning");
    return;
  }

  const bodyField = document.getElementById("commentBody");
  const targetField = document.getElementById("commentTarget");
  if (!bodyField || !targetField) return;

  const bodyText = bodyField.value.trim();
  if (!bodyText) {
    showToast("Comment cannot be empty.", "error");
    return;
  }

  const targetType = targetField.value;

  try {
    if (editingCommentId) {
      await updateComment(editingCommentId, { body: bodyText });
      showToast("Comment updated", "success", 1800);
    } else {
      const payload = {
        target_type: targetType,
        body: bodyText,
        anchor_start: null,
        anchor_end: null,
      };

      if (pendingCommentSelection && pendingCommentSelection.targetType === targetType) {
        payload.anchor_start = pendingCommentSelection.anchorStart;
        payload.anchor_end = pendingCommentSelection.anchorEnd;
      }

      await addComment(payload);
      showToast("Comment added", "success", 1800);
    }

    await loadComments(activeCollaboration.id);
    closeCommentComposer();
  } catch (error) {
    console.error("Failed to submit comment:", error);
    showToast(error.message || "Unable to save comment", "error");
  }
}

async function addComment(payload) {
  const response = await makeAuthenticatedRequest(`${API_BASE}/collaboration/${activeCollaboration.id}/comments`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to add comment");
  }
}

async function updateComment(commentId, payload) {
  const response = await makeAuthenticatedRequest(
    `${API_BASE}/collaboration/${activeCollaboration.id}/comments/${commentId}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to update comment");
  }
}

async function deleteComment(commentId) {
  const response = await makeAuthenticatedRequest(
    `${API_BASE}/collaboration/${activeCollaboration.id}/comments/${commentId}`,
    {
      method: "DELETE",
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to delete comment");
  }
}

function handleCommentListClick(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) return;

  const action = button.dataset.action;
  const commentId = button.dataset.commentId;
  if (!commentId) return;

  const comment = findCommentById(commentId);
  if (!comment) return;

  if (action === "delete") {
    if (confirm("Delete this comment?")) {
      deleteComment(commentId)
        .then(() => loadComments(activeCollaboration.id))
        .then(() => showToast("Comment deleted", "success", 1800))
        .catch((error) => {
          console.error("Delete comment failed:", error);
          showToast(error.message || "Unable to delete comment", "error");
        });
    }
    return;
  }

  if (action === "toggle-resolve") {
    updateComment(commentId, { resolved: !comment.resolved })
      .then(() => loadComments(activeCollaboration.id))
      .then(() => showToast(comment.resolved ? "Comment reopened" : "Comment resolved", "success", 1800))
      .catch((error) => {
        console.error("Resolve comment failed:", error);
        showToast(error.message || "Unable to update comment", "error");
      });
    return;
  }

  if (action === "edit") {
    openCommentComposer({
      commentId,
      targetType: comment.target_type,
      body: comment.body,
      quote: getCommentQuote(comment),
    });
  }
}

function findCommentById(commentId) {
  return (collaborationComments || []).find((comment) => comment.id === commentId);
}

function openCommentComposer(options = {}) {
  const composer = document.getElementById("commentComposer");
  const targetField = document.getElementById("commentTarget");
  const bodyField = document.getElementById("commentBody");
  const preview = document.getElementById("commentSelectionPreview");

  if (!composer || !targetField || !bodyField || !preview) return;

  composer.style.display = "flex";
  targetField.value = options.targetType || targetField.value || "original";
  bodyField.value = options.body || "";

  if (options.commentId) {
    editingCommentId = options.commentId;
    pendingCommentSelection = null;
    preview.textContent = options.quote
      ? `Anchored snippet: "${options.quote}"`
      : "Updating existing comment";
  } else if (pendingCommentSelection?.quote) {
    preview.textContent = `Anchored snippet: "${pendingCommentSelection.quote}"`;
  } else if (options.quote) {
    preview.textContent = `Anchored snippet: "${options.quote}"`;
  } else {
    resetCommentSelectionPreview();
  }

  bodyField.focus();
}

function closeCommentComposer() {
  const composer = document.getElementById("commentComposer");
  const bodyField = document.getElementById("commentBody");
  const targetField = document.getElementById("commentTarget");
  if (!composer || !bodyField || !targetField) return;

  composer.style.display = "none";
  bodyField.value = "";
  editingCommentId = null;
  pendingCommentSelection = null;
  resetCommentSelectionPreview();
}

function updateCommentComposerState() {
  const toggleComposerBtn = document.getElementById("toggleCommentComposerBtn");
  const composer = document.getElementById("commentComposer");
  if (!toggleComposerBtn) return;

  if (!activeCollaboration || !canComment()) {
    toggleComposerBtn.disabled = true;
    if (composer) composer.style.display = "none";
    return;
  }

  toggleComposerBtn.disabled = false;
}

function resetCommentSelectionPreview() {
  const preview = document.getElementById("commentSelectionPreview");
  if (preview) {
    preview.textContent = "Select text in the prompt to anchor your comment.";
  }
}

function handleCommentSelection() {
  if (!activeCollaboration || !canComment() || editingCommentId) return;

  const selection = window.getSelection();
  if (!selection || selection.isCollapsed || selection.rangeCount === 0) return;

  const range = selection.getRangeAt(0);
  const container =
    range.commonAncestorContainer.nodeType === Node.TEXT_NODE
      ? range.commonAncestorContainer.parentElement
      : range.commonAncestorContainer;

  if (!container) return;
  const messageText = container.closest(".message-text");
  if (!messageText) return;

  const targetType = messageText.dataset.targetType;
  if (!targetType) return;

  const selectedText = selection.toString().trim();
  if (!selectedText) return;

  const { start, end } = computeSelectionOffsets(range, messageText);
  pendingCommentSelection = {
    targetType,
    anchorStart: start,
    anchorEnd: end,
    quote: selectedText,
  };

  openCommentComposer({
    targetType,
    quote: selectedText,
  });

  selection.removeAllRanges();
}

function computeSelectionOffsets(range, container) {
  const preRange = range.cloneRange();
  preRange.selectNodeContents(container);
  preRange.setEnd(range.startContainer, range.startOffset);
  const start = preRange.toString().length;
  const end = start + range.toString().length;
  return { start, end };
}

function canComment() {
  const permission = getActivePermission();
  return permission === "comment" || permission === "edit";
}

function canEditCollaboration() {
  const permission = getActivePermission();
  return permission === "edit";
}

function getActivePermission() {
  if (!activeCollaboration) return null;
  return (
    activeCollaboration.requester_permission ||
    activeCollaboration.base_permission ||
    activeCollaboration.permission ||
    null
  );
}

function isPromptOwner() {
  if (!currentUserProfile) return false;
  if (activeCollaboration && activeCollaboration.owner_id === currentUserProfile.id) {
    return true;
  }
  if (activePrompt && activePrompt.user_id === currentUserProfile.id) {
    return true;
  }
  return false;
}

function openShareModal() {
  const overlay = document.getElementById("shareModal");
  if (!overlay) return;
  overlay.style.display = "flex";
  overlay.setAttribute("aria-hidden", "false");
}

function closeShareModal() {
  const overlay = document.getElementById("shareModal");
  if (!overlay) return;
  overlay.style.display = "none";
  overlay.setAttribute("aria-hidden", "true");
}

function populateShareModalDefaults() {
  const permissionField = document.getElementById("sharePermission");
  const expiryField = document.getElementById("shareExpiry");
  const urlRow = document.getElementById("shareUrlRow");
  const urlInput = document.getElementById("shareUrl");

  if (permissionField) {
    permissionField.value = activeCollaboration?.base_permission || "view";
  }
  if (expiryField) {
    expiryField.value = "";
  }
  if (urlRow && urlInput) {
    if (activeCollaboration?.share_url) {
      urlInput.value = activeCollaboration.share_url;
      urlRow.style.display = "flex";
    } else {
      urlInput.value = "";
      urlRow.style.display = "none";
    }
  }
}

async function handleShareFormSubmit(event) {
  event.preventDefault();

  if (!activePrompt) {
    showToast("Load a prompt before sharing.", "warning");
    return;
  }

  if (!isPromptOwner()) {
    showToast("Only the prompt owner can manage share links.", "error");
    return;
  }

  const permissionField = document.getElementById("sharePermission");
  const expiryField = document.getElementById("shareExpiry");
  const urlRow = document.getElementById("shareUrlRow");
  const urlInput = document.getElementById("shareUrl");

  const payload = {
    base_permission: permissionField ? permissionField.value : "view",
  };

  if (expiryField && expiryField.value) {
    payload.expires_in_hours = Number(expiryField.value);
  }

  try {
    const response = await makeAuthenticatedRequest(`${API_BASE}/collaboration/${activePrompt.id}/share`, {
      method: "POST",
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Failed to configure share link");
    }

    if (urlRow && urlInput) {
      urlInput.value = data.share_url;
      urlRow.style.display = "flex";
    }

    await hydrateCollaborationById(data.collaboration_id);
    showToast("Share link updated", "success", 2000);
  } catch (error) {
    console.error("Share modal error:", error);
    showToast(error.message || "Unable to update share link", "error");
  }
}

function copyShareUrlToClipboard() {
  const urlInput = document.getElementById("shareUrl");
  if (!urlInput || !urlInput.value) {
    showToast("Nothing to copy yet—generate a link first.", "warning");
    return;
  }

  navigator.clipboard
    .writeText(urlInput.value)
    .then(() => showToast("Share link copied", "success", 1600))
    .catch((error) => {
      console.error("Copy share link failed:", error);
      showToast("Unable to copy link", "error");
    });
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
        data.tokens_used || "N/A",
        data.prompt_history_id
      );
      
      if (data.prompt_history_id) {
        await loadPromptDetails(data.prompt_history_id);
      } else {
        clearCollaborationState();
      }

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
      '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>';
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
        <div class="message-actions">
          <button class="message-action-btn" onclick="copyMessageText(this)" title="Copy message" aria-label="Copy message">
            <span class="copy-icon" aria-hidden="true">📋</span>
            <span class="copy-feedback" aria-hidden="true">Copied!</span>
          </button>
        </div>
      </div>
      <div class="message-text" data-target-type="original">${escapeHtml(text)}</div>
    </div>
  `;
  chatMessages.appendChild(messageDiv);
  scrollToBottom();
}

function addAssistantMessage(text, mode, model, tokens, promptHistoryId = null) {
  const chatMessages = document.getElementById("chatMessages");
  const messageDiv = document.createElement("div");
  messageDiv.className = "message assistant-message";
  
  // Set prompt history ID as data attribute
  if (promptHistoryId) {
    messageDiv.dataset.promptHistoryId = promptHistoryId;
  }
  
  messageDiv.innerHTML = `
    <div class="message-avatar">🤖</div>
    <div class="message-content">
      <div class="message-header">
        <span class="message-role">Assistant</span>
        <div class="message-actions top-actions">
          <button class="message-action-btn" onclick="copyMessageText(this)" title="Copy message" aria-label="Copy message">
            <span class="copy-icon" aria-hidden="true">📋</span>
            <span class="copy-feedback" aria-hidden="true">Copied!</span>
          </button>
        </div>
      </div>
      <div class="message-text" data-target-type="optimized">${formatMessageText(text)}</div>
      <div class="message-actions bottom-actions">
        <button class="message-action-btn like-btn" onclick="likeMessage(this)" title="Like message">
          <span>❤️</span>
        </button>
        <button class="message-action-btn dislike-btn" onclick="dislikeMessage(this)" title="Dislike message">
          <span>👎</span>
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
  if (collaborationOnlyMode && activePrompt) {
    chatHistory = [
      {
        id: activePrompt.id,
        original_prompt: activePrompt.original_prompt,
        inference_type: activePrompt.inference_type,
        created_at: activePrompt.created_at,
      },
    ];
    displayChatHistory();
    return;
  }
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
    <div class="chat-history-item" data-history-id="${item.id}" role="listitem" onclick="${collaborationOnlyMode ? 'loadSharedConversation()' : `loadChatHistoryItem('${item.id}')`}">
      ${!collaborationOnlyMode ? `<button class="chat-history-delete-btn" onclick="event.stopPropagation(); deleteChatHistoryItem('${item.id}')" title="Delete chat" aria-label="Delete chat"><img src="/static/logos/delete.png" alt="Delete" /></button>` : ''}
      <div class="chat-history-preview">
        ${escapeHtml(item.original_prompt.substring(0, 60))}${item.original_prompt.length > 60 ? '...' : ''}
      </div>
      <div class="chat-history-meta">
        <span class="chat-history-mode ${item.inference_type}">${item.inference_type.toUpperCase()}</span>
        <span>${formatTimestamp(item.created_at)}</span>
      </div>
    </div>
  `).join('');
  
  const header = collaborationOnlyMode
    ? `<div class="chat-history-shared-label">Shared conversation</div>`
    : "";

  historyList.innerHTML = header + historyHTML;
}

async function loadChatHistoryItem(historyId) {
  try {
    const response = await makeAuthenticatedRequest(`${API_BASE}/prompt-history/${historyId}`, {
      method: "GET"
    });
    
    if (response.ok) {
      const data = await response.json();

      renderPromptConversation(data);
      await hydrateCollaborationForHistory(data.id);

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

async function deleteChatHistoryItem(historyId) {
  // Confirm deletion
  if (!confirm("Are you sure you want to delete this chat? This action cannot be undone.")) {
    return;
  }

  try {
    const response = await makeAuthenticatedRequest(`${API_BASE}/prompt-history/${historyId}`, {
      method: "DELETE"
    });
    
    if (response.ok || response.status === 204) {
      showToast("Chat deleted successfully", "success", 2000);
      
      // Remove from local array
      chatHistory = chatHistory.filter(item => item.id !== historyId);
      
      // If the deleted chat was currently loaded, clear it
      if (activePrompt && activePrompt.id === historyId) {
        handleNewChat();
      }
      
      // Reload chat history to refresh the list
      await loadChatHistory();
    } else {
      const errorData = await response.json().catch(() => ({}));
      showToast(errorData.detail || "Failed to delete chat", "error");
    }
  } catch (error) {
    console.error("Error deleting chat history item:", error);
    showToast("Error deleting chat", "error");
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
  activePrompt = null;
  collaborationOnlyMode = false;
  clearCollaborationState();
  
  showToast("New chat started", "success", 2000);
}

function loadSharedConversation() {
  if (activePrompt) {
    renderPromptConversation(activePrompt);
    if (activeCollaboration) {
      updateCollaborationPanel();
    }
  }
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

function formatMessageText(text) {
  // First escape HTML to prevent XSS
  const div = document.createElement('div');
  div.textContent = text;
  let escaped = div.innerHTML;
  
  // Format section headers to be bold
  const sectionHeaders = [
    'Goal:', 'Context:', 'Constraints:', 'Output format:', 'Requirements:',
    'Instructions:', 'Steps:', 'Process:', 'Method:', 'Approach:',
    'Examples:', 'Sample:', 'Template:', 'Format:', 'Structure:',
    'Follow-up Questions:', 'Follow-up questions:', 'Follow up Questions:', 'Follow up questions:'
  ];
  
  sectionHeaders.forEach(header => {
    const regex = new RegExp(`(${header.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    escaped = escaped.replace(regex, '<strong>$1</strong>');
  });
  
  // Also format markdown-style bold text **text**
  escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  return escaped;
}

function copyMessageText(button) {
  const messageContent = button.closest('.message-content');
  const textElement = messageContent.querySelector('.message-text');
  const textToCopy = textElement.textContent.trim();
  
  navigator.clipboard.writeText(textToCopy).then(() => {
    const icon = button.querySelector(".copy-icon");
    const feedback = button.querySelector(".copy-feedback");

    button.classList.add("copied");
    button.setAttribute("aria-label", "Copied!");

    if (icon) {
      icon.setAttribute("aria-hidden", "true");
    }
    if (feedback) {
      feedback.setAttribute("aria-hidden", "false");
    }
    
    setTimeout(() => {
      button.classList.remove("copied");
      button.setAttribute("aria-label", "Copy message");
      if (icon) {
        icon.setAttribute("aria-hidden", "true");
      }
      if (feedback) {
        feedback.setAttribute("aria-hidden", "true");
      }
    }, 2000);
    
    showToast("Message copied to clipboard", "success", 2000);
  }).catch(err => {
    console.error("Copy failed:", err);
    showToast("Failed to copy message", "error");
  });
}

// Global feedback state
let feedbackState = new Map(); // prompt_history_id -> feedback_type

async function likeMessage(button) {
  const messageElement = button.closest('.message');
  const promptHistoryId = messageElement.dataset.promptHistoryId;
  
  if (!promptHistoryId) {
    console.error("Missing prompt history ID for feedback");
    showToast("Unable to submit feedback - missing prompt ID", "error");
    return;
  }
  
  const heartIcon = button.querySelector("span");
  const originalIcon = heartIcon.textContent;
  
  try {
    console.log("Submitting like feedback for prompt:", promptHistoryId);
    
    // Send feedback to backend
    const result = await submitFeedback(promptHistoryId, 'like');
    console.log("Feedback submission result:", result);
    
    // Update UI
    button.classList.add("liked");
    heartIcon.textContent = "💖";
    feedbackState.set(promptHistoryId, 'like');
    
    // Update dislike button if it exists
    const dislikeBtn = messageElement.querySelector('.dislike-btn');
    if (dislikeBtn) {
      dislikeBtn.classList.remove("disliked");
      dislikeBtn.querySelector("span").textContent = "👎";
    }
    
    showToast("Thanks for the feedback!", "success", 2000);
    
    setTimeout(() => {
      button.classList.remove("liked");
      heartIcon.textContent = originalIcon;
    }, 2000);
    
  } catch (error) {
    console.error("Failed to submit like feedback:", error);
    showToast(`Failed to submit feedback: ${error.message}`, "error");
  }
}

async function dislikeMessage(button) {
  const messageElement = button.closest('.message');
  const promptHistoryId = messageElement.dataset.promptHistoryId;
  
  if (!promptHistoryId) {
    console.error("Missing prompt history ID for feedback");
    showToast("Unable to submit feedback - missing prompt ID", "error");
    return;
  }
  
  const dislikeIcon = button.querySelector("span");
  const originalIcon = dislikeIcon.textContent;
  
  try {
    console.log("Submitting dislike feedback for prompt:", promptHistoryId);
    
    // Send feedback to backend
    const result = await submitFeedback(promptHistoryId, 'dislike');
    console.log("Feedback submission result:", result);
    
    // Update UI
    button.classList.add("disliked");
    dislikeIcon.textContent = "👎";
    feedbackState.set(promptHistoryId, 'dislike');
    
    // Update like button if it exists
    const likeBtn = messageElement.querySelector('.like-btn');
    if (likeBtn) {
      likeBtn.classList.remove("liked");
      likeBtn.querySelector("span").textContent = "❤️";
    }
    
    showToast("Thanks for the feedback!", "success", 2000);
    
    setTimeout(() => {
      button.classList.remove("disliked");
      dislikeIcon.textContent = originalIcon;
    }, 2000);
    
  } catch (error) {
    console.error("Failed to submit dislike feedback:", error);
    showToast(`Failed to submit feedback: ${error.message}`, "error");
  }
}

async function submitFeedback(promptHistoryId, feedbackType) {
  console.log("Submitting feedback:", { promptHistoryId, feedbackType });
  
  const requestBody = {
    prompt_history_id: promptHistoryId,
    feedback_type: feedbackType
  };
  
  console.log("Sending feedback request:", requestBody);
  console.log("API URL:", `${API_BASE}${ENDPOINTS.FEEDBACK}`);
  
  const response = await makeAuthenticatedRequest(`${API_BASE}${ENDPOINTS.FEEDBACK}`, {
    method: 'POST',
    body: JSON.stringify(requestBody)
  });
  
  console.log("Feedback response status:", response.status);
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to submit feedback');
  }
  
  return await response.json();
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
window.dislikeMessage = dislikeMessage;
window.loadChatHistoryItem = loadChatHistoryItem;
window.deleteChatHistoryItem = deleteChatHistoryItem;

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