# Free online demo: Render + Supabase ($0)

The whole app (web app + API + model) runs as one Docker container on Render's free instance; the cases
live in a free Supabase PostgreSQL database.

## Why ONNX here

Render's free instance has 512 MB of RAM. With PyTorch loaded the API needs about 1 to 1.4 GB, so this
deployment runs the same EfficientNet-B3 through ONNX Runtime instead (`INFERENCE_BACKEND=onnx`).
Measured with the full app running under uvicorn: about 380 MB, about 0.1 s per screening on one CPU core.

Nothing about the model changes:

* `backend/scripts/export_onnx.py` exports the backbone up to `features[-1]`; the head (average pool,
  dropout, linear) runs in NumPy, so MC Dropout (10 passes) works exactly as before.
* Grad-CAM needs no PyTorch: after `features[-1]` the network is average pool + linear, so Grad-CAM's channel
  weights are the linear weights divided by H x W, and the heatmap equals CAM exactly.
* `backend/tests/test_onnx_backend.py` checks the probabilities against PyTorch (difference below 1e-5) and the
  heatmap PNG pixel by pixel (at most 4 of 255 levels, from rounding).

Render's free disk is wiped on every restart, so photos and heatmaps are stored in the database
(`IMAGE_STORE=db`, table `stored_files`, photos reduced to 1024 px).

## Steps

1. **Database (Supabase).** Project `skin-lesion-screening` (Frankfurt). Tables are created with Row Level
   Security on and no policies, so Supabase's public REST API cannot read them; the app connects as the
   database owner. In Supabase: *Connect* > *Session pooler* > copy the URI and put the database password in
   it. Use the pooler (IPv4), not the direct connection.
2. **Service (Render).** *New* > *Blueprint* > choose this repository. Render reads `render.yaml`, generates
   `SECRET_KEY`, and asks for `DATABASE_URL`: paste the Supabase URI from step 1.
3. Wait for the build (about 5 to 10 minutes the first time), then open the `onrender.com` address.
   `GET /health` should report `"model_loaded": true`.

## Things to know

* The free service sleeps after 15 minutes without traffic and takes about a minute to wake. Open the site
  a few minutes before a demo.
* A free Supabase project is paused after a week with little activity. Open the Supabase dashboard (or use
  the app) at least once a week.
* Run locally the same way: `INFERENCE_BACKEND=onnx IMAGE_STORE=db uvicorn app.main:app` with
  `pip install -r requirements-deploy.txt`.
