import { ApiClient, SessionStore } from "./ApiClient.js";

// The single client the whole app shares.
export const api = new ApiClient(import.meta.env.VITE_API_URL || "http://localhost:8000", new SessionStore());
