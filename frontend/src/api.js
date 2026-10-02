const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const DISCLAIMER =
  "Decision-support prototype only. Not a diagnosis. Consult a qualified clinician.";

async function request(path, { token, ...opts } = {}) {
  const res = await fetch(BASE + path, {
    ...opts,
    headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(opts.headers || {}) },
  });
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

export const register = (email, password) =>
  request("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

export const login = (email, password) =>
  request("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: email, password }),
  });

export const predict = (token, file) => {
  const form = new FormData();
  form.append("image", file);
  return request("/predict", { method: "POST", token, body: form });
};

export const listCases = (token) => request("/cases", { token });
export const getCase = (token, id) => request(`/cases/${id}`, { token });
