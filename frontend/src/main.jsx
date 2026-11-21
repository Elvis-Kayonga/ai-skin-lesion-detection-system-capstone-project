import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
// Inter is bundled with the app (no request to Google Fonts), so it also works offline and in Docker.
import "@fontsource-variable/inter";
import "./styles.css";

createRoot(document.getElementById("root")).render(<App />);
