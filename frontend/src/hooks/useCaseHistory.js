import { useCallback, useEffect, useState } from "react";
import { api } from "../services/api.js";

/** The current browser's past cases. Loads once the session is ready; `refresh` reloads them. */
export function useCaseHistory(ready) {
  const [cases, setCases] = useState([]);

  const refresh = useCallback(() => api.listCases().then(setCases).catch(() => {}), []);

  useEffect(() => {
    if (ready) refresh();
  }, [ready, refresh]);

  return { cases, refresh };
}
