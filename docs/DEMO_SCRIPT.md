# Demo video script (target: 7 to 8 minutes, limit 5 to 10)

Goal: show the working app. Keep the intro under 30 seconds. Do not explain the research, show the features.

## Before you record (5 minutes)

- Backend running (`uvicorn app.main:app`), web app running (`npm run dev`), open http://localhost:5173.
- Do one analysis first so the model is warm. The very first image takes 15 to 35 seconds, later ones about 2 seconds.
- Use a fresh browser window, zoom to 110 percent so text is readable, close other tabs.
- Allow the camera when the browser asks, and test that your webcam shows up before recording.
- Have these ready: the `sample_images/` folder (3 lesion images, the blurry file, the .txt file).
- For an empty history, delete `backend/skin_screening.db` while the backend is stopped, then start it again.
- Record with any screen recorder with the microphone on. Speak slowly.

## Scenes

| Time | What you do on screen | What you say (short) |
|---|---|---|
| 0:00 | Show the home screen | "This is a skin lesion pre-screening prototype for places with few dermatologists. It is decision support only, not a diagnosis, and that sentence is shown at the top and bottom of every screen." |
| 0:30 | Point at the "Know the limits" box | "The key limits are visible straight away: the training data is mostly lighter skin and it is not validated on dark skin." |
| 1:00 | Click **Take a photo**, allow the camera, point it at any safe object or a printed sample image, click **Capture photo** | "I can take a photo with the camera. The circle helps centre the lesion." |
| 1:45 | Click **Choose a different photo**, pick a sample image, show the preview | "Or I can upload a photo, or drag and drop one." |
| 2:15 | Click **Analyse image** | "The server first checks file type, size, resolution and blur." |
| 2:45 | Show the result: class, uncertainty meter, probability bars | "It gives a probability for all 7 classes and an uncertainty level. Uncertainty comes from running the model 10 times with dropout switched on." |
| 3:30 | Point at the heatmap next to the photo | "The heatmap shows where the model looked. It is an explanation aid, not proof that the model is right." |
| 4:00 | Analyse the second sample image that shows "Review recommended" | "When the model is unsure, or sees a possible melanoma, it shows this banner with the reason. The badge and the banner use the same threshold." |
| 4:45 | Upload the blurry image, then the .txt file | "Bad input is rejected with a clear message instead of giving a wrong answer." |
| 5:30 | Open the **History** tab, click **View** on an older case | "Every case is saved for this browser, and I can reopen the result and heatmap. There is no login screen, the app keeps a private anonymous session for each browser." |
| 6:15 | Open http://localhost:8000/docs | "This is the API page, Swagger UI. Other apps can use the same functions." |
| 6:45 | In Swagger: try `POST /auth/register`, click **Authorize**, then try `POST /predict` with an image, show the JSON | "Here is the raw output: probabilities, entropy, review flag, heatmap and timing." |
| 7:30 | Show the Results section of the README | "On the held-out test set: 83.5 percent accuracy, macro F1 0.732. The weak point is melanoma sensitivity: 57.5 percent, or 87.7 percent when the review flag counts. That is why the app flags rather than reassures." |
| 8:15 | Show the Limitations section of the README | "Next step is testing on a dataset with skin-tone labels. Nothing here claims it works on dark skin." |
| 8:40 | End | "Thank you." |

Note for the .txt upload: the file picker only offers JPEG and PNG by default. In the file dialog switch the filter to "All files" to pick the .txt file.

## Tips

- If the first analysis is slow on camera, say "the model is warming up". Better, warm it up before recording.
- If a result is surprising, say so. Honest is better than polished: the model is overconfident on some images and the same image can flag differently between runs. Mention it once.
- Do not say the app diagnoses, detects cancer, or works on all skin tones.
- Do not show your `.env` file, `kaggle.json`, or any secret.
- Do not point the camera at a real person's skin lesion. Use sample images only.
- Upload to YouTube as unlisted, or to Google Drive with link sharing on, then paste the link into the README at "Demo video".
