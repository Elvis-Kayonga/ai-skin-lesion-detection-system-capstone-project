import { useEffect, useState } from "react";
import * as api from "./api.js";
import Upload from "./components/Upload.jsx";
import ResultCard from "./components/ResultCard.jsx";
import History from "./components/History.jsx";
import Limitations from "./components/Limitations.jsx";

export default function App() {
  const [status, setStatus] = useState("loading"); // loading | ready | error
  const [bootError, setBootError] = useState("");
  const [result, setResult] = useState(null);
  const [original, setOriginal] = useState(null);
  const [cases, setCases] = useState([]);
  const [tab, setTab] = useState("screen");

  const refresh = () => api.listCases().then(setCases).catch(() => {});

  const boot = () => {
    setStatus("loading");
    api
      .ensureSession()
      .then(() => {
        setStatus("ready");
        refresh();
      })
      .catch((e) => {
        setBootError(e.message);
        setStatus("error");
      });
  };

  useEffect(boot, []);

  const openCase = async (id) => {
    setOriginal(null);
    setResult(await api.getCase(id));
    setTab("screen");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="shell">
      <div className="topbar" role="note">
        {api.DISCLAIMER} <button className="link" onClick={() => setTab("about")}>Read the limitations</button>
      </div>

      <header className="header">
        <div className="brand">
          <span className="logo" aria-hidden="true" />
          <div>
            <h1>Skin Lesion Pre-Screening</h1>
            <p className="muted small">Explainable, uncertainty-aware decision support</p>
          </div>
        </div>
        <nav className="tabs" aria-label="Main">
          {[["screen", "Screen"], ["history", "History"], ["about", "Limitations"]].map(([id, label]) => (
            <button key={id} className={tab === id ? "tab active" : "tab"} onClick={() => setTab(id)}>
              {label}
              {id === "history" && cases.length > 0 && <span className="count">{cases.length}</span>}
            </button>
          ))}
        </nav>
      </header>

      <main className="main">
        {status === "loading" && (
          <section className="card center"><span className="spinner dark" aria-hidden="true" /> Connecting to the screening server...</section>
        )}

        {status === "error" && (
          <section className="card center">
            <div className="notice error-box" role="alert">{bootError}</div>
            <button className="btn primary" onClick={boot}>Try again</button>
          </section>
        )}

        {status === "ready" && tab === "screen" && (
          <>
            <Upload
              onStart={() => setResult(null)}
              onResult={(r, preview) => {
                setResult(r);
                setOriginal(preview);
                refresh();
                setTimeout(() => document.querySelector(".result")?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
              }}
            />
            {result ? <ResultCard result={result} original={original} /> : <Limitations compact />}
          </>
        )}

        {status === "ready" && tab === "history" && <History cases={cases} onOpen={openCase} />}
        {tab === "about" && <Limitations />}
      </main>

      <footer className="footer">
        <strong>{api.DISCLAIMER}</strong>
        <span>Prototype for a university capstone. No real patient data.</span>
      </footer>
    </div>
  );
}
