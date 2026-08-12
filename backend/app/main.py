"""
TakeMeter API — serves the fine-tuned DistilBERT classifier via ONNX Runtime.

Classifies a Reddit-style college-admissions comment into one of four
epistemic categories: evidence_based_advice, anecdotal_experience,
unsupported_take, emotional_reaction.

Deliberately avoids torch/transformers at runtime — inference uses
onnxruntime (CPU) + the tokenizers library directly, which keeps the
memory footprint small enough for Render's free tier.
"""

import json
import os
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from tokenizers import Tokenizer

MODEL_DIR = Path(__file__).parent / "model"
MAX_LENGTH = 256  # comments are short; keeps inference fast and light

app = FastAPI(
    title="TakeMeter API",
    description="Classifies Reddit college-admissions comments by epistemic type.",
    version="1.0.0",
)

# CORS: allow the deployed frontend + local dev. Set FRONTEND_ORIGIN on Render.
frontend_origin = os.environ.get("FRONTEND_ORIGIN", "")
allowed_origins = ["http://localhost:5173", "http://localhost:3000"]
if frontend_origin:
    allowed_origins.append(frontend_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Model loading (once, at startup) ---------------------------------------

_session: ort.InferenceSession | None = None
_tokenizer: Tokenizer | None = None
_id2label: dict[int, str] = {}

LABEL_DESCRIPTIONS = {
    "evidence_based_advice": "Backed by something that would still be true with the confident framing stripped away — a policy, a statistic, a documented rule.",
    "anecdotal_experience": "The writer recounting their own story, without directing advice at the reader.",
    "unsupported_take": "A confident claim, prediction, or ranking that doesn't survive having the confident tone removed.",
    "emotional_reaction": "The writer expressing a feeling about their own process, with little reportable detail.",
}


def load_model() -> None:
    global _session, _tokenizer, _id2label

    so = ort.SessionOptions()
    so.intra_op_num_threads = 1  # keep it light on a shared free-tier CPU
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

    onnx_path = MODEL_DIR / "model_quantized.onnx"
    _session = ort.InferenceSession(
        str(onnx_path), sess_options=so, providers=["CPUExecutionProvider"]
    )

    _tokenizer = Tokenizer.from_file(str(MODEL_DIR / "tokenizer.json"))

    with open(MODEL_DIR / "config.json") as f:
        config = json.load(f)
    _id2label = {int(k): v for k, v in config["id2label"].items()}


@app.on_event("startup")
def on_startup() -> None:
    load_model()


# --- Schemas ------------------------------------------------------------

class ClassifyRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=3000)


class LabelScore(BaseModel):
    label: str
    description: str
    probability: float


class ClassifyResponse(BaseModel):
    predicted_label: str
    scores: list[LabelScore]
    inference_ms: float


# --- Routes ---------------------------------------------------------------

@app.get("/")
def root():
    return {"status": "ok", "service": "takemeter-api"}


@app.get("/api/health")
def health():
    return {"status": "ok", "model_loaded": _session is not None}


@app.post("/api/classify", response_model=ClassifyResponse)
def classify(req: ClassifyRequest):
    if _session is None or _tokenizer is None:
        raise HTTPException(status_code=503, detail="Model is still loading, try again shortly.")

    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text must not be empty.")

    start = time.perf_counter()

    _tokenizer.enable_truncation(max_length=MAX_LENGTH)
    encoding = _tokenizer.encode(text)

    input_ids = np.array([encoding.ids], dtype=np.int64)
    attention_mask = np.array([encoding.attention_mask], dtype=np.int64)

    ort_inputs = {"input_ids": input_ids, "attention_mask": attention_mask}
    input_names = {i.name for i in _session.get_inputs()}
    ort_inputs = {k: v for k, v in ort_inputs.items() if k in input_names}

    logits = _session.run(None, ort_inputs)[0][0]

    exp = np.exp(logits - np.max(logits))
    probs = exp / exp.sum()

    elapsed_ms = (time.perf_counter() - start) * 1000

    scores = [
        LabelScore(
            label=_id2label[i],
            description=LABEL_DESCRIPTIONS.get(_id2label[i], ""),
            probability=round(float(p), 4),
        )
        for i, p in enumerate(probs)
    ]
    scores.sort(key=lambda s: s.probability, reverse=True)

    return ClassifyResponse(
        predicted_label=scores[0].label,
        scores=scores,
        inference_ms=round(elapsed_ms, 2),
    )
