export const API_BASE = "http://localhost:8001/api/v1"; 

// Endpoints
export const ENDPOINTS = {
  REGISTER: "/signup",
  LOGIN: "/login",
  PROFILE: "/profile",
  VALIDATE: "/validate",
  REFRESH: "/refresh",
  LOGOUT: "/logout",
  CHAT: "/optimize-prompt"
};

// Storage keys (to avoid hardcoding everywhere)
export const STORAGE_KEYS = {
  TOKEN: "access_token",
  REFRESH_TOKEN: "refresh_token",
  USER_EMAIL: "user_email",
};

// Redirects
export const ROUTES = {
  CHATBOT: "/frontend",
  AUTH: "/auth",
  LOGIN: "/auth"
};
