# Usability test guide (System Usability Scale)

**Goal (from my proposal):** a mean System Usability Scale (SUS) score of **65 or higher** from a small group in Kigali (peers, supervisors or health-science students, not practising clinicians).

**Ethics and privacy:** participants use only the sample images in `sample_images/`. No real patient photos, no names or personal data in the results. Participation is voluntary and anyone can stop at any time.

## Before each session (2 minutes)

1. Start the app (`uvicorn` in `backend/`, `npm run dev` in `frontend/`) and open http://localhost:5173 in a fresh browser window.
2. Put the files from `sample_images/` on the desktop.
3. Tell the participant: "This is a prototype that helps a health worker decide which skin lesion photos need a specialist. It is not a diagnosis tool. I am testing the app, not you. Please think aloud."

## Tasks (about 8 minutes, do not help unless they are stuck for more than a minute)

| # | Task given to the participant | Success means |
|---|---|---|
| 1 | "Analyse the photo `ISIC_0030440.jpg`." | Result card appears |
| 2 | "What does the app think this lesion is, and how sure is it?" | Names the top class and reads the uncertainty level |
| 3 | "Does the app recommend a clinician review? Why?" | Finds the banner and reads the reason (or says there is none) |
| 4 | "Which part of the photo did the model look at?" | Points to the heatmap |
| 5 | "Try the photo `blurry_example_will_be_rejected.jpg`." | Reads the rejection message |
| 6 | "Find the photo you analysed first." | Opens History and clicks View |
| 7 | "Find out what this app cannot do." | Opens Limitations |
| 8 (optional) | "Take a photo with the camera of any object." | Captures and analyses, or reads a clear message |

Record for each task: completed yes/no, time in seconds, and any comment. Use `sus_responses_template.csv`.

## The questionnaire (right after the tasks)

Each statement is answered from 1 (strongly disagree) to 5 (strongly agree). These are the standard SUS statements (Brooke, 1996), with "system" meaning this app.

1. I think that I would like to use this system frequently.
2. I found the system unnecessarily complex.
3. I thought the system was easy to use.
4. I think that I would need the support of a technical person to be able to use this system.
5. I found the various functions in this system were well integrated.
6. I thought there was too much inconsistency in this system.
7. I would imagine that most people would learn to use this system very quickly.
8. I found the system very cumbersome to use.
9. I felt very confident using the system.
10. I needed to learn a lot of things before I could get going with this system.

Then ask one open question: "What was the most confusing part, and what would you change?"

## Scoring

Fill in `sus_responses.csv` (copy of the template, one row per participant, answers q1 to q10), then run from the repo root:

```
python backend/scripts/sus_score.py docs/usability/sus_responses.csv
```

How SUS is scored: for odd statements the score is (answer - 1), for even statements it is (5 - answer); the sum is multiplied by 2.5, giving 0 to 100 per person. A score of 68 is the commonly used average; my proposal target is 65.
