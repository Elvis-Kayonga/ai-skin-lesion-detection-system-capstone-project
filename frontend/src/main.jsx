import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
// Atkinson Hyperlegible (Braille Institute) is designed to stay readable for people with low vision, which
// suits health workers reading on small phone screens. Bundled with the app, so it works offline and in Docker.
import "@fontsource-variable/atkinson-hyperlegible-next";
import "@fontsource-variable/atkinson-hyperlegible-next/wght-italic.css";
import "./styles.css";

createRoot(document.getElementById("root")).render(<App />);
