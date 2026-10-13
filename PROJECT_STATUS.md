# PROJECT STATUS (living document for AI coding assistants)

Last updated: 2026-10-13 | Updated by: AI assistant (synced with GitHub, demo video link added) | Git: main at 937e5c1 on GitHub; local has uncommitted README fix + this file

---

## 0. RULES FOR ANY AI ASSISTANT (read this first, every session)

You are helping Kayonga Elvis (the only author and contributor) build this project. This file is the single source of truth for where the project is. Follow these rules every time.

**Before you code**
1. Read this whole file. If it conflicts with older notes or your memory, this file wins.
2. Run `git status` and `git log --oneline -n 5` and compare with the "Git" line above. If they differ, someone changed things since the last update: tell the user and refresh sections 3 to 6 before continuing.

**After every change you make (this is mandatory, not optional)**
1. Update the "Last updated" line at the top (date, who, git state).
2. Add an entry at the TOP of the Changelog (section 9): date, what changed, which files, how you verified it.
3. Update section 3 (status table), section 6 (known issues) and section 7 (open tasks): tick off what is done, add what you discovered.
4. If you made a design choice, add it to section 8 (decisions) with the reason.
5. If the change affects the UI or API, also update `README.md`, and retake affected screenshots in `docs/screenshots/`.
6. Mention in your final message that you updated this file.

**If you cannot edit files (for example a web chat)**
End every answer with a block titled `STATUS UPDATE` containing the exact text to paste into sections 3, 6, 7 and 9. The user will paste it in.

**Hard rules for this project (never break)**
1. This is decision support and pre-screening, NOT diagnosis. Never write text, UI copy, comments or docs that say it diagnoses or detects cancer. Every result screen shows: "Decision-support prototype only. Not a diagnosis. Consult a qualified clinician."
2. Never invent metrics. Numbers come only from the real Colab run (`backend/model/model_config.json`, `docs/results/*.csv`). If a number is missing, leave a clearly marked placeholder.
3. Never claim it works on dark skin (Fitzpatrick V to VI). HAM10000 has no skin-tone labels and is mostly lighter-skinned patients. Dark-skin performance is unmeasured and is the main future work.
4. Keep scope small: an MVP for a supervisor demo.
5. No real patient data. No secrets in Git (`.env`, `kaggle.json`, tokens, passwords). Passwords are hashed.
6. Ask before changing the model contract (section 4).
7. Do not add any AI tool as author, co-author or credit in commits, PRs, README or file headers. The user must be the only visible contributor. Write plain commit messages with no trailers.
8. Never `git push` without the user's explicit "push" in that message. Never store or echo a token the user pastes. Remind them to revoke it.
9. Writing style for README and docs: plain English, ASCII only, no em dashes, no emojis.

**Practical lessons from earlier sessions**
- Windows. Use PowerShell for git and npm. Do not kill processes by name (`Stop-Process -Name python`); kill by PID or by listening port only.
- AI terminals cannot show login prompts, so `git push` fails there. The user pushes from their own terminal, or gives a one-off token (use it via a temporary header only, never save it).
- Always test with REAL HAM10000 images, not synthetic ones. Synthetic test images hid a bad blur threshold earlier.
- The model uses random dropout, so the same image can give slightly different results and can flip across the review threshold.
- The user keeps a local AI instruction file on their disk that points to this document. It is excluded from Git through `.git/info/exclude`. Never commit it, and never mention AI tool names in tracked files.

---

## 1. Goal

**Product:** an explainable, uncertainty-aware AI-assisted skin lesion pre-screening prototype for low-resource settings in Rwanda, where dermatologists are scarce.

**User's personal goal:** that this works fairly for people with Black or dark skin (Fitzpatrick V to VI). Today this is NOT achieved or measured. It is stated honestly as the main future work.

**Current assignment (ML track, capstone):** deliver an initial MVP with: a notebook (data visualization and engineering, model architecture, initial metrics), a deployment mockup/MVP (web interface and Swagger UI), a README (description, repo link, setup, designs/screenshots, deployment plan), a 5 to 10 minute demo video, and a zip of the GitHub repo.

**Repo:** https://github.com/Elvis-Kayonga/ai-skin-lesion-detection-system-capstone-project (branch `main`)

**Immediate goal (next):** finish submission items (section 7, priority A), then host: React frontend on Vercel and the API on a separate host.

---

## 2. Stack and file map

Python 3.10+, PyTorch/torchvision (EfficientNet-B3 proposed, MobileNetV2 baseline), pytorch-grad-cam, FastAPI, SQLite via SQLAlchemy (PostgreSQL via Docker Compose is the documented production path), React 18 with Vite 5.

```
README.md                 Public README (setup, results, screenshots, deployment plan, limitations)
PROJECT_STATUS.md         This file
docker-compose.yml        PostgreSQL + API + web (validated, NOT yet run)
.env.example              For docker compose: SECRET_KEY, POSTGRES_PASSWORD
backend/
  app/main.py             Routes, startup check (SECRET_KEY >= 32 chars), CORS
  app/config.py           Settings (env-driven): upload limits, blur threshold, paths, CORS_ORIGINS
  app/ml.py               Model load, MC Dropout inference, review flag, Grad-CAM
  app/quality.py          Upload validation: type, size, resolution, blur
  app/security.py         Password hashing (bcrypt), JWT, current_user
  app/models.py           SQLAlchemy tables
  app/schemas.py          Pydantic response models
  app/db.py               Engine and session
  model/                  efficientnet_b3_best.pth (41 MB, committed) + model_config.json
  storage/                Saved uploads and heatmaps (gitignored, runtime only)
  Dockerfile, .env.example, requirements.txt
frontend/
  src/App.jsx             Layout, tabs (Screen, History, Limitations), boot/session
  src/api.js              API client + anonymous per-browser session (no login screen)
  src/components/         Upload.jsx, Camera.jsx, ResultCard.jsx, History.jsx, Limitations.jsx
  src/styles.css          Design (teal theme, responsive)
  Dockerfile, package.json
notebooks/skin_lesion_training.ipynb   Colab notebook (clean copy, NO outputs yet)
docs/figures/             Charts from the real run
docs/results/             Metrics CSVs from the real run
docs/screenshots/         12 UI screenshots (real, taken from the running app)
(docs/DEMO_SCRIPT.md was deleted from the repo by the user on GitHub on purpose; see D11)
sample_images/            3 HAM10000 sample images + a blurry file + a .txt file for rejection demos
```

**API** (Swagger at `/docs`): `GET /health`, `POST /auth/register`, `POST /auth/login` (OAuth2 form, username = email), `POST /predict` (multipart field `image`, auth), `GET /cases`, `GET /cases/{id}` (auth, owner only).
Response of `/predict`: `case_id, predicted_class, class_name, probabilities (7), entropy, entropy_threshold, review_recommended, review_reason, heatmap_base64, model_version, disclaimer, inference_ms`.

**Upload checks:** JPEG/PNG only (415), max 8 MB (413), each side at least 224 px (422), severe blur (422, sharpness measured at 512 px long side, threshold 5.0).

**Frontend behaviour:** no login screen. On first load `api.js` silently registers a random guest account and keeps its credentials in `localStorage`, so each browser has a private history. Photo input by camera (`getUserMedia`, with phone-camera fallback), file picker, or drag and drop. Result card has the review banner, uncertainty pill and meter (uses the server's `entropy_threshold`), probability bars, original vs Grad-CAM, and the disclaimer. The result is cleared when a new file is picked or analysis starts.

---

## 3. Status table (keep this current)

| Area | Status | Notes |
|---|---|---|
| Backend API (auth, predict, cases, health) | Done, tested | Smoke-tested with the real model. Swagger works. |
| Upload validation | Done, calibrated | Blur threshold calibrated on 43 real HAM10000 images. Catches only severe blur. |
| Model inference (MC Dropout, entropy, flag, Grad-CAM) | Done, tested | Matches the model contract. About 2 s per image on laptop CPU after warm-up. First image 15 to 35 s. |
| Trained model | Done | EfficientNet-B3 + MobileNetV2 baseline trained in Colab. Real metrics in section 5. |
| Frontend MVP (camera, upload, results, history, limitations) | Done, tested | Tested headless in Edge with a fake camera. NOT tested with a real webcam. |
| No-login anonymous sessions | Done | See decisions D3. |
| UI design and mobile layout | Done | 12 screenshots in `docs/screenshots/`. |
| README | Done | Demo video link added. |
| Demo video | Done | Recorded and linked in README: https://youtu.be/xynFxpXcZa8 |
| Executed notebook (with outputs) | NOT done | Repo copy has no outputs. User must download the executed .ipynb from Colab. |
| Docker Compose deployment | Written, NOT run | `docker compose config` passes. Daemon was not running, so images never built. |
| Hosting (Vercel + API host) | Planned, not started | API host not chosen yet. See section 7. |
| Skin-tone evaluation (Fitzpatrick) | Not started | Future work. Candidate datasets: Diverse Dermatology Images, Fitzpatrick17k, PAD-UFES-20 (check licences first). |
| Automated tests | None | Only manual smoke tests so far. |

---

## 4. Model contract (do not change without asking the user)

Files: `backend/model/efficientnet_b3_best.pth` (state_dict) and `model_config.json` with `input_size` 300, `mean`, `std` (ImageNet), `class_codes` (akiec, bcc, bkl, df, mel, nv, vasc), `class_names`, `mc_dropout_passes` 10, `entropy_threshold`, `melanoma_flag_threshold`, `melanoma_index` 4, `test_metrics`, `mission_metrics`, `disclaimer`, `limitations`.

Inference rules (must match training):
- Resize directly to 300x300 (no crop), ImageNet normalisation.
- `torchvision.models.efficientnet_b3(weights=None)`, replace `classifier[1]` with `Linear(in_features, 7)`, load the state_dict.
- MC Dropout: compute `F.adaptive_avg_pool2d(model.features(x),1).flatten(1)` once, run `model.classifier` T times with dropout in train mode, average the softmax. Entropy = -sum(p log p).
- Review flag = `entropy >= entropy_threshold` OR `P(melanoma) >= melanoma_flag_threshold`.
- Grad-CAM: target layer `model.features[-1]`, target = top predicted class, eval mode, fp32.

---

## 5. Real results (from the Colab run; never edit by hand)

Dataset: HAM10000, 10,015 images, 7 classes (nv is 66.9%). Lesion-level split, test set 1,441 images.

| Model | Accuracy | Macro precision | Macro recall | Macro F1 | Macro AUC | Melanoma sensitivity |
|---|---|---|---|---|---|---|
| EfficientNet-B3 | 0.8348 | 0.7310 | 0.7431 | 0.7322 | 0.9632 | 0.5753 |
| MobileNetV2 (baseline) | 0.8099 | 0.6495 | 0.7224 | 0.6727 | 0.9539 | 0.4178 |

Thresholds (chosen on validation): `entropy_threshold` 0.4129, `melanoma_flag_threshold` 0.05 (this is the lowest value the search allows, so it flags aggressively).

Uncertainty on the test set: 31.3% of images flagged; accuracy 93.5% unflagged vs 61.6% flagged; 73.0% of errors flagged; melanoma sensitivity 61.0% (top class) and 87.7% (counting a flag as a catch).

Training: EfficientNet-B3 14 epochs, MobileNetV2 10 epochs; AdamW lr 3e-4 wd 1e-4, cosine schedule, class-weighted cross-entropy, early stopping on validation macro-F1.

---

## 6. Known issues and limitations (add new ones here)

1. Dark-skin performance is unmeasured. HAM10000 is mostly lighter skin with no skin-tone labels.
2. Melanoma detection is weak (57.5% top-class sensitivity, 87.7% with the flag).
3. The model learned from dermoscope images. Phone photos are a different domain and are untested.
4. The model is often overconfident (frequently shows about 100% for one class).
5. MC Dropout is random: the same image can flag or not flag on different runs near the threshold.
6. Small classes (df has 9 test images, vasc 21) give unreliable scores.
7. The blur check is coarse (calibrated on 43 dermoscopy images, catches only severe blur).
8. The sample images and screenshots may be training images (the reproduced split did not match the notebook's counts, so held-out images could not be identified). They show the interface, not accuracy.
9. Host storage is ephemeral on most free hosts: SQLite and saved images reset on restart. If a database persists but images do not, `GET /cases/{id}` fails because the heatmap file is missing (not handled yet).
10. Public hosting would allow anyone to create sessions and upload. No rate limiting yet.
11. Real webcam path is untested (only a fake camera in headless Edge).
12. Docker images have never been built or run.

---

## 7. Open tasks (priority order; tick and move to the changelog when done)

**A. Submission (due soon)**
- [ ] User: download the executed notebook from Colab (File, Download, .ipynb) and replace `notebooks/skin_lesion_training.ipynb`; then commit.
- [x] Demo video recorded and linked in README (done by the user).
- [ ] User: revoke the GitHub token that was pasted in chat (GitHub, Settings, Developer settings, Personal access tokens).
- [ ] User: add the commit email e.kayonga@alustudent.com to GitHub (Settings, Emails) so commits link to their profile; check the Contributors list shows only them.
- [ ] Create the submission zip from committed files: `git archive -o capstone.zip HEAD`.
- [ ] Optionally try `docker compose up --build` once and record the result here.

**B. Hosting (not started; waiting on the user's choice of API host)**
Plan: React frontend on Vercel (Root Directory `frontend`, env `VITE_API_URL` set to the API address, build-time). API on a separate host because PyTorch plus the model needs about 1 to 2 GB RAM (Hugging Face Spaces Docker is the recommended free option; Render or Fly.io for always-on). Set `SECRET_KEY` and `CORS_ORIGINS` (JSON list with the Vercel address) as secrets on the API host.
Code changes to make when the host is chosen:
- [ ] Read the port from the environment (Hugging Face uses 7860) in `backend/Dockerfile` or the start command.
- [ ] Warm up the model at startup so the first user does not wait 15 to 35 s.
- [ ] Handle a missing heatmap file in `GET /cases/{id}` without a 500.
- [ ] Add simple rate limiting on `/auth/register` and `/predict`.
- [ ] Update the README deployment section with the real steps and the live URLs.

**C. Quality and science (later)**
- [ ] Evaluate on a diverse external set with Fitzpatrick labels; report sensitivity by skin tone. Do not claim improvement until measured.
- [ ] Investigate improving melanoma sensitivity (more data, calibration, better threshold search).
- [ ] Add export of split ids in the notebook so held-out sample images can be identified.
- [ ] Add automated tests (API smoke tests, quality-check unit tests).

---

## 8. Decisions and reasons (add new ones; never silently reverse one)

- **D1. Split by lesion, not by image.** HAM10000 has several photos per lesion; an image-level split leaks near-duplicates into the test set and inflates scores.
- **D2. Report macro metrics and melanoma sensitivity,** because about 67% of data is one class and plain accuracy misleads.
- **D3. No login screen, but keep auth under the hood.** The web app auto-creates a random guest account per browser (credentials in `localStorage`). This keeps per-device private history and a secured API, without a shared open history. Trade-off: clearing browser data loses access to old cases.
- **D4. Blur threshold 5.0 at 512 px.** The first guess (60) would have rejected 25 of 43 real images (58%). Calibrated on real HAM10000 images; blurred copies (sigma 3 or more) scored 5.6 or less. Only severe blur is caught.
- **D5. Added `entropy_threshold` to the `/predict` response** (additive change) so the uncertainty badge and the review banner always agree.
- **D6. API refuses to start if `SECRET_KEY` is shorter than 32 characters,** so nobody runs it with a guessable signing key.
- **D7. Model weights (41 MB) are committed** so a fresh clone runs. They contain no patient data. GitHub's limit is 100 MB per file.
- **D8. AI tooling files are kept out of Git** (local exclude) so only the author is visible. This file uses a neutral name on purpose, and tracked files must not name AI tools.
- **D9. Frontend on Vercel, API on a separate host,** because the model does not fit serverless limits. Camera access requires HTTPS, which both provide.
- **D10. Screenshots use real HAM10000 images and say they may be training images.** They show the interface, not accuracy.
- **D11. The user deleted `docs/DEMO_SCRIPT.md` from the repo on GitHub (commit 937e5c1).** Treat the script as intentionally removed. Do not recreate it in the repo. It remains in git history (commit a275443) if needed.

---

## 9. Changelog (newest first; add an entry after EVERY change)

Entry format:
```
### YYYY-MM-DD - short title (git: hash or "uncommitted")
- What changed and why (1 to 3 lines)
- Files: path1, path2
- Verified by: what you ran or checked (build, smoke test, screenshot)
```

### 2026-10-13 - Added this status document, synced with GitHub (git: see top line)
- Created PROJECT_STATUS.md so any AI assistant knows the goal, progress and rules, and must update it after every change.
- Found 2 commits made by the user on GitHub (ea65b00 adds the demo video link, 937e5c1 deletes docs/DEMO_SCRIPT.md). Fast-forwarded local main onto them (no merge, nothing lost).
- Fixed the broken markdown of the demo video link in README (stray parentheses and a line break) and removed "demo script" from the README file map.
- Files: PROJECT_STATUS.md, README.md (plus a local, uncommitted AI instruction file that points here)
- Verified by: `git log HEAD..origin/main` before the fast-forward; content checked against the repo, README and model_config.json.

### 2026-10-02 - User edits made directly on GitHub (git: ea65b00, 937e5c1, pushed)
- Added the demo video link to README (https://youtu.be/xynFxpXcZa8). Deleted docs/DEMO_SCRIPT.md.
- Files: README.md, docs/DEMO_SCRIPT.md (deleted)

### Milestone 3 - Demo script rewrite (git: a275443, pushed)
- Rewrote `docs/DEMO_SCRIPT.md` to follow the assignment rubric: data, architecture, metrics, deployment demo (about 9 minutes).
- Files: docs/DEMO_SCRIPT.md

### Milestone 2 - No login, camera, new UI (git: 32b3e8c, pushed)
- Removed the login screen (anonymous per-browser session), added Take a photo (camera) plus Upload and drag and drop, redesigned the whole UI (teal theme, uncertainty meter, side-by-side images, mobile layout). Retook all screenshots (12). Updated README and demo script.
- Files: frontend/src/* (App.jsx, api.js, styles.css, components/*), docs/screenshots/*, README.md, docs/DEMO_SCRIPT.md. Removed Login.jsx.
- Verified by: `npm run build`; headless Edge run covering camera capture (fake camera), upload, blur and wrong-type rejection, history after reload, mobile width; no page errors.

### Milestone 1 - Initial MVP (git: 07bd4c8, pushed)
- Built the FastAPI backend, React frontend, Colab notebook (with per-epoch checkpoint and resume), README, docs, Docker files. Added the trained model and the real results. Fixed bugs found with real images: blur threshold too strict (D4), stale result shown under a new image, badge contradicting the review banner (D5), no guard on weak `SECRET_KEY` (D6).
- Files: backend/*, frontend/*, notebooks/*, docs/*, sample_images/*, README.md, docker-compose.yml, .gitignore
- Verified by: API smoke tests (auth, rejections, predict with the real model, cases), `npm run build`, screenshots reviewed one by one.
