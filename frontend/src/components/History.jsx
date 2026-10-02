export default function History({ cases, onOpen }) {
  if (!cases.length) return <section className="card"><p>No cases yet.</p></section>;
  return (
    <section className="card">
      <h2>Case history</h2>
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>#</th><th>Date</th><th>Top class</th><th>Entropy</th><th>Review</th><th></th></tr>
          </thead>
          <tbody>
            {cases.map((c) => (
              <tr key={c.case_id}>
                <td>{c.case_id}</td>
                <td>{new Date(c.created_at + "Z").toLocaleString()}</td>
                <td>{c.class_name}</td>
                <td>{c.entropy.toFixed(2)}</td>
                <td>{c.review_recommended ? "Recommended" : "No"}</td>
                <td><button onClick={() => onOpen(c.case_id)}>View</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
