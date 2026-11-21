// The three possible next steps, in order of urgency. The result lights up the one that applies;
// the how-to guide shows the same scale so users learn it before their first result.
export const TRIAGE_STEPS = [
  { level: "urgent", label: "See a doctor" },
  { level: "check", label: "Not sure" },
  { level: "watch", label: "No warning signs" },
];

export default function TriageScale({ active }) {
  return (
    <ol className="triage" aria-label="Possible results">
      {TRIAGE_STEPS.map((s) => (
        <li key={s.level} className={`triage-step triage-${s.level} ${active === s.level ? "on" : ""}`}
          aria-current={active === s.level ? "step" : undefined}>
          <span className="triage-dot" aria-hidden="true" />
          {s.label}
        </li>
      ))}
    </ol>
  );
}
