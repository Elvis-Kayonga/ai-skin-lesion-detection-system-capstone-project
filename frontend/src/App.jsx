import { useState } from "react";
import { DISCLAIMER } from "./constants.js";
import { api } from "./services/api.js";
import { useSession } from "./hooks/useSession.js";
import { useCaseHistory } from "./hooks/useCaseHistory.js";
import Upload from "./components/Upload.jsx";
import ResultCard from "./components/ResultCard.jsx";
import History from "./components/History.jsx";
import Limitations from "./components/Limitations.jsx";
import HowToUse from "./components/HowToUse.jsx";
import ResultPlaceholder from "./components/ResultPlaceholder.jsx";

const TABS = [["screen", "Screen"], ["history", "History"], ["about", "Limitations"]];

export default function App() {
  const session = useSession();
  const { cases, refresh } = useCaseHistory(session.status === "ready");
  const [result, setResult] = useState(null);
  const [original, setOriginal] = useState(null);
  const [tab, setTab] = useState("screen");

  const openCase = async (id) => {
    setOriginal(null);
    setResult(await api.getCase(id));
    setTab("screen");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const showResult = (r, preview) => {
    setResult(r);
    setOriginal(preview);
    refresh();
    setTimeout(() => document.querySelector(".result")?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
  };

  return (
    <div className="shell">
      <div className="topbar" role="note">
        {DISCLAIMER} <button className="link" onClick={() => setTab("about")}>Read the limitations</button>
      </div>

      <header className="header">
        <div className="header-inner">
          <div className="brand">
            <span className="logo" aria-hidden="true">
              <svg viewBox="0 0 32 32" width="32" height="32">
                <circle cx="16" cy="16" r="13" fill="none" stroke="currentColor" strokeWidth="2.5" />
                <circle cx="16" cy="16" r="5.5" fill="currentColor" />
              </svg>
            </span>
            <div>
              <h1>Skin Lesion Pre-Screening</h1>
              <p className="brand-sub">Check a skin spot and decide who should see a doctor</p>
            </div>
          </div>
          <nav className="tabs" aria-label="Main">
            {TABS.map(([id, label]) => (
              <button key={id} className={tab === id ? "tab active" : "tab"} onClick={() => setTab(id)}
                aria-current={tab === id ? "page" : undefined}>
                {label}
                {id === "history" && cases.length > 0 && <span className="count">{cases.length}</span>}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="main">
        {session.status === "loading" && (
          <section className="card center"><span className="spinner dark" aria-hidden="true" /> Connecting to the screening server...</section>
        )}

        {session.status === "error" && (
          <section className="card center">
            <div className="notice error-box" role="alert">{session.error}</div>
            <button className="btn primary" onClick={session.retry}>Try again</button>
          </section>
        )}

        {session.status === "ready" && tab === "screen" && (
          <>
            <HowToUse />
            <div className="workspace">
              <Upload onStart={() => setResult(null)} onResult={showResult} />
              {result ? <ResultCard result={result} original={original} /> : <ResultPlaceholder />}
            </div>
          </>
        )}

        {session.status === "ready" && tab === "history" && <History cases={cases} onOpen={openCase} />}
        {tab === "about" && <Limitations />}
      </main>

      <footer className="footer">
        <strong>{DISCLAIMER}</strong>
        <span>Prototype for a university capstone. No real patient data.</span>
      </footer>
    </div>
  );
}
