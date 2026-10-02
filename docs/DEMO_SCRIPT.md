push# Demo video script (target 9 minutes, limit 10, minimum 5)

This script follows the assignment rubric in order. Keep introductions short and spend the time on showing things working.

| Rubric item | Where in this video |
|---|---|
| Data visualization and data engineering | Part 1 (notebook) |
| Model architecture (layers, activations, optimisation) | Part 2 (notebook) |
| Initial performance metrics | Part 3 (notebook) |
| Deployment option: mockup / MVP (web interface, API UI) | Part 4 (live app and Swagger UI) |

Text in quotes is what you say. Plain text is what you do on screen. Read it naturally, in your own words, and slow down at the numbers.

## Before you record

- Open the **executed** notebook (with all outputs showing) in one browser tab. If you have not saved the executed version yet: in Colab use File, Download, .ipynb, and open that. The same charts are also saved in `docs/figures/` as a backup.
- Backend running (`uvicorn app.main:app`) and web app running (`npm run dev`). Open http://localhost:5173 in a second tab and http://localhost:8000/docs in a third.
- Run one analysis first so the model is warm. The first image can take 15 to 35 seconds, later ones about 2 seconds.
- Allow the camera in the browser and check your webcam works. Do not point it at anyone's real skin lesion. Use a sample image on screen or a safe object.
- Zoom the browser to 110 percent, close other tabs and hide any secrets (`.env`, `kaggle.json`).
- Use any screen recorder with the microphone on. One take is fine, small pauses are fine.

---

## Intro (0:00 to 0:20)

Show the app home screen.

> "Hello, I am Kayonga Elvis. This is my capstone prototype: an explainable, uncertainty-aware skin lesion pre-screening tool for places with few dermatologists. It is decision support only, not a diagnosis. I will show the data, the model, the results, and then the working application."

---

## Part 1: Data visualization and data engineering (0:20 to 2:40)

Switch to the notebook. Scroll to Section 2.

**Class distribution chart**

> "The model is trained on HAM10000: 10,015 dermoscopic images across 7 skin lesion types. This chart shows the first big challenge: the classes are very imbalanced. Melanocytic nevi, which are common moles, make up about 67 percent of the data. Dermatofibroma and vascular lesions are tiny classes."

**Demographics chart (age, sex, body site)**

> "Here is who is in the data: age, sex and body site. Notice that the dataset has no skin-tone labels. It comes mostly from lighter-skinned patients. This is the main limitation of this project, and I will come back to it."

**Class versus body site heatmap, then the sample images grid**

> "This heatmap shows how lesion types relate to body location, which tells us the data has real structure. And these are example images from each class, so you can see how similar some of them look, for example benign and malignant pigmented lesions."

**Data engineering cells (split, class weights, augmentation)**

> "Now the data engineering. First, the split. HAM10000 contains several photos of the same lesion. If I split randomly by image, near-identical photos would land in both training and test sets and inflate the scores. So I split by lesion, keeping each lesion in only one set, and checked in code that there is no overlap. The split is roughly 70 percent train, 15 validation and 15 test, and the test set has 1,441 images."

> "Second, because of the imbalance I use a class-weighted loss, so mistakes on rare classes cost more. Third, images are resized straight to 300 by 300 with standard ImageNet normalisation, and the training images are augmented with flips, rotation and colour changes."

---

## Part 2: Model architecture (2:40 to 4:30)

Scroll to Section 3. Show the printed classifier and the model summary.

> "The proposed model is EfficientNet-B3, pretrained on ImageNet and fine-tuned on this data. It starts with a convolution stem, then a stack of MBConv blocks. These use depthwise separable convolutions, squeeze-and-excitation attention, batch normalisation, and the SiLU activation function. After the feature layers there is global average pooling, a dropout layer with 0.3 probability, and a final linear layer with 7 outputs, one per class."

Point at the parameter count in the summary output.

> "The summary shows the layer shapes and the parameter counts. As a baseline I also trained MobileNetV2, a lighter model that uses ReLU6 activations, so I can show what the bigger model adds."

Scroll to the training function.

> "For optimisation I use the AdamW optimiser with a learning rate of 0.0003 and weight decay of 0.0001, a cosine learning-rate schedule, class-weighted cross-entropy loss, gradient clipping, and mixed precision to speed up training. Training stops early when validation macro F1 stops improving. EfficientNet-B3 trained for 14 epochs and MobileNetV2 for 10. The notebook also saves a checkpoint to Google Drive after every epoch, so training can resume if Colab disconnects."

Show the training curves chart.

> "Training loss keeps falling while validation F1 flattens around 0.73 to 0.74. That tells me the model starts to overfit, which is why I use early stopping."

---

## Part 3: Initial performance metrics (4:30 to 6:30)

Scroll to Section 5. Show the model comparison table.

> "Here are the results on the held-out test set. EfficientNet-B3 reaches 83.5 percent accuracy, macro precision 0.731, macro recall 0.743 and macro F1 0.732, with a macro AUC of 0.963. The MobileNetV2 baseline gets 81.0 percent accuracy and macro F1 0.673. So the proposed model is better on every metric."

> "I report macro averages because plain accuracy is misleading here. A model that always says 'mole' would already get about 67 percent."

Show the per-class report and the confusion matrix.

> "Per class, moles and vascular lesions are strong. The weak spot is melanoma: recall is 57.5 percent and precision only 49 percent. In the confusion matrix, melanoma is often mixed up with moles and benign keratosis. Dermatofibroma and vascular lesions have very few test images, 9 and 21, so those scores are not reliable."

Show the uncertainty section and chart.

> "To handle this I added uncertainty. The model runs 10 times with dropout switched on, and I measure how much the answers disagree, which is entropy. A case is flagged for review when entropy is high or the melanoma probability is at least 5 percent. On the test set, 31 percent of images get flagged. Accuracy is 93.5 percent on unflagged images and 61.6 percent on flagged ones, and the flag catches 73 percent of the model's mistakes. Counting a flag as a catch, melanoma sensitivity rises from about 61 percent to 87.7 percent. That is still not perfect, so this tool must never be used to reassure someone."

Show the Grad-CAM examples chart.

> "Finally, explainability. Grad-CAM heatmaps show where in the image the model looked to make its decision."

---

## Part 4: Deployment option, working application and API (6:30 to 9:30)

Switch to http://localhost:5173.

**Home screen**

> "Now the deployed prototype. This is the web interface. There is no login screen. The app keeps a private anonymous session in the browser, and the disclaimer is shown on every screen. The key limitations are shown right here on the main page."

**Take a photo**

Click Take a photo, allow the camera, click Capture photo.

> "I can take a photo directly with the camera. The circle helps centre the lesion."

**Upload**

Click Choose a different photo, pick a sample image, then click Analyse image.

> "Or I can upload a photo or drag and drop one. The server checks the file type, size, resolution and blur before the model runs."

**Result**

> "The result shows the most likely class, an uncertainty meter with the review threshold marked, the probability of every class, and the Grad-CAM heatmap next to the photo."

Analyse the second sample that triggers a review banner.

> "When the model is unsure, or sees a possible melanoma, it shows 'Review recommended' with the reason. The uncertainty badge and this banner use the same threshold, so they never disagree."

**Rejections**

Upload the blurry sample, then the text file (switch the file dialog filter to All files).

> "Bad input is rejected with a clear message, instead of producing a wrong answer."

**History**

Open the History tab and click View on an older case.

> "Every case is saved for this browser, and I can reopen the result and heatmap."

**Swagger UI**

Open http://localhost:8000/docs. Use /auth/register, click Authorize, then try /predict with an image.

> "This is the API interface, Swagger UI. The same prediction function is available to other applications. Here is the raw output: all 7 probabilities, entropy, the review flag, the heatmap and the processing time, in about 2 seconds."

**Deployment plan**

Show the Deployment plan section of the README (or docker-compose.yml).

> "For deployment, the repo includes Docker Compose with a PostgreSQL database, the API and the web app. The plan is to host the React interface on Vercel and the API on a separate service, because the model needs more memory than serverless functions allow. Before any real pilot it would need ethics approval, privacy safeguards and clinical validation."

---

## Closing (9:30 to 10:00)

Show the Limitations section of the README.

> "To be clear about the limits: this is a pre-screening prototype, not a diagnosis. The training data is mostly lighter skin and the model has not been tested on dark skin, so I make no claim that it works there. The next step is to evaluate on a dataset with skin-tone labels, such as Fitzpatrick17k, and report results by skin tone. Thank you."

---

## Timing check

| Part | Start | Length |
|---|---|---|
| Intro | 0:00 | 20 s |
| 1. Data | 0:20 | 2 min 20 s |
| 2. Architecture | 2:40 | 1 min 50 s |
| 3. Metrics | 4:30 | 2 min |
| 4. Deployment demo | 6:30 | 3 min |
| Closing | 9:30 | 30 s |

If you run long, shorten Part 1 (skip the body-site heatmap) and the history scene. If you run short, add the confusion matrix explanation or the Docker Compose file.

## Tips

- If something is slow on screen, say "the model is warming up". Better, warm it up before recording.
- If a result is surprising, say so once. It is honest and your supervisor will respect it: the model is sometimes overconfident, and the same image can flag differently between runs because the uncertainty method is random.
- Never say the app diagnoses, detects cancer, or works on all skin tones.
- Upload the finished video as unlisted on YouTube, or to Google Drive with link sharing on, then paste the link into the README at "Demo video".
