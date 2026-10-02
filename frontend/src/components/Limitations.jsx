export default function Limitations() {
  return (
    <section className="card limitations">
      <h2>About / Limitations</h2>
      <ul>
        <li><strong>Not a diagnosis.</strong> This is a pre-screening decision-support prototype. Always consult a qualified clinician.</li>
        <li><strong>Dataset bias.</strong> The model is trained on HAM10000, which has no skin-tone labels and comes mostly from lighter-skinned patients.</li>
        <li><strong>No skin-tone validation.</strong> Performance on Black / dark skin (Fitzpatrick V–VI) has not been measured and must not be assumed. This is the main planned future work.</li>
        <li><strong>Uncertainty.</strong> Unfamiliar or ambiguous images are flagged with “Review recommended”, but a missing flag does not mean a lesion is safe.</li>
        <li><strong>Image quality.</strong> Blurry or very small images are rejected. Prototype only: do not upload real patient data.</li>
      </ul>
    </section>
  );
}
