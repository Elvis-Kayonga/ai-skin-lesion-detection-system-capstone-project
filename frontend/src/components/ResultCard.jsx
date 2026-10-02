import { DISCLAIMER } from "../api.js";

const NAMES = {
  akiec: "Actinic keratoses",
  bcc: "Basal cell carcinoma",
  bkl: "Benign keratosis-like",
  df: "Dermatofibroma",
  mel: "Melanoma",
  nv: "Melanocytic nevi",
  vasc: "Vascular lesions",
};

// The badge uses the same entropy threshold as the server's review flag (from model_config.json),
// so the badge and the "Review recommended" banner can never disagree:
// High = at or above the threshold, Medium = above half of it, Low = below that.
function uncertaintyLevel(entropy, threshold) {
  if (entropy >= threshold) return "High";
  if (entropy >= threshold / 2) return "Medium";
  return "Low";
}

export default function ResultCard({ result, original }) {
  const level = uncertaintyLevel(result.entropy, result.entropy_threshold);
  const rows = Object.entries(result.probabilities).sort((a, b) => b[1] - a[1]);
  // Meter runs from 0 to 2x the review threshold; the marker sits at the threshold.
  const meterMax = result.entropy_threshold * 2;
  const meterPct = Math.min(result.entropy / meterMax, 1) * 100;

  return (
    <section className="card result" aria-live="polite">
      <div className="card-head">
        <h2>Result</h2>
      </div>

      {result.review_recommended && (
        <div className="notice warn" role="alert">
          <strong>Review recommended.</strong> {result.review_reason}
        </div>
      )}

      <div className="summary">
        <div>
          <div className="eyebrow">Most likely class</div>
          <div className="top-class">{result.class_name}</div>
        </div>
        <div className={`pill ${level.toLowerCase()}`}>{level} uncertainty</div>
      </div>

      <div className="meter" aria-hidden="true">
        <div className="meter-fill" style={{ width: `${meterPct}%` }} />
        <div className="meter-mark" style={{ left: "50%" }} />
      </div>
      <div className="meter-legend muted small">
        <span>Certain</span>
        <span>Unsure</span>
      </div>
      <p className="muted small meter-note">
        Entropy {result.entropy.toFixed(2)}. The review threshold (the line in the middle) is {result.entropy_threshold.toFixed(2)}.
      </p>

      <h3>Probability for each class</h3>
      <div className="bars">
        {rows.map(([code, p], i) => (
          <div key={code} className={`bar-row ${i === 0 ? "top" : ""}`}>
            <span className="bar-label">{NAMES[code] || code}</span>
            <div className="bar"><div style={{ width: `${(p * 100).toFixed(1)}%` }} /></div>
            <span className="bar-val">{(p * 100).toFixed(1)}%</span>
          </div>
        ))}
      </div>

      <h3>What the model looked at</h3>
      <div className="side-by-side">
        {original && (
          <figure><img src={original} alt="Your original photo" /><figcaption>Your photo, resized the way the model sees it</figcaption></figure>
        )}
        <figure>
          <img src={`data:image/png;base64,${result.heatmap_base64}`} alt="Grad-CAM heatmap overlay" />
          <figcaption>Heatmap: warmer colours influenced the result more</figcaption>
        </figure>
      </div>
      <p className="muted small">
        The heatmap explains where the model looked. It does not prove the result is correct.
      </p>

      <p className="meta">
        Case #{result.case_id} &middot; model {result.model_version} &middot; {result.inference_ms} ms
      </p>
      <div className="disclaimer">{result.disclaimer || DISCLAIMER}</div>
    </section>
  );
}
