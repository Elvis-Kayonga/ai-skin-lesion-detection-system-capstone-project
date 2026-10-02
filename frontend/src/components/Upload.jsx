import { useState } from "react";
import * as api from "../api.js";

export default function Upload({ token, onStart, onResult, onAuthError }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const pick = (f) => {
    setError("");
    onStart();
    setFile(f);
    setPreview(f ? URL.createObjectURL(f) : null);
  };

  const run = async () => {
    setError("");
    onStart(); // hide any previous result so it is never shown next to a new image
    setBusy(true);
    try {
      onResult(await api.predict(token, file), preview);
    } catch (e) {
      if (e.status === 401) return onAuthError();
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="card">
      <h2>Upload a lesion photo</h2>
      <p className="muted">JPEG or PNG, in focus, well lit, lesion centred. Use only non-identifying test images.</p>
      <input type="file" accept="image/jpeg,image/png" onChange={(e) => pick(e.target.files[0] || null)} />
      {preview && <img className="preview" src={preview} alt="Selected upload preview" />}
      {error && <p className="error" role="alert">{error}</p>}
      <button className="primary" disabled={!file || busy} onClick={run}>
        {busy ? "Analysing…" : "Analyse image"}
      </button>
    </section>
  );
}
