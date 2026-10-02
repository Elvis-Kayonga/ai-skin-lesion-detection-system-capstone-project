import { DISCLAIMER } from "../api.js";

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

  return (
    <section className="card result">
      {result.review_recommended && (
        <div className="banner" role="alert">
          <strong>Review recommended.</strong> {result.review_reason}
        </div>
      )}
      <h2>Top class: {result.class_name}</h2>
      <p>
        Uncertainty: <span className={`badge ${level.toLowerCase()}`}>{level}</span>{" "}
        <span className="muted">
          (entropy {result.entropy.toFixed(2)}, review threshold {result.entropy_threshold.toFixed(2)})
        </span>
      </p>

      <div className="bars">
        {rows.map(([code, p]) => (
          <div key={code} className="bar-row">
            <span className="bar-label">{code}</span>
            <div className="bar"><div style={{ width: `${(p * 100).toFixed(1)}%` }} /></div>
            <span className="bar-val">{(p * 100).toFixed(1)}%</span>
          </div>
        ))}
      </div>

      <div className="side-by-side">
        {original && (
          <figure><img src={original} alt="Original" /><figcaption>Original</figcaption></figure>
        )}
        <figure>
          <img src={`data:image/png;base64,${result.heatmap_base64}`} alt="Grad-CAM heatmap overlay" />
          <figcaption>Grad-CAM: regions that influenced the model</figcaption>
        </figure>
      </div>

      <p className="muted small">
        Case #{result.case_id} · model {result.model_version} · {result.inference_ms} ms
      </p>
      <p className="disclaimer">{result.disclaimer || DISCLAIMER}</p>
    </section>
  );
}
