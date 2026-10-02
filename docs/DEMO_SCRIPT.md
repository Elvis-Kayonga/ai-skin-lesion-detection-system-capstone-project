# Demo video script (target: 7 to 8 minutes, limit 5 to 10)

Goal: show the working app. Keep the intro under 30 seconds. Do not explain the research, show the features.

## Before you record (5 minutes)

- Backend running (`uvicorn app.main:app`), web app running (`npm run dev`).
- Do one analysis first so the model is warm. The very first image takes 15 to 35 seconds, later ones about 2 seconds.
- Use a fresh browser window, zoom to 110 percent so text is readable, close other tabs.
- Have these ready in a folder: `sample_images/` (3 lesion images, the blurry file, the .txt file).
- Delete `backend/skin_screening.db` before recording if you want an empty history.
- Record with any screen recorder with microphone on. Speak slowly.

## Scenes

| Time | What you do on screen | What you say (short) |
|---|---|---|
| 0:00 | Show the login page | "This is a skin lesion pre-screening prototype for places with few dermatologists. It is decision support only, not a diagnosis, and that sentence is on every screen." |
| 0:30 | Scroll to the Limitations panel on the login page | "The limitations are visible before login: the training data is mostly light skin, and it is not validated on dark skin." |
| 1:00 | Click Register, create an account, you land on the Screen tab | "Accounts use hashed passwords and login tokens." |
| 1:30 | Choose a sample image, show the preview, click Analyse | "I upload a lesion image. The server checks type, size, resolution and blur first." |
| 2:15 | Show the result card: top class, bars, uncertainty badge | "It gives a probability for all 7 classes and an uncertainty level. Uncertainty comes from running the model 10 times with dropout on." |
| 3:00 | Point at the heatmap next to the original | "The heatmap shows where the model looked. It is an explanation aid, not proof the model is right." |
| 3:30 | Analyse the second image that triggers "Review recommended" | "When the model is unsure, or sees a possible melanoma, it shows this banner and the reason. The badge and banner use the same threshold." |
| 4:15 | Upload the blurry image | "Bad input is rejected with a clear message instead of giving a wrong answer." |
| 4:45 | Upload the .txt file (see note below) | "Wrong file types are rejected too." |
| 5:15 | Open the History tab, click View on an older case | "Every case is stored, and I can reopen the result and heatmap." |
| 5:45 | Open http://localhost:8000/docs | "This is the API page, Swagger UI. The same functions are available for other apps to use." |
| 6:15 | In Swagger: Authorize, then try POST /predict with an image, show the JSON | "Here is the raw output: probabilities, entropy, review flag, heatmap and timing." |
| 7:00 | Open the notebook outputs or README Results section | "On the held-out test set: 83.5 percent accuracy, macro F1 0.732. The weak point is melanoma sensitivity at 57.5 percent, 87.7 percent when the review flag counts. That is why the app flags rather than reassures." |
| 7:40 | Show the Limitations section of the README | "Next step is testing on a dataset with skin-tone labels. Nothing here claims it works on dark skin." |
| 8:00 | End | "Thank you." |

Note for the .txt upload: the file picker only offers JPEG and PNG by default. In the file dialog switch the filter to "All files" to select the .txt file.

## Tips

- If the first analysis is slow on camera, say "the model is warming up". Better, warm it up before recording.
- If a result is surprising, say so. Honest is better than polished: the model is overconfident on some images and the same image can flag differently between runs. Mention it once.
- Do not say the app diagnoses, detects cancer, or works on all skin tones.
- Do not show your `.env` file, `kaggle.json`, or any secret.
- Upload to YouTube as unlisted, or to Google Drive with link sharing on, then paste the link into the README at "Demo video".
