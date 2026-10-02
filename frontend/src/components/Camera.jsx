import { useEffect, useRef, useState } from "react";

function cameraMessage(e) {
  if (e && (e.name === "NotAllowedError" || e.name === "SecurityError"))
    return "Camera access was blocked. Allow the camera in your browser settings, or upload a photo instead.";
  if (e && (e.name === "NotFoundError" || e.name === "OverconstrainedError"))
    return "No camera was found on this device. Upload a photo instead.";
  return "The camera could not be started. Upload a photo instead.";
}

export default function Camera({ onCapture, onCancel, onUnavailable }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  const [facing, setFacing] = useState("environment");

  const stop = () => {
    if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  };

  useEffect(() => {
    let cancelled = false;
    setReady(false);
    setError("");
    (async () => {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        onUnavailable();
        return;
      }
      try {
        stop();
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: facing }, width: { ideal: 1920 }, height: { ideal: 1080 } },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        videoRef.current.srcObject = stream;
        await videoRef.current.play().catch(() => {});
        setReady(true);
      } catch (e) {
        if (!cancelled) setError(cameraMessage(e));
      }
    })();
    return () => {
      cancelled = true;
      stop();
    };
  }, [facing]);

  const capture = () => {
    const v = videoRef.current;
    if (!v || !v.videoWidth) return;
    const canvas = document.createElement("canvas");
    canvas.width = v.videoWidth;
    canvas.height = v.videoHeight;
    canvas.getContext("2d").drawImage(v, 0, 0);
    canvas.toBlob(
      (blob) => blob && onCapture(new File([blob], `camera-${Date.now()}.jpg`, { type: "image/jpeg" })),
      "image/jpeg",
      0.92
    );
  };

  return (
    <div className="camera">
      {error ? (
        <div className="notice error-box" role="alert">{error}</div>
      ) : (
        <div className="camera-frame">
          <video ref={videoRef} playsInline muted />
          {!ready && <div className="camera-loading">Starting camera...</div>}
          <div className="camera-guide" aria-hidden="true" />
        </div>
      )}
      <p className="hint">Hold steady, use good light and centre the lesion inside the circle. Fill most of the frame.</p>
      <div className="row">
        {!error && (
          <button className="btn primary" onClick={capture} disabled={!ready}>Capture photo</button>
        )}
        {!error && (
          <button className="btn" onClick={() => setFacing(facing === "environment" ? "user" : "environment")}>
            Switch camera
          </button>
        )}
        <button className="btn ghost" onClick={onCancel}>Cancel</button>
      </div>
    </div>
  );
}
