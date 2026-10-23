# MODEL EXPLANATION

**Decision-support prototype only. Not a diagnosis. Consult a qualified clinician.**

This document explains, in simple words, everything I built for my capstone: what the system does, how I built each part, which datasets I used and why, the problems I ran into, and how I solved them. Every number here comes from my own training and test runs (the files in `docs/results/`). Nothing is estimated or made up.

Author: Kayonga Elvis, African Leadership University, BSc Software Engineering.

---

## Contents

1. [The problem I am trying to solve](#1-the-problem-i-am-trying-to-solve)
2. [What I built, in one picture](#2-what-i-built-in-one-picture)
3. [The datasets I used and why](#3-the-datasets-i-used-and-why)
4. [How I built the model](#4-how-i-built-the-model)
5. [How each part of the system works](#5-how-each-part-of-the-system-works)
6. [My notebooks and what each one is for](#6-my-notebooks-and-what-each-one-is-for)
7. [My results](#7-my-results)
8. [Challenges I met and how I solved them](#8-challenges-i-met-and-how-i-solved-them)
9. [What my system cannot do yet](#9-what-my-system-cannot-do-yet)
10. [What I would do next](#10-what-i-would-do-next)
11. [Glossary of terms](#11-glossary-of-terms)

---

## 1. The problem I am trying to solve

In Rwanda, and in many low-resource settings, there are very few dermatologists. People with a worrying skin lesion often wait a long time, or never see a specialist at all. Some of those lesions are skin cancer, and melanoma in particular is dangerous if it is found late.

I wanted to build a tool that helps a health worker **decide which lesions need a specialist's attention first**. It looks at a photo of a skin lesion and gives:

- the most likely type of lesion, with a probability for each of 7 types
- how sure it is (its uncertainty)
- a heatmap showing which part of the photo it looked at
- a clear "Review recommended" warning when it is unsure or sees a possible melanoma

**It is pre-screening, not diagnosis.** It does not replace a doctor. Every result screen says so.

My personal goal is that a tool like this works **fairly for people with Black and dark skin**. As I explain below, my current model does not achieve that yet, and I measured why.

---

## 2. What I built, in one picture

```
  Phone / laptop browser                      My server (API)
  +-----------------------------+   photo   +-------------------------------------------+
  | Take a photo or upload one  | --------> | 1. Check the photo (type, size, blur)      |
  |                             |           | 2. Model looks at it 10 times (uncertainty)|
  | See: lesion type,           | <-------- | 3. Decide: review recommended or not       |
  | probability bars,           |  result   | 4. Draw a heatmap (Grad-CAM)               |
  | uncertainty, heatmap,       |           | 5. Save the case in the database           |
  | warning, disclaimer         |           +-------------------------------------------+
  +-----------------------------+
```

The system has three layers:

| Layer | What it is | Built with |
|---|---|---|
| Model | The AI that looks at the photo | PyTorch, EfficientNet-B3 |
| Backend (API) | The server that checks photos, runs the model, saves cases | Python, FastAPI, SQLite |
| Frontend | The web page people use | React |

---

## 3. The datasets I used and why

I used four public datasets. Each one has a different job. I chose them because each answered a specific question, not just to have "more data".

### 3.1 HAM10000: my main training data

- **What it is:** 10,015 photos of skin lesions taken with a dermatoscope (a magnifying lens with built-in light). Each photo has an expert-confirmed label.
- **The 7 lesion types it covers:**

| Code | Lesion type | Danger |
|---|---|---|
| nv | Melanocytic nevi (common moles) | benign |
| bkl | Benign keratosis-like lesions | benign |
| df | Dermatofibroma | benign |
| vasc | Vascular lesions | benign |
| akiec | Actinic keratoses / intraepithelial carcinoma | pre-cancer |
| bcc | Basal cell carcinoma | cancer |
| mel | Melanoma | dangerous cancer |

- **Why I used it:** it is the best-known public dataset for these 7 lesion types, it is free for research, and the labels are reliable. It let me build and test a working model quickly.
- **Its big weakness:** the patients are mostly light-skinned, and the dataset has no skin-tone labels. Also, 66.9% of the photos are common moles, so the classes are very unbalanced.
- **How I split it:** 7,116 photos for training, 1,458 for validation (choosing settings), 1,441 for testing (final marks). I split by **lesion**, not by photo (see challenge 2).
- **Licence:** CC BY-NC 4.0 (non-commercial use with credit).

### 3.2 PAD-UFES-20: real smartphone photos

- **What it is:** 2,298 photos of skin lesions taken with ordinary **smartphones** in Brazil, with patient IDs and confirmed labels.
- **Why I used it:** my app accepts phone photos, because that is what a health worker in Rwanda would actually use. HAM10000 only has dermatoscope photos, which look very different. I needed to know how my model does on phone photos, and whether training on them helps.
- **What I did with it:** I mapped its labels to my 7 types (basal cell carcinoma to bcc, actinic keratosis to akiec, nevus to nv, seborrheic keratosis to bkl, melanoma to mel). I **dropped squamous cell carcinoma** because HAM10000 has no class for it. That left 2,106 photos, which I split **by patient** into 1,494 training, 304 validation and 308 test photos.
- **Its weakness:** most patients have lighter skin (only 8 Fitzpatrick V photos and 1 Fitzpatrick VI photo). The test set has only 4 melanomas.
- **Licence:** CC BY (free with credit). I downloaded it from the ISIC Archive (collection 406).

### 3.3 ISIC Archive, dark skin, benign: testing false alarms on dark skin

- **What it is:** 410 lesions from 21 patients with Fitzpatrick skin type V or VI (dark skin), from Memorial Sloan Kettering Cancer Center. All are labelled only as **benign**, without a specific lesion type.
- **Why I used it:** it is the largest openly licensed set of dark-skin lesion photos I could find. Because every lesion is benign, it tells me how often my model **wrongly raises the alarm** on dark skin.
- **How I used it:** for **testing only**, never training. I used one photo per lesion so the same lesion is not counted twice.
- **Its weakness:** only 21 patients from one hospital, and no specific lesion types, so it cannot tell me whether my model finds cancer on dark skin.
- **Licence:** CC BY.

### 3.4 Fitzpatrick17k, dark skin, labelled: testing accuracy on dark skin

- **What it is:** a public collection of 16,577 clinical photos with skin-type labels. I kept only dark-skin photos (Fitzpatrick V and VI) whose condition matches one of my 7 types. That gave 137 photos, but only **48 could still be downloaded** because many of the original web links are broken.
- **Why I used it:** it is the only public source I found with **dark skin and a matching lesion label**, so it is the only way I could measure accuracy on dark skin directly.
- **How I used it:** for **testing only**, never training.
- **Its weakness:** very small (48 photos: 24 basal cell carcinoma, 18 melanoma, 3 actinic keratosis, 3 vascular), web-sourced photos with some label noise.
- **Licence:** CC BY-NC-SA 3.0.

### 3.5 Datasets I looked at but did not use

| Dataset | Why I did not use it |
|---|---|
| ISIC 2019 | It would add about 15,000 more training photos, but almost all from lighter skin. My tests showed that adding more light-skin data made dark skin worse, so I dropped this plan. |
| DDI (Diverse Dermatology Images) | Good dark-skin data, but it requires a signed access agreement and I did not have time to get approval before my deadline. |
| SCIN (Google) | It has good skin-tone balance, but it is mostly rashes and infections, not skin cancer, so it does not match my 7 lesion types. |

---

## 4. How I built the model

### 4.1 The model I chose: EfficientNet-B3

- **What it is:** a convolutional neural network (CNN), a type of AI that is very good at understanding images.
- **Why I chose it:** it gives high accuracy for its size, so it can run on a normal computer without an expensive GPU.
- **Transfer learning:** I did not start from zero. The model was first trained by others on ImageNet (millions of everyday photos), so it already knew edges, colours and textures. I then **fine-tuned** it on skin lesions. This works well when you only have about 10,000 images.
- **What I changed:** I replaced its last layer with a new one that outputs my 7 lesion types.
- **How it is built inside:** a starting convolution layer, then 26 MBConv blocks (they use depthwise-separable convolutions, squeeze-and-excitation attention and the SiLU activation), then average pooling, a dropout layer (30%), and my final layer with 7 outputs.

### 4.2 The comparison model: MobileNetV2

I also trained MobileNetV2, a smaller and faster model, with the same settings. This let me show that EfficientNet-B3 was the better choice, using real numbers instead of just saying so.

### 4.3 How I trained it

| Setting | What I used | Why |
|---|---|---|
| Photo size | 300 by 300 pixels, resized straight (no cropping) | So the lesion edges are never cut off |
| Colour normalisation | ImageNet averages | Because the model was pre-trained that way |
| Augmentation | Random flips, rotations up to 30 degrees, colour changes | So the model learns the lesion, not the camera angle or lighting |
| Loss | Class-weighted cross-entropy | Rare lesion types count more, so the model does not just guess "mole" |
| Optimiser | AdamW, learning rate 0.0003, weight decay 0.0001 | A reliable choice for fine-tuning |
| Schedule | Cosine learning rate | Big steps first, small careful steps at the end |
| Stopping | Early stopping on validation macro-F1 | Stop when the model stops improving, to avoid overfitting |
| Speed | Mixed precision on a Google Colab GPU | Faster training |
| Safety | A checkpoint saved after every epoch | So a Colab disconnect does not lose my work |

EfficientNet-B3 trained for 14 epochs and MobileNetV2 for 10.

### 4.4 Uncertainty: how the model knows when it is unsure

A normal model always gives one confident answer, even when it is guessing. I wanted mine to **admit when it is unsure**.

- **How:** I use a method called **MC Dropout**. When the model looks at a photo, it runs its last layer **10 times**, each time randomly switching off some connections. If the 10 answers agree, the model is sure. If they disagree, it is unsure.
- **I measure the disagreement with "entropy".** High entropy means unsure.
- **The review rule:** the app shows "Review recommended" if the entropy is at least **0.413**, or if the chance of melanoma is at least **5%**. I chose both numbers using the validation set only, never the test set.
- **Why such a low melanoma threshold?** Missing a melanoma is the worst possible mistake, so I made the tool cautious. The cost is that it flags about 1 in 3 photos for review.

### 4.5 Explainability: showing where the model looked

I use **Grad-CAM**, which colours the parts of the photo that most influenced the answer (red means strong influence). This helps a health worker check that the model looked at the lesion, not at a hair or a ruler. A heatmap shows where the model looked. It does not prove the answer is right.

### 4.6 Calibration: making the probabilities honest

My model was **overconfident**: it often said "100%" even when wrong. I tested a fix called **temperature scaling**: one number (2.017, chosen on validation data) that softens the probabilities. It made the probabilities much more honest (see section 7.3). I saved the result as extra settings, but I have **not switched it on in the live app yet**, so the app, README and video all match.

---

## 5. How each part of the system works

### 5.1 Photo input (frontend)

- **Three ways to add a photo:** take one with the camera, upload a file, or drag and drop.
- **Camera:** the page opens the camera with a circle guide to centre the lesion. On phones where the browser cannot open it in the page, the phone's own camera app opens instead. Browsers only allow the camera on a secure (HTTPS) site or on localhost.
- **No login screen:** when someone opens the app for the first time, it quietly creates a private anonymous account for that browser. So people go straight in, but each browser still has its own private history, and nobody can see someone else's cases.

### 5.2 Quality checks (backend)

Before the model runs, the server checks the photo and rejects bad ones with a clear message:

| Check | Rule | Error shown |
|---|---|---|
| File type | JPEG or PNG only | "Unsupported file type" |
| File size | 8 MB or less | "Image is too large" |
| Resolution | each side at least 224 pixels | "Resolution is too low, move closer" |
| Blur | sharpness score at least 5.0 | "Image looks too blurry, hold steady" |

I measure sharpness with the **Laplacian variance** on the photo resized to 512 pixels, so the score does not depend on the camera's resolution.

### 5.3 Prediction (backend)

1. Resize the photo to 300 by 300 pixels.
2. Run the model's feature layers once.
3. Run the last layer 10 times with dropout on (MC Dropout) and average the answers.
4. Work out the entropy and the review decision.
5. Draw the Grad-CAM heatmap for the most likely type.
6. Save the case, the result and the heatmap.
7. Send everything back in about 2 seconds (the very first photo takes 15 to 35 seconds while the model warms up).

### 5.4 Result screen (frontend)

- The **most likely type** in large text.
- An **uncertainty meter** with the review threshold marked in the middle. The badge (Low, Medium, High) uses the **same threshold** as the server, so the badge and the warning can never disagree.
- **Probability bars** for all 7 types.
- The **photo and its heatmap** side by side.
- The **"Review recommended" banner** with the reason, when it applies.
- The **disclaimer** on every screen.

### 5.5 History and limitations

- **History** lists every past case for that browser, and any case can be reopened.
- **Limitations** are shown on the main screen and on their own tab: not a diagnosis, mostly light-skin training data, not validated on dark skin, and do not upload real patient photos.

### 5.6 Security and privacy

- Passwords are **hashed** (bcrypt). Logins use **tokens** (JWT).
- The server **refuses to start** without a strong secret key (at least 32 characters), so nobody can run it with a guessable key.
- Secrets (`.env`, `kaggle.json`) are **never stored in Git**. The `.gitignore` blocks every `.env` variant and key files.
- The app is a prototype: **no real patient data** is used.

### 5.7 API (for other apps)

The same functions are available through an API, with an interactive test page (Swagger UI) at `/docs`:

| Endpoint | What it does |
|---|---|
| `GET /health` | Is the server up and is the model loaded? |
| `POST /auth/register`, `POST /auth/login` | Create an account or log in |
| `POST /predict` | Send a photo, get the full result |
| `GET /cases`, `GET /cases/{id}` | List past cases, or open one |

### 5.8 Deployment plan

- **Today:** it runs on my laptop (SQLite database).
- **Production design:** Docker Compose with a PostgreSQL database, the API and the web app. The files are written but not yet tested end to end.
- **Hosting plan:** the web page on Vercel and the API on a separate server, because the model needs more memory than Vercel's serverless functions allow.
- **Before any real use:** ethics approval (Rwanda National Ethics Committee), patient consent, and following Rwanda's data protection law (Law No. 058/2021), which expects personal data to be stored in Rwanda.

---

## 6. My notebooks and what each one is for

All training runs in the cloud (Google Colab or Kaggle), because my laptop has no suitable GPU.

| Notebook | Purpose | Status |
|---|---|---|
| `notebooks/skin_lesion_training.ipynb` | My **main notebook**. It explores the data with charts, splits it by lesion, trains EfficientNet-B3 and MobileNetV2, measures them, chooses the uncertainty thresholds, draws Grad-CAM examples, and exports the model files the app uses. | Run in Colab |
| `notebooks/phase1_export_logits.ipynb` | Rebuilds my exact data split, **checks it matches** the original run, and saves the model's raw answers (10 passes per photo) so I could test calibration on my laptop without retraining. | Run in Colab |
| `notebooks/phase3_finetune_public.ipynb` | Fine-tunes my model on **phone photos** (PAD-UFES-20) and tests both the old and new model on **dark-skin** photos, with confidence intervals. It only lets the new model replace the old one if a rule I wrote beforehand is passed. | Run on a Kaggle T4 GPU (27 minutes) |

Supporting scripts:

| File | Purpose |
|---|---|
| `backend/scripts/calibrate.py` | Runs the calibration test on my laptop using the saved raw answers |
| `backend/app/ml/calibration.py` | The calibration maths, kept in one place |
| `backend/tests/` | 58 automated tests: unit tests for each part (quality rules, review rule, security, services, calibration) and integration tests of the whole API with the real model |

---

## 7. My results

All results are on **test data the model never trained on**.

### 7.1 Main model on HAM10000 (1,441 test photos)

| Model | Accuracy | Macro F1 | Macro AUC | Melanoma found |
|---|---|---|---|---|
| **EfficientNet-B3 (mine)** | **83.5%** | **0.732** | **0.963** | **57.5%** |
| MobileNetV2 (comparison) | 81.0% | 0.673 | 0.954 | 41.8% |

EfficientNet-B3 is better on every measure. I report **macro** scores because plain accuracy hides problems: a model that always says "mole" would already score about 67%.

Per lesion type, common moles (nv) and vascular lesions do best. **Melanoma is the weak spot**: the model names it correctly 57.5% of the time.

### 7.2 The review flag (uncertainty)

| On the test set | Result |
|---|---|
| Photos flagged for review | 31.3% |
| Accuracy on photos not flagged | 93.5% |
| Accuracy on flagged photos | 61.6% |
| Model mistakes that were flagged | 73.0% |
| Melanomas caught (named correctly, or flagged) | 87.7% |

The flag works: the model is much more accurate when it is not worried, and it flags most of its own mistakes. But about 1 in 8 melanomas is still neither named nor flagged.

### 7.3 Calibration test (not switched on in the app)

| On the test set | Before | After |
|---|---|---|
| Calibration error (lower is better) | 0.095 | 0.021 |
| Accuracy | 83.2% | 83.1% |
| Melanomas caught (named or flagged) | 88.4% | 91.8% |
| Photos flagged | 31.9% | 35.8% |

These "before" numbers differ a little from section 7.2 because the 10 random passes are random each time.

### 7.4 Phone photos and dark skin (Phase 3)

| Test set | Measure | My current model | After fine-tuning on phone photos |
|---|---|---|---|
| HAM10000 (1,441 dermatoscope photos) | Macro F1 | 0.732 | 0.708 |
| PAD-UFES-20 (308 phone photos) | Accuracy | **34.1%** | **80.2%** |
| Dark skin, benign (410 lesions, 21 patients) | Wrongly called pre-cancer or cancer | 1.7% | **31.2%** |
| Dark skin, labelled (48 photos) | Accuracy | 27.1% | 25.0% |
| Dark skin melanomas (18) | Recognised as melanoma | 6 | **0** |

What I learned:

1. **My model fails on phone photos** (34%), and training on phone photos fixes most of that (80%).
2. **My model does poorly on dark skin** (27% accuracy).
3. **Adding more light-skin data made dark skin worse.** False alarms on benign dark-skin lesions jumped from 1.7% to 31.2%, and none of the 18 dark-skin melanomas was recognised.
4. **So I did not deploy the fine-tuned model.** Before the run, I wrote a rule: no loss on the original test set and no rise in dark-skin false alarms. It failed both, so the app still runs my original model.

The dark-skin test sets are small, so these numbers are evidence of the problem, not a final measurement. But they clearly show that **the fix for dark skin is data from dark-skinned patients**.

---

## 8. Challenges I met and how I solved them

| # | Challenge | What I did | Why |
|---|---|---|---|
| 1 | **Unbalanced classes:** 67% of photos are common moles | Class-weighted loss, and I report macro scores | So rare but dangerous types are not ignored, and my scores are not inflated |
| 2 | **Same lesion, several photos:** HAM10000 has several photos of one lesion | I split by lesion, not by photo, and checked in code that no lesion is in two sets | Otherwise near-identical photos in training and test would make my scores look better than they are |
| 3 | **Colab disconnects** stopped my training | A checkpoint saved to Google Drive after every epoch, with automatic resume | A disconnect now costs at most one epoch |
| 4 | **My first blur check rejected good photos:** my first guess threshold would have rejected 25 of 43 real photos | I measured sharpness on 43 real HAM10000 photos and set the threshold to 5.0 | Real dermatoscope photos are naturally smooth; the new threshold still rejects badly blurred photos |
| 5 | **Uncertainty badge contradicted the warning** ("Low" next to "High uncertainty") | The badge now uses the same threshold as the server | A screening tool must never give mixed messages |
| 6 | **An old result stayed on screen** under a new photo | The result clears as soon as a new photo is chosen | So a result is never shown next to the wrong photo |
| 7 | **The model was overconfident** (often 100%) | MC Dropout uncertainty, the review flag, and a calibration test | A probability should mean what it says |
| 8 | **Melanoma is often missed** | A low melanoma threshold (5%) on the review flag | Missing a melanoma is worse than an extra review; this raised melanoma catching to 87.7% |
| 9 | **Weak secret key risk** | The server refuses to start without a 32-character key | Protects logins from being forged |
| 10 | **Login made the app hard to use** | An automatic private anonymous session per browser | Easy to use, and each person's history stays private |
| 11 | **Very little public dark-skin data** | I searched every public option, used dark-skin photos for testing only, and measured the gap | With so few photos, training on them would leave nothing honest to test with |
| 12 | **Phone photos look different** from dermatoscope photos | I measured it (34%) and fine-tuned on PAD-UFES-20 (80%) | The app accepts phone photos, so this matters for real use |
| 13 | **Fine-tuning could quietly make things worse** | I wrote a promotion rule before the run | So I could not fool myself after seeing the results; it correctly blocked a harmful model |
| 14 | **I could not tell if my demo photos were training photos** | I exported my exact split and checked: two sample photos were training photos, one was a test photo | So my screenshots are not mistaken for accuracy proof |
| 15 | **No GPU on my laptop** | I trained on Google Colab and Kaggle | My laptop would need about 5 hours per epoch |

---

## 9. What my system cannot do yet

- **It is not a diagnosis tool** and must never be used alone.
- **It is not safe for dark skin yet:** 27% accuracy on dark-skin photos in my test.
- **It is weak on phone photos:** 34% accuracy with the current model.
- **It misses melanomas:** it names 57.5% correctly, 87.7% with the review flag.
- **It is overconfident** without calibration.
- **It is trained mostly on dermatoscope photos** from lighter-skinned patients in Europe and Australia.
- **It is not clinically validated** and has no ethics approval for use on patients.

---

## 10. What I would do next

1. **Collect consented local data in Rwanda:** phone photos of lesions on dark skin, labelled by dermatologists and confirmed by biopsy where possible, with ethics approval.
2. **Retrain and test on that data,** reporting results separately for each skin tone.
3. **Get access to DDI** (a dark-skin dataset that needs an agreement) for a proper outside test.
4. **Switch on calibration** in the live app once tested.
5. **Run a supervised study** comparing the tool with dermatologists before any pilot.
6. **Deploy** with the web page on Vercel and the API on a server in Rwanda, following Rwanda's data protection law.

---

## 11. Glossary of terms

| Term | Simple meaning |
|---|---|
| Accuracy | The share of photos the model got right |
| Sensitivity | Of all the real cases (for example melanomas), the share the model found |
| Macro F1 | A score that treats all 7 lesion types as equally important, so rare types count |
| AUC | How well the model ranks the right type above the wrong ones (1.0 is perfect) |
| Validation set | Photos used to choose settings, never for the final marks |
| Test set | Photos kept aside until the end, used only for the final marks |
| Fine-tuning | Taking an already-trained model and training it a little more on new data |
| Overfitting | When a model memorises its training photos instead of learning general patterns |
| MC Dropout | Running the model several times with random parts switched off, to measure uncertainty |
| Entropy | A number for how unsure the model is |
| Grad-CAM | A heatmap of where the model looked |
| Calibration | Making the model's probabilities match how often it is really right |
| Fitzpatrick scale | A scale of skin types from I (very light) to VI (very dark) |
| Dermatoscope | A magnifying lens with light, used by skin doctors |
| Confidence interval (CI) | The range the true value probably lies in; small test sets give wide ranges |
