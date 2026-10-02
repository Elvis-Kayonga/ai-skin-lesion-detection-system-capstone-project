import { useRef, useState } from "react";
import * as api from "../api.js";
import Camera from "./Camera.jsx";

export default function Upload({ onStart, onResult }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [mode, setMode] = useState("idle"); // idle | camera
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [drag, setDrag] = useState(false);
  const fileInput = useRef(null);
  const nativeCamera = useRef(null); // phone camera fallback when in-page camera is unavailable

  const pick = (f) => {
    setError("");
    onStart();
    if (preview) URL.revokeObjectURL(preview);
    setFile(f);
    setPreview(f ? URL.createObjectURL(f) : null);
    setMode("idle");
  };

  const run = async () => {
    setError("");
    onStart(); // hide any previous result so it is never shown next to a new image
    setBusy(true);
    try {
      onResult(await api.predict(file), preview);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDrag(false);
    const f = e.dataTransfer.files && e.dataTransfer.files[0];
    if (f) pick(f);
  };

  return (
    <section className="card">
      <div className="card-head">
        <h2>1. Add a photo of the lesion</h2>
        <p className="muted">Take a new photo or upload one. JPEG or PNG. Use only non-identifying test images.</p>
      </div>

      {mode === "camera" ? (
        <Camera
          onCapture={pick}
          onCancel={() => setMode("idle")}
          onUnavailable={() => {
            setMode("idle");
            nativeCamera.current && nativeCamera.current.click();
          }}
        />
      ) : (
        <>
          {!preview && (
            <div
              className={`dropzone ${drag ? "drag" : ""}`}
              onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
              onDragLeave={() => setDrag(false)}
              onDrop={onDrop}
            >
              <div className="drop-icon" aria-hidden="true">
                <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5" /><path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
                </svg>
              </div>
              <p><strong>Drag and drop a photo here</strong></p>
              <p className="muted small">or use one of the buttons below</p>
            </div>
          )}

          {preview && (
            <div className="preview-wrap">
              <img className="preview" src={preview} alt="Selected lesion preview" />
              <p className="muted small">{file && file.name}</p>
            </div>
          )}

          <div className="row">
            <button className="btn" onClick={() => setMode("camera")} disabled={busy}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M4 8h3l2-3h6l2 3h3a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z" /><circle cx="12" cy="13" r="3.5" /></svg>
              Take a photo
            </button>
            <button className="btn" onClick={() => fileInput.current.click()} disabled={busy}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5" /><path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" /></svg>
              {preview ? "Choose a different photo" : "Upload a photo"}
            </button>
          </div>

          <input
            ref={fileInput}
            type="file"
            accept="image/jpeg,image/png"
            hidden
            onChange={(e) => { pick(e.target.files[0] || null); e.target.value = ""; }}
          />
          <input
            ref={nativeCamera}
            type="file"
            accept="image/*"
            capture="environment"
            hidden
            onChange={(e) => { pick(e.target.files[0] || null); e.target.value = ""; }}
          />
        </>
      )}

      {error && <div className="notice error-box" role="alert">{error}</div>}

      {mode !== "camera" && (
        <button className="btn primary big" disabled={!file || busy} onClick={run}>
          {busy ? (<><span className="spinner" aria-hidden="true" /> Analysing...</>) : "2. Analyse image"}
        </button>
      )}
    </section>
  );
}
