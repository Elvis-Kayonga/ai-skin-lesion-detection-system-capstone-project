import TriageScale from "./TriageScale.jsx";

// Shown in the result panel before the first analysis, so the layout does not jump and the user
// can see what kind of answer to expect.
export default function ResultPlaceholder() {
  return (
    <section className="panel result-empty" aria-label="Result">
      <h2>Result</h2>
      <p className="muted">Add a photo and tap <em>Analyse image</em>. The result shows one of these next steps:</p>
      <TriageScale />
      <p className="muted small">You will also see the photo, a heatmap of where the system looked, and how sure it is.</p>
    </section>
  );
}
