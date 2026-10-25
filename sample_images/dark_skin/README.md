# Dark-skin test photos (Fitzpatrick IV to VI)

**Decision-support prototype only. Not a diagnosis. Consult a qualified clinician.**

These 29 clinical photos are the **locked test set** from Phase 4b (`notebooks/phase4b_tune_dark_skin.ipynb`). They were put aside before any tuning, so the deployed model (`efficientnet_b3-v1-darkskin`) never trained on them. They are here so anyone can try the app on dark skin.

| File | What it holds |
|---|---|
| `<class>_fitz<type>_<id>.jpg` | The photo. The name gives the true class (bcc, mel or df) and the Fitzpatrick skin type (4, 5 or 6). |
| `labels.csv` | True class, Fitzpatrick type, original Fitzpatrick17k label and source URL for every photo |
| `app_results.json` | What the running app answered for each photo (laptop CPU, 25 October 2026) |

Contents: 17 basal cell carcinoma, 11 melanoma, 1 dermatofibroma. Skin type IV: 18, V: 6, VI: 5. There are **no benign moles** in this set, because none of the dark-skin mole photos could still be downloaded. So these photos only show how the app handles cancers, not harmless spots.

## Results in the running app

| Measure | Result |
|---|---|
| Correct lesion type | 23 of 29 (79%) |
| Cancers named correctly or flagged for review | 27 of 28 |
| Skin types V and VI only, correct | 10 of 11 |

The Phase 4b notebook measured 24 of 29 and 28 of 28 on the same photos. The small difference is most likely from saving the photos again as JPEG and from small CPU and GPU number differences. One cancer was missed in the app: `bcc_fitz4_185942f8.jpg` was called dermatofibroma without a review flag.

Twenty-nine photos are far too few to show that the model works on dark skin. See the main README, Sections 6 and 12.

## Source and credit

- Photo list and skin-type labels: **Fitzpatrick17k**, Groh M, Harris C, Soenksen L, et al. "Evaluating Deep Neural Networks Trained on Clinical Images in Dermatology with the Fitzpatrick 17k Dataset." CVPR Workshops, 2021. Annotations licensed CC BY-NC-SA 3.0.
- Photos: **Atlas Dermatologico** (atlasdermatologico.com.br). The original URL of each photo is in `labels.csv`. The copyright of the photos stays with their owners.
- Use for non-commercial research and education only. If you own one of these photos and want it removed, please open an issue on the repository.
