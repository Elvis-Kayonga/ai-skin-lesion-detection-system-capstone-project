// Unit tests for ApiClient with a fake server and in-memory storage (no backend needed).
import { describe, expect, it } from "vitest";
import { ApiClient, ApiError, NETWORK_ERROR, SessionStore } from "./ApiClient.js";

class MemoryStorage {
  constructor() { this.data = {}; }
  getItem(k) { return k in this.data ? this.data[k] : null; }
  setItem(k, v) { this.data[k] = String(v); }
}

const json = (status, body) => ({ ok: status < 400, status, json: async () => body });

/** A tiny fake API: answers by path, records every call. */
function fakeServer(routes) {
  const calls = [];
  const fetchImpl = async (url, options = {}) => {
    const path = url.replace("http://api", "");
    calls.push({ path, options });
    const handler = routes[path];
    if (!handler) throw new TypeError("network down");
    return handler(options, calls);
  };
  return { fetchImpl, calls };
}

let counter = 0;
const newClient = (routes, storage = new MemoryStorage()) => {
  const server = fakeServer(routes);
  const client = new ApiClient("http://api", new SessionStore(storage), server.fetchImpl, () => `id${++counter}`);
  return { client, server, storage };
};

describe("ApiClient", () => {
  it("creates a guest account on first visit and remembers it", async () => {
    const { client, server, storage } = newClient({ "/auth/register": () => json(201, { access_token: "T1" }) });
    await client.ensureSession();
    expect(client.token).toBe("T1");
    expect(server.calls.map((c) => c.path)).toEqual(["/auth/register"]);
    const saved = JSON.parse(storage.getItem("skin_guest_session"));
    expect(saved.email).toMatch(/^guest-.+@guest\.local$/);
  });

  it("logs back in with the saved guest account on the next visit", async () => {
    const storage = new MemoryStorage();
    storage.setItem("skin_guest_session", JSON.stringify({ email: "guest-x@guest.local", password: "pw" }));
    const { client, server } = newClient({ "/auth/login": () => json(200, { access_token: "T2" }) }, storage);
    await client.ensureSession();
    expect(client.token).toBe("T2");
    expect(server.calls.map((c) => c.path)).toEqual(["/auth/login"]);
  });

  it("creates a new account if the saved one no longer exists (database reset)", async () => {
    const storage = new MemoryStorage();
    storage.setItem("skin_guest_session", JSON.stringify({ email: "old@guest.local", password: "pw" }));
    const { client, server } = newClient({
      "/auth/login": () => json(401, { detail: "Incorrect email or password." }),
      "/auth/register": () => json(201, { access_token: "T3" }),
    }, storage);
    await client.ensureSession();
    expect(client.token).toBe("T3");
    expect(server.calls.map((c) => c.path)).toEqual(["/auth/login", "/auth/register"]);
  });

  it("starts only one session even when several requests ask at once", async () => {
    const { client, server } = newClient({ "/auth/register": () => json(201, { access_token: "T" }) });
    await Promise.all([client.ensureSession(), client.ensureSession(), client.ensureSession()]);
    expect(server.calls.filter((c) => c.path === "/auth/register")).toHaveLength(1);
  });

  it("sends the token and, after a 401 (expired token), logs in again and retries once", async () => {
    let caseCalls = 0;
    const { client, server } = newClient({
      "/auth/register": () => json(201, { access_token: "T1" }),
      "/auth/login": () => json(200, { access_token: "T2" }),
      "/cases": () => (++caseCalls === 1 ? json(401, { detail: "Invalid or expired token" }) : json(200, [])),
    });
    expect(await client.listCases()).toEqual([]);
    expect(server.calls.map((c) => c.path)).toEqual(["/auth/register", "/cases", "/auth/login", "/cases"]);
    const caseRequests = server.calls.filter((c) => c.path === "/cases");
    expect(caseRequests.map((c) => c.options.headers.Authorization)).toEqual(["Bearer T1", "Bearer T2"]);
  });

  it("turns the server's error message into an ApiError with the status", async () => {
    const { client } = newClient({
      "/auth/register": () => json(201, { access_token: "T" }),
      "/predict": () => json(422, { detail: "Image looks too blurry (sharpness 0.8, needs at least 5.0)." }),
    });
    const err = await client.predict(new Blob(["x"])).catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(422);
    expect(err.message).toMatch(/too blurry/);
  });

  it("explains clearly when the server cannot be reached", async () => {
    const { client } = newClient({});
    const err = await client.ensureSession().catch((e) => e);
    expect(err.message).toBe(NETWORK_ERROR);
    expect(err.status).toBe(0);
  });

  it("keeps working when browser storage is blocked (private mode)", async () => {
    const blocked = { getItem() { throw new Error("blocked"); }, setItem() { throw new Error("blocked"); } };
    const { client } = newClient({ "/auth/register": () => json(201, { access_token: "T" }) }, blocked);
    await client.ensureSession();
    expect(client.token).toBe("T");
  });
});
