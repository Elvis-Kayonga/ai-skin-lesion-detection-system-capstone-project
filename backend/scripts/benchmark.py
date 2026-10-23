"""Performance benchmark of the real API with the real model.

It starts its own server (temporary database and storage, so real data is never touched), then measures:
  1. start-up time (process start until the model is loaded and /health answers)
  2. cold start: the first prediction after start-up
  3. warm latency over N sequential predictions (mean, p50, p95), client round-trip and server inference time
  4. concurrency: C clients at once (throughput, p95 latency) and whether /health still answers meanwhile
  5. memory (resident set size) of the server process
plus the hardware and software it ran on.

Run from the repo root:
    python backend/scripts/benchmark.py --label laptop-before-warmup
Results go to docs/results/performance_<label>.json
"""
import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import psutil

REPO = Path(__file__).resolve().parents[2]
BACKEND = REPO / "backend"
SAMPLE = REPO / "sample_images" / "ISIC_0030440.jpg"
RESULTS = REPO / "docs" / "results"


def percentile(values, q):
    values = sorted(values)
    k = (len(values) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (k - lo)


def summary(ms):
    return {"n": len(ms), "mean_ms": round(statistics.mean(ms)), "p50_ms": round(percentile(ms, 0.5)),
            "p95_ms": round(percentile(ms, 0.95)), "min_ms": round(min(ms)), "max_ms": round(max(ms))}


def environment():
    import torch
    import fastapi
    cpu = platform.processor()
    try:
        if os.name == "nt":
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            cpu = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
        elif Path("/proc/cpuinfo").exists():
            cpu = next(l.split(":", 1)[1].strip() for l in Path("/proc/cpuinfo").read_text().splitlines()
                       if l.startswith("model name"))
    except Exception:
        pass
    return {
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "cpu": cpu or platform.processor(),
        "logical_cores": psutil.cpu_count(),
        "ram_gb": round(psutil.virtual_memory().total / 1e9, 1),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none (CPU inference)",
        "python": platform.python_version(),
        "torch": torch.__version__,
        "fastapi": fastapi.__version__,
    }


class Server:
    """Starts uvicorn as a separate process with throw-away data folders."""

    def __init__(self, port):
        self.port = port
        self.url = f"http://127.0.0.1:{port}"
        self.tmp = Path(tempfile.mkdtemp(prefix="skin_bench_"))

    def start(self):
        env = {**os.environ,
               "SECRET_KEY": "benchmark-secret-key-that-is-long-enough-0123456789",
               "DATABASE_URL": f"sqlite:///{(self.tmp / 'bench.db').as_posix()}",
               "STORAGE_DIR": str(self.tmp / "storage")}
        t0 = time.perf_counter()
        self.proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(self.port)],
                                     cwd=BACKEND, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        while True:
            try:
                if httpx.get(self.url + "/health", timeout=2).json().get("model_loaded"):
                    return time.perf_counter() - t0
            except httpx.HTTPError:
                pass
            if self.proc.poll() is not None:
                raise RuntimeError("server exited during start-up")
            time.sleep(0.25)

    def _processes(self):
        # On Windows a virtual-environment python.exe is a small launcher that starts the real interpreter
        # as a child process, so memory must be summed over the whole process tree.
        parent = psutil.Process(self.proc.pid)
        return [parent] + parent.children(recursive=True)

    def rss_mb(self):
        return round(sum(p.memory_info().rss for p in self._processes()) / 1e6)

    def stop(self):
        for p in reversed(self._processes()):
            try:
                p.terminate()
            except psutil.NoSuchProcess:
                pass
        self.proc.wait(timeout=30)


def new_token(url):
    r = httpx.post(url + "/auth/register", json={"email": f"bench-{uuid.uuid4().hex[:8]}@test.local",
                                                 "password": "password123"}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def predict(url, token, data):
    t0 = time.perf_counter()
    r = httpx.post(url + "/predict", headers={"Authorization": f"Bearer {token}"},
                   files={"image": ("lesion.jpg", data, "image/jpeg")}, timeout=300)
    r.raise_for_status()
    return (time.perf_counter() - t0) * 1000, r.json()["inference_ms"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--warm", type=int, default=20, help="sequential warm predictions")
    ap.add_argument("--clients", type=int, default=4, help="concurrent clients")
    ap.add_argument("--per-client", type=int, default=3)
    ap.add_argument("--port", type=int, default=8020)
    args = ap.parse_args()

    data = SAMPLE.read_bytes()
    server = Server(args.port)
    out = {"label": args.label, "environment": environment(), "image": SAMPLE.name}
    try:
        out["startup_s"] = round(server.start(), 2)
        out["rss_after_startup_mb"] = server.rss_mb()
        token = new_token(server.url)

        cold_ms, cold_infer = predict(server.url, token, data)
        out["cold_first_prediction"] = {"round_trip_ms": round(cold_ms), "server_inference_ms": cold_infer}

        warm = [predict(server.url, token, data) for _ in range(args.warm)]
        out["warm_sequential"] = {"round_trip": summary([w[0] for w in warm]),
                                  "server_inference": summary([w[1] for w in warm])}
        out["rss_after_warm_mb"] = server.rss_mb()

        # Concurrency: several clients at once, while a separate thread keeps checking /health
        health_ms, stop = [], threading.Event()

        def probe():
            while not stop.is_set():
                t0 = time.perf_counter()
                httpx.get(server.url + "/health", timeout=30)
                health_ms.append((time.perf_counter() - t0) * 1000)
                time.sleep(0.2)

        tokens = [new_token(server.url) for _ in range(args.clients)]
        prober = threading.Thread(target=probe, daemon=True)
        prober.start()
        t0 = time.perf_counter()
        with ThreadPoolExecutor(args.clients) as pool:
            jobs = [pool.submit(predict, server.url, tokens[i % args.clients], data)
                    for i in range(args.clients * args.per_client)]
            lat = [j.result()[0] for j in jobs]
        wall = time.perf_counter() - t0
        stop.set()
        prober.join()
        out["concurrent"] = {"clients": args.clients, "requests": len(lat), "wall_s": round(wall, 2),
                             "throughput_req_per_s": round(len(lat) / wall, 2), "round_trip": summary(lat),
                             "health_during_load": summary(health_ms)}
        out["rss_peak_mb"] = server.rss_mb()
    finally:
        server.stop()

    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"performance_{args.label}.json"
    path.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    print("saved", path)


if __name__ == "__main__":
    main()
