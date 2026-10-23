export default function Limitations({ compact = false }) {
  return (
    <section className={`card limitations ${compact ? "compact" : ""}`}>
      <div className="card-head">
        <h2>{compact ? "Know the limits" : "About and limitations"}</h2>
      </div>
      <ul>
        <li><strong>Not a diagnosis.</strong> This is a pre-screening decision-support prototype. Always consult a qualified clinician.</li>
        <li><strong>Dataset bias.</strong> The model learned mostly from HAM10000, which comes mainly from lighter-skinned patients. It was then fine-tuned with only about 110 dark-skin photos and some benign dark-skin lesions.</li>
        <li><strong>Dark skin is not validated.</strong> On a small test of 29 dark-skin photos, accuracy rose from 28% to 83% after fine-tuning, but that sample is far too small to rely on. Do not assume it works on Black and dark skin (Fitzpatrick V to VI). Validation with local clinical photos is the main future work.</li>
        {!compact && (
          <>
            <li><strong>Dermoscope training images.</strong> The model learned from dermoscopic close-ups. Ordinary phone photos look different and are not validated.</li>
            <li><strong>Melanoma sensitivity is limited.</strong> On the HAM10000 held-out test set it was 70.5% for the top class and 93.8% when the review flag is counted. Some melanomas will be missed.</li>
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
