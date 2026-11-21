import { useEffect, useRef, useState } from "react";

function cameraMessage(e) {
  if (e && (e.name === "NotAllowedError" || e.name === "SecurityError"))
    return "Camera access was blocked. Allow the camera in your browser settings, or upload a photo instead.";
  if (e && (e.name === "NotFoundError" || e.name === "OverconstrainedError"))
    return "No camera was found on this device. Upload a photo instead.";
  return "The camera could not be started. Upload a photo instead.";
}

// The cropped photo is scaled down to at most this size; the model works at a few hundred pixels anyway.
const MAX_OUTPUT_PX = 1024;

export default function Camera({ onCapture, onCancel, onUnavailable }) {
  const videoRef = useRef(null);
  const frameRef = useRef(null);
  const guideRef = useRef(null);
  const streamRef = useRef(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  const [facing, setFacing] = useState("environment");
  // Flash ("torch"): browsers only allow a page to switch it on in some cases (Chrome on Android with the
  // back camera). Elsewhere (iPhone, laptops) the button is hidden and the hint asks for bright light.
  const [torchSupported, setTorchSupported] = useState(false);
  const [torchOn, setTorchOn] = useState(false);

  const setTorch = async (on) => {
    const track = streamRef.current && streamRef.current.getVideoTracks()[0];
    if (!track) return false;
    try {
      await track.applyConstraints({ advanced: [{ torch: on }] });
      setTorchOn(on);
      return true;
    } catch {
      return false;
    }
  };

  const stop = () => {
    if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  };

  useEffect(() => {
    let cancelled = false;
    setReady(false);
    setError("");
    setTorchSupported(false);
    setTorchOn(false);
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
        // Turn the flash on by default when this device lets the browser control it.
        const track = stream.getVideoTracks()[0];
        const caps = track && typeof track.getCapabilities === "function" ? track.getCapabilities() : {};
        if (caps && caps.torch) {
          setTorchSupported(true);
          try {
            await track.applyConstraints({ advanced: [{ torch: true }] });
            if (!cancelled) setTorchOn(true);
          } catch {
            /* flash refused: keep going without it */
          }
        }
      } catch (e) {
        if (!cancelled) setError(cameraMessage(e));
      }
    })();
    return () => {
      cancelled = true;
      stop();
    };
  }, [facing]);

  // Send only what is inside the guide circle. The camera sees more than the screen shows (the video is
  // scaled to cover the frame and the overflow is hidden), so we map the circle's on-screen box back to
  // the camera's own pixels and crop that square. Anything outside the circle never reaches the model.
  const guideCrop = (v) => {
    const frame = frameRef.current;
    const guide = guideRef.current;
    const vw = v.videoWidth;
    const vh = v.videoHeight;
    if (!frame || !guide) return null;
    const f = frame.getBoundingClientRect();
    const g = guide.getBoundingClientRect();
    if (!f.width || !g.width) return null;
    // object-fit: cover -> one scale for both axes, video centred, the excess cut off.
    const scale = Math.max(f.width / vw, f.height / vh);
    const offX = (f.width - vw * scale) / 2;
    const offY = (f.height - vh * scale) / 2;
    let sx = (g.left - f.left - offX) / scale;
    let sy = (g.top - f.top - offY) / scale;
    let side = Math.min(g.width, g.height) / scale;
    // Keep the square inside the camera image.
    side = Math.min(side, vw, vh);
    sx = Math.max(0, Math.min(sx, vw - side));
    sy = Math.max(0, Math.min(sy, vh - side));
    return { sx, sy, side };
  };

  const capture = () => {
    const v = videoRef.current;
    if (!v || !v.videoWidth) return;
    const crop = guideCrop(v) || {
      // Fallback (should not happen): a centred square.
      side: Math.min(v.videoWidth, v.videoHeight),
      sx: (v.videoWidth - Math.min(v.videoWidth, v.videoHeight)) / 2,
      sy: (v.videoHeight - Math.min(v.videoWidth, v.videoHeight)) / 2,
    };
    const out = Math.round(Math.min(crop.side, MAX_OUTPUT_PX));
    const canvas = document.createElement("canvas");
    canvas.width = out;
    canvas.height = out;
    canvas.getContext("2d").drawImage(v, crop.sx, crop.sy, crop.side, crop.side, 0, 0, out, out);
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
        <div className="camera-frame" ref={frameRef}>
          <video ref={videoRef} playsInline muted />
          {!ready && <div className="camera-loading">Starting camera...</div>}
          <div className="camera-guide" ref={guideRef} aria-hidden="true" />
        </div>
      )}
      <p className="hint">
        {torchSupported
          ? "The flash helps the system see the skin clearly. "
          : "This browser cannot turn on the flash, so use bright light (daylight near a window works well). "}
        Hold steady about 10 cm from the skin and centre the spot inside the circle. Only the area inside the
        circle is sent for analysis.
      </p>
      <div className="row">
        {!error && (
          <button className="btn primary" onClick={capture} disabled={!ready}>Capture photo</button>
        )}
        {!error && torchSupported && (
          <button className="btn" onClick={() => setTorch(!torchOn)} aria-pressed={torchOn}>
            {torchOn ? "Flash: on" : "Flash: off"}
          </button>
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
