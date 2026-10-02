import { useState } from "react";
import * as api from "../api.js";

export default function Login({ onToken }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const fn = mode === "login" ? api.login : api.register;
      onToken((await fn(email, password)).access_token);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card narrow">
      <h1>Skin Lesion Pre-Screening</h1>
      <p className="muted">{api.DISCLAIMER}</p>
      <form onSubmit={submit}>
        <label>Email<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
        <label>Password<input type="password" minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
        {error && <p className="error">{error}</p>}
        <button className="primary" disabled={busy}>{mode === "login" ? "Log in" : "Create account"}</button>
      </form>
      <button className="link" onClick={() => setMode(mode === "login" ? "register" : "login")}>
        {mode === "login" ? "No account? Register" : "Have an account? Log in"}
      </button>
    </div>
  );
}
