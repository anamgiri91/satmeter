# TakeMeter — full-stack

A deployable version of the [TakeMeter](../README.md) research project: a fine-tuned
DistilBERT model that classifies Reddit college-admissions comments by *epistemic type*
(evidence-based advice, anecdotal experience, unsupported take, or emotional reaction).

```
satmeter-app/
├── backend/      FastAPI + ONNX Runtime inference API
├── frontend/     React (Vite) UI
└── render.yaml   One-click Render Blueprint (both services)
```

## Why ONNX instead of PyTorch

The original checkpoint is a 256MB PyTorch `.safetensors` file. Loading it with
`transformers` + `torch` pulls in ~700MB of dependencies and the runtime memory
needed to hold the model can OOM on Render's free tier (512MB RAM) — the same
failure mode as the PyTorch-loading issue on Bobcat Advisor.

Instead, this backend:
1. Converts the model to ONNX (`optimum`), then dynamically quantizes it to int8
   — shrinks the weights from 256MB → 67MB with no meaningful accuracy loss
   (verified predictions match the original PyTorch model on the same inputs).
2. Serves it with `onnxruntime` (CPU) + the standalone `tokenizers` library —
   **no `torch` or `transformers` at runtime at all.** The deployed backend's
   only ML dependency is `onnxruntime`.

The conversion script isn't checked in (it's a one-time step) — see below if you
need to re-run it after retraining the model.

## Local development

**Backend:**
```bash
cd backend
pip install -r requirements.txt --break-system-packages   # or use a venv
uvicorn app.main:app --reload --port 8000
```
Visit `http://localhost:8000/api/health` to confirm the model loaded.

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env       # VITE_API_URL=http://localhost:8000
npm run dev
```
Visit `http://localhost:5173`.

## Deploying to Render

### Option A — Blueprint (recommended)
1. Push this folder to a GitHub repo.
2. In Render: **New → Blueprint**, point it at the repo. It reads `render.yaml`
   and creates both services (`takemeter-api`, `takemeter-web`) automatically.
3. **After the first deploy**, Render assigns final URLs (e.g.
   `takemeter-api-xyz1.onrender.com` if `takemeter-api` was taken). Update:
   - `takemeter-web`'s `VITE_API_URL` env var → the actual backend URL, then
     trigger a manual redeploy of the frontend (Vite bakes this in at build time).
   - `takemeter-api`'s `FRONTEND_ORIGIN` env var → the actual frontend URL,
     then redeploy the backend (this is what CORS uses).

### Option B — Manual (two separate services)
**Backend** — New Web Service, root directory `backend`:
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Env var: `FRONTEND_ORIGIN=<your frontend URL>`

**Frontend** — New Static Site, root directory `frontend`:
- Build command: `npm install && npm run build`
- Publish directory: `dist`
- Env var: `VITE_API_URL=<your backend URL>`
- Add a rewrite rule `/* → /index.html` (client-side routing isn't used yet,
  but this avoids 404s on refresh if you add routes later)

### A note on the free tier
Render's free web services spin down after 15 minutes of inactivity and take
~30–50 seconds to wake back up on the next request. The frontend already
shows a friendlier message than a raw network error if the first classify
request times out while the backend is waking up.

## Re-converting the model (if you retrain)

```bash
pip install torch transformers "optimum[onnxruntime]" onnxruntime --break-system-packages

python3 - <<'EOF'
from optimum.onnxruntime import ORTModelForSequenceClassification, ORTQuantizer
from optimum.onnxruntime.configuration import AutoQuantizationConfig
from transformers import AutoTokenizer

model = ORTModelForSequenceClassification.from_pretrained("takemeter-finetuned", export=True)
model.save_pretrained("onnx_model")
AutoTokenizer.from_pretrained("takemeter-finetuned").save_pretrained("onnx_model")

quantizer = ORTQuantizer.from_pretrained(model)
qconfig = AutoQuantizationConfig.avx2(is_static=False, per_channel=False)
quantizer.quantize(save_dir="onnx_model_quantized", quantization_config=qconfig)
EOF
```
Then copy `model_quantized.onnx`, `config.json`, `tokenizer.json`,
`tokenizer_config.json`, `special_tokens_map.json`, and `vocab.txt` from
`onnx_model_quantized/` into `backend/app/model/`.
