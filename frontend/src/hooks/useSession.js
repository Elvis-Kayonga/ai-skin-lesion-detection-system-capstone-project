import { useCallback, useEffect, useState } from "react";
import { api } from "../services/api.js";

/** Starts the anonymous session on first load. Returns its status and a retry function. */
export function useSession() {
  const [status, setStatus] = useState("loading"); // loading | ready | error
  const [error, setError] = useState("");

  const start = useCallback(() => {
    setStatus("loading");
    api.ensureSession()
      .then(() => setStatus("ready"))
      .catch((e) => {
        setError(e.message);
        setStatus("error");
      });
  }, []);

  useEffect(start, [start]);
  return { status, error, retry: start };
}
