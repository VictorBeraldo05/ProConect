// src/services/apiClient.js
// Configure sempre VITE_API_BASE para apontar ao backend (ex.: https://proconect.pythonanywhere.com)
const API_BASE = import.meta.env.VITE_API_BASE;
if (!API_BASE) {
  throw new Error("VITE_API_BASE não definido. Configure no .env/.env.production o endpoint do backend.");
}

function getAccessToken() {
  return localStorage.getItem("access_token") || null;
}

function setTokens(access, refresh) {
  if (access) localStorage.setItem("access_token", access);
  if (refresh) localStorage.setItem("refresh_token", refresh);
}

export async function apiFetch(path, opts = {}) {
  const headers = new Headers(opts.headers || {});
  if (!headers.has("Content-Type") && opts.body) {
    headers.set("Content-Type", "application/json");
  }
  const token = getAccessToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
  const isJson = (res.headers.get("content-type") || "").includes("application/json");
  const data = isJson ? await res.json() : await res.text();
  if (!res.ok) {
    const msg = isJson ? (data?.error || JSON.stringify(data)) : data;
    throw new Error(msg || `Erro HTTP ${res.status}`);
  }
  return data;
}

export async function loginApi(email, password) {
  const data = await apiFetch(`/api/auth/login`, {
    method: "POST",
    body: JSON.stringify({ email, password })
  });
  // data: { access_token, refresh_token, user, profile }
  setTokens(data.access_token, data.refresh_token);
  return data;
}

export async function registerApi(payload) {
  // payload: { nome, email, password, is_worker?, perfil_worker?, preferencias? }
  const data = await apiFetch(`/api/auth/register`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
  return data; // { user, profile }
}

export async function meApi() {
  return apiFetch(`/api/auth/me`, { method: "GET" });
}

export function clearSession() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

export { API_BASE };

export async function updateMeApi(payload) {
  return apiFetch(`/api/users/me`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function saveOnboardingApi(payload) {
  return apiFetch(`/api/users/me/onboarding`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function uploadProfilePhotoApi(file) {
  const token = getAccessToken();
  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/api/users/me/foto`, {
    method: "POST",
    headers,
    body: form,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.error || "Falha no upload");
  return data; // { foto_url, profile }
}
