const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const DISCLAIMER =
  "Decision-support prototype only. Not a diagnosis. Consult a qualified clinician.";

async function request(path, { token, ...opts } = {}) {
  let res;
  try {
    res = await fetch(BASE + path, {
      ...opts,
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(opts.headers || {}) },
    });
  } catch {
    throw new Error("Cannot reach the screening server. Check that the backend is running.");
  }
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") msg = body.detail;
    } catch {}
    const err = new Error(msg);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

const register = (email, password) =>
  request("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

const login = (email, password) =>
  request("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: email, password }),
  });

// ---- Anonymous per-browser session -------------------------------------------------
// There is no login screen. The first visit silently creates a throwaway account whose
// random credentials live in this browser only, so each device keeps its own private history.
const KEY = "skin_guest_session";
let token = null;
let pending = null;

const rand = () =>
  (crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2) + Date.now().toString(36)).replace(/-/g, "");

const store = {
  get() {
    try { return JSON.parse(localStorage.getItem(KEY) || "null"); } catch { return null; }
  },
  set(v) {
    try { localStorage.setItem(KEY, JSON.stringify(v)); } catch {}
  },
};

async function startSession() {
  const saved = store.get();
  if (saved) {
    try {
      token = (await login(saved.email, saved.password)).access_token;
      return;
    } catch (e) {
      if (e.status !== 401) throw e; // server problem: do not create a new account
    }
  }
  const creds = { email: `guest-${rand()}@guest.local`, password: rand() + rand() };
  token = (await register(creds.email, creds.password)).access_token;
  store.set(creds);
}

export function ensureSession() {
  if (token) return Promise.resolve();
  if (!pending) pending = startSession().finally(() => { pending = null; });
  return pending;
}

async function authed(path, opts = {}) {
  await ensureSession();
  try {
    return await request(path, { ...opts, token });
  } catch (e) {
    if (e.status !== 401) throw e;
    token = null; // token expired or database was reset: start a fresh session once
    await ensureSession();
    return request(path, { ...opts, token });
  }
}

export const predict = (file) => {
  const form = new FormData();
  form.append("image", file);
  return authed("/predict", { method: "POST", body: form });
};

export const listCases = () => authed("/cases");
export const getCase = (id) => authed(`/cases/${id}`);
