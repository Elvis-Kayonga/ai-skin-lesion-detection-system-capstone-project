// Talks to the screening API. Everything network- and session-related lives here, so the React
// components only call methods like `api.predict(file)` and never deal with tokens or HTTP details.

export const NETWORK_ERROR = "Cannot reach the screening server. Check that the backend is running.";

/** An error from the API, carrying the HTTP status (0 when the server could not be reached). */
export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/** Remembers this browser's anonymous guest credentials. Storage failures (private mode) are ignored. */
export class SessionStore {
  constructor(storage = globalThis.localStorage, key = "skin_guest_session") {
    this.storage = storage;
    this.key = key;
  }

  load() {
    try { return JSON.parse(this.storage.getItem(this.key) || "null"); } catch { return null; }
  }

  save(credentials) {
    try { this.storage.setItem(this.key, JSON.stringify(credentials)); } catch { /* ignore */ }
  }
}

const randomId = () =>
  (globalThis.crypto?.randomUUID
    ? globalThis.crypto.randomUUID()
    : Math.random().toString(36).slice(2) + Date.now().toString(36)
  ).replace(/-/g, "");

/**
 * There is no login screen. The first visit silently creates a throwaway account whose random
 * credentials stay in this browser only, so each device keeps its own private case history.
 */
export class ApiClient {
  constructor(baseUrl, sessionStore, fetchImpl = (...args) => globalThis.fetch(...args), newId = randomId) {
    this.baseUrl = baseUrl;
    this.sessionStore = sessionStore;
    this.fetch = fetchImpl;
    this.newId = newId;
    this.token = null;
    this.pending = null;
  }

  // ---------- low level ----------
  async request(path, { token, ...options } = {}) {
    let res;
    try {
      res = await this.fetch(this.baseUrl + path, {
        ...options,
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(options.headers || {}) },
      });
    } catch {
      throw new ApiError(NETWORK_ERROR, 0);
    }
    if (!res.ok) {
      let message = `Request failed (${res.status})`;
      try {
        const body = await res.json();
        if (typeof body.detail === "string") message = body.detail;
      } catch { /* not JSON */ }
      throw new ApiError(message, res.status);
    }
    return res.json();
  }

  register(email, password) {
    return this.request("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
  }

  login(email, password) {
    return this.request("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username: email, password }),
    });
  }

  // ---------- anonymous session ----------
  async startSession() {
    const saved = this.sessionStore.load();
    if (saved) {
      try {
        this.token = (await this.login(saved.email, saved.password)).access_token;
        return;
      } catch (e) {
        if (e.status !== 401) throw e; // server problem: do not replace the saved account
      }
    }
    const credentials = { email: `guest-${this.newId()}@guest.local`, password: this.newId() + this.newId() };
    this.token = (await this.register(credentials.email, credentials.password)).access_token;
    this.sessionStore.save(credentials);
  }

  ensureSession() {
    if (this.token) return Promise.resolve();
    if (!this.pending) this.pending = this.startSession().finally(() => { this.pending = null; });
    return this.pending;
  }

  async authed(path, options = {}) {
    await this.ensureSession();
    try {
      return await this.request(path, { ...options, token: this.token });
    } catch (e) {
      if (e.status !== 401) throw e;
      this.token = null; // token expired or the database was reset: start a fresh session once
      await this.ensureSession();
      return this.request(path, { ...options, token: this.token });
    }
  }

  // ---------- screening ----------
  predict(file) {
    const form = new FormData();
    form.append("image", file);
    return this.authed("/predict", { method: "POST", body: form });
  }

  listCases() {
    return this.authed("/cases");
  }

  getCase(id) {
    return this.authed(`/cases/${id}`);
  }
}
