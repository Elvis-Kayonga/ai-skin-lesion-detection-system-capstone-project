export default function Limitations({ compact = false }) {
  return (
    <section className={`card limitations ${compact ? "compact" : ""}`}>
      <div className="card-head">
        <h2>{compact ? "Know the limits" : "About and limitations"}</h2>
      </div>
      <ul>
        <li><strong>Not a diagnosis.</strong> This is a pre-screening decision-support prototype. Always consult a qualified clinician.</li>
        <li><strong>Dataset bias.</strong> The model is trained on HAM10000, which has no skin-tone labels and comes mostly from lighter-skinned patients.</li>
        <li><strong>No skin-tone validation.</strong> Performance on Black and dark skin (Fitzpatrick V to VI) has not been measured and must not be assumed. This is the main planned future work.</li>
        {!compact && (
          <>
            <li><strong>Dermoscope training images.</strong> The model learned from dermoscopic close-ups. Ordinary phone photos look different and are not validated.</li>
            <li><strong>Melanoma sensitivity is limited.</strong> On the held-out test set it was 57.5% for the top class and 87.7% when the review flag is counted. Some melanomas will be missed.</li>
            <li><strong>Overconfidence.</strong> The model can show close to 100% for one class even when it is wrong. The review flag is a better warning than the probability.</li>
            <li><strong>Uncertainty is random near the threshold.</strong> The same image can be flagged on one run and not on the next.</li>
            <li><strong>Image quality.</strong> Very small or severely blurry images are rejected, but mild blur or poor lighting can pass.</li>
          </>
        )}
        <li><strong>Prototype only.</strong> Do not upload photos of real patients.</li>
      </ul>
    </section>
  );
}
