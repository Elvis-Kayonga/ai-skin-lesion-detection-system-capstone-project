---
title: Skin Lesion Pre-Screening
colorFrom: green
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
license: cc-by-nc-4.0
short_description: Explainable, uncertainty-aware skin lesion pre-screening
---

# Skin Lesion Pre-Screening (capstone prototype)

**Decision-support prototype only. Not a diagnosis. Consult a qualified clinician.**

Upload or take a photo of a skin lesion. The app shows the most likely of 7 lesion classes, how unsure the model is, a "Review recommended" warning when it is unsure or sees a possible melanoma, and a heatmap of where the model looked.

- Do not upload photos of real patients. Use test images only.
- The model learned mostly from lighter-skinned patients and was fine-tuned on a small set of dark-skin photos. It is **not validated on dark skin**.
- Cases are stored only until the Space restarts.

Source code, results and limitations: https://github.com/Elvis-Kayonga/ai-skin-lesion-detection-system-capstone-project

Author: Kayonga Elvis, African Leadership University (BSc Software Engineering capstone).
