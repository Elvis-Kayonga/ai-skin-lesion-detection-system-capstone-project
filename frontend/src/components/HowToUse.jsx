import { useState } from "react";

const KEY = "howto-closed";

function initiallyOpen() {
  try {
    return localStorage.getItem(KEY) !== "1";
  } catch {
    return true;
  }
}

// A short guide for first-time users: how to take a good photo and what each result colour means.
// Open until the user closes it once; remembered per browser.
export default function HowToUse() {
  const [open, setOpen] = useState(initiallyOpen);

  const toggle = (e) => {
    const isOpen = e.currentTarget.open;
    setOpen(isOpen);
    try {
      localStorage.setItem(KEY, isOpen ? "0" : "1");
    } catch {
      /* private mode: just do not remember */
    }
  };

  return (
    <details className="howto" open={open} onToggle={toggle}>
      <summary>How to use this app (read this first)</summary>
      <ol className="howto-steps">
        <li>
          <strong>Take a clear photo.</strong> Tap <em>Take a photo</em>. On phones that allow it the flash turns on
          by itself. Hold the phone about 10 cm from the skin, keep it still, and put the spot in the middle of the
          circle. Or tap <em>Upload a photo</em> to use one you already have.
        </li>
        <li>
          <strong>Tap <em>Analyse image</em>.</strong> The answer takes a few seconds. If the photo is blurry or too
          small, the app asks you to take it again.
        </li>
        <li>
          <strong>Read the coloured box at the top of the result.</strong> It tells you what to do next:
          <ul className="howto-legend">
            <li><span className="dot dot-urgent" /> <strong>Red: see a doctor.</strong> The system found signs of a
              possible skin cancer. Refer the person to a doctor or skin specialist as soon as possible.</li>
            <li><span className="dot dot-check" /> <strong>Orange: not sure.</strong> The system cannot give a reliable
              answer. Retake the photo in better light. If it is still unsure, refer the person to a doctor.</li>
            <li><span className="dot dot-watch" /> <strong>Green: no warning signs found.</strong> This does not
              prove the skin is healthy. See a doctor if the spot grows, changes, bleeds, itches or hurts.</li>
          </ul>
        </li>
        <li>
          <strong>Look at the heatmap</strong> to see which part of the photo the system paid attention to. Every
          result is saved under <em>History</em> so you can show it to a doctor later.
        </li>
      </ol>
      <p className="muted small">
        This app helps you decide who should see a doctor. It does not diagnose and it does not replace a doctor.
      </p>
    </details>
  );
}
