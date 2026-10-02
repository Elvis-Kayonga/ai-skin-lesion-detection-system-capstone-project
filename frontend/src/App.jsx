import { useEffect, useState } from "react";
import * as api from "./api.js";
import Login from "./components/Login.jsx";
import Upload from "./components/Upload.jsx";
import ResultCard from "./components/ResultCard.jsx";
import History from "./components/History.jsx";
import Limitations from "./components/Limitations.jsx";

export default function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem("token"));
  const [result, setResult] = useState(null);
  const [original, setOriginal] = useState(null);
  const [cases, setCases] = useState([]);
  const [tab, setTab] = useState("screen");

  const logout = () => {
    sessionStorage.removeItem("token");
    setToken(null);
    setResult(null);
  };

  const refresh = () =>
    api.listCases(token).then(setCases).catch((e) => e.status === 401 && logout());

  useEffect(() => {
    if (token) refresh();
  }, [token]);

  if (!token)
    return (
      <>
        <Login
          onToken={(t) => {
            sessionStorage.setItem("token", t);
            setToken(t);
          }}
        />
        <Limitations />
      </>
    );

  const openCase = async (id) => {
    setOriginal(null);
    setResult(await api.getCase(token, id));
    setTab("screen");
  };

  return (
    <div className="app">
      <header>
        <h1>Skin Lesion Pre-Screening</h1>
        <nav>
          <button className={tab === "screen" ? "active" : ""} onClick={() => setTab("screen")}>
            Screen
          </button>
          <button className={tab === "history" ? "active" : ""} onClick={() => setTab("history")}>
            History
          </button>
          <button className={tab === "about" ? "active" : ""} onClick={() => setTab("about")}>
            Limitations
          </button>
          <button onClick={logout}>Log out</button>
        </nav>
      </header>

      {tab === "screen" && (
        <>
          <Upload
            token={token}
            onStart={() => setResult(null)}
            onResult={(r, preview) => {
              setResult(r);
              setOriginal(preview);
              refresh();
            }}
            onAuthError={logout}
          />
          {result && <ResultCard result={result} original={original} />}
        </>
      )}
      {tab === "history" && <History cases={cases} onOpen={openCase} />}
      {tab === "about" && <Limitations />}
      <footer>{api.DISCLAIMER}</footer>
    </div>
  );
}
