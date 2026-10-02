export default function History({ cases, onOpen }) {
  return (
    <section className="card">
      <div className="card-head">
        <h2>Case history</h2>
        <p className="muted">Kept for this browser only. Clearing your browser data removes the link to these cases.</p>
      </div>
      {!cases.length ? (
        <p className="empty">No cases yet. Analyse a photo and it will appear here.</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>#</th><th>Date</th><th>Most likely class</th><th>Entropy</th><th>Review</th><th></th></tr>
            </thead>
            <tbody>
              {cases.map((c) => (
                <tr key={c.case_id}>
                  <td>{c.case_id}</td>
                  <td>{new Date(c.created_at + "Z").toLocaleString()}</td>
                  <td>{c.class_name}</td>
                  <td>{c.entropy.toFixed(2)}</td>
                  <td>{c.review_recommended ? <span className="tag warn">Recommended</span> : <span className="tag">No</span>}</td>
                  <td><button className="btn small-btn" onClick={() => onOpen(c.case_id)}>View</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
