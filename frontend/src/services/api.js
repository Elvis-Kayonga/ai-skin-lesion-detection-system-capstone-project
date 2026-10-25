import { ApiClient, SessionStore } from "./ApiClient.js";

// Where the API lives. "same-origin" means the API serves this web app itself (the online demo),
// so requests go to the same address the page was loaded from.
const configured = import.meta.env.VITE_API_URL || "http://localhost:8000";
const baseUrl = configured === "same-origin" ? "" : configured;

// The single client the whole app shares.
export const api = new ApiClient(baseUrl, new SessionStore());
