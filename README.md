---
title: MIC Prediction API
emoji: 🧬
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

[![Hugging Face Space](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Space-blue)](https://huggingface.co/spaces/danielt95/mic-prediction-api)

# MIC Prediction Deployment

A small deployment project: a fine-tuned [ProtBERT](https://huggingface.co/Rostlab/prot_bert_bfd)
model that predicts the minimum inhibitory concentration (MIC, \[µM\]) of a peptide
sequence against *Acinetobacter baumannii*, served via a FastAPI API and deployed as a
Hugging Face Space (Docker), with GitHub Actions syncing pushes to the Space.

Model weights: [danielt95/acinetobacter-baumannii-mic-bert](https://huggingface.co/danielt95/acinetobacter-baumannii-mic-bert)
(fine-tuned as part of my [peptideTransformer](https://github.com/dtischler95/peptideTransformer) Master's thesis project).

## About the model

A fine-tuned [ProtBERT](https://huggingface.co/Rostlab/prot_bert_bfd) model that
**estimates how strongly an antimicrobial peptide inhibits _Acinetobacter baumannii_**,
reported as MIC (minimum inhibitory concentration, µM).

- **Input:** one peptide, the 20 standard amino acids, ≤ 36 residues.
- **Output:** predicted `log10(MIC)`, **lower means more potent** (the UI shows µM).
- **Data-first, not SOTA-chasing:** this comes out of the
  [peptideTransformer](https://github.com/dtischler95/peptideTransformer) thesis on data
  quality, whose central finding is that AMP activity prediction is **capped by
  experimental measurement noise (~0.4 log₁₀ MIC, a ~3-fold range), not by model
  architecture**. It's trained on de-duplicated data with sequence-level splits (no
  peptide in both train and test).
- **Use it for:** ranking and triaging peptide candidates, not as a replacement for lab testing.

**Test-set performance** (~1710 _A. baumannii_ peptides, sequence input):

| Metric | Test | Train |
|---|---|---|
| R² | 0.45 | 0.85 |
| RMSE (log₁₀ MIC) | ~0.55 | ~0.28 |

An RMSE of ~0.55 log₁₀ sits close to that measurement-noise floor, about as good as this
data allows. <sub>The point isn't a high R². It's an R² you can trust.</sub>

## Live demo

The web frontend is at https://danielt95-mic-prediction-api.hf.space/ . The raw API's Swagger UI is at
https://danielt95-mic-prediction-api.hf.space/docs

## Endpoints

- `GET /` - redirects to the web frontend at `/ui/`.
- `POST /predict` - predict the MIC for a peptide sequence given in the request body.
  Sequence is validated: only the 20 standard amino acids, non-empty, max 36 residues.
- `POST /predict-batch` - predict the MIC for many sequences at once. The request
  body is raw `text`, either one sequence per line or FASTA (headers become the
  result `id`). Up to 200 sequences, scored in a single forward pass. Invalid
  sequences are not rejected wholesale - each gets an `error` while the valid ones
  are still scored.
- `GET /predict-by-uniprot/{accession}` - fetch a sequence from UniProt by accession ID
  (e.g. `P01308`) and predict its MIC. Same validation as `/predict` applies to the
  fetched sequence.

## Local setup

```bash
pip install -r requirements.txt
python -m app.model                                   # quick CLI check
uvicorn app.main:app --reload --port 8000             # start the API
```

Then open http://127.0.0.1:8000/ for the web frontend (or
http://127.0.0.1:8000/docs for the interactive Swagger UI).

## Docker

```bash
docker build -t mic-prediction-api .
docker run -d -p 8000:7860 mic-prediction-api
```

Then open http://127.0.0.1:8000/ for the web frontend (or `/docs` for the Swagger
UI) as above. The container listens on port 7860 internally (the port Hugging Face
Spaces expects), `-p 8000:7860` maps it to 8000 on the host.

## Deploy your own model

`app/model.py` is the only model-specific file, and the model is chosen by the
`MODEL_REPO` environment variable (defaulting to the A. baumannii model above). Swapping
in another [peptideTransformer](https://github.com/dtischler95/peptideTransformer) model needs **no code change**:

- **Locally:** `MODEL_REPO=youruser/your-model uvicorn app.main:app --port 8000`
- **On a Hugging Face Space:** add a `MODEL_REPO` *Variable* (Settings → Variables and
  secrets) and restart. With no variable set, the default model is used, so an existing
  Space keeps working unchanged.

A model is drop-in compatible if it matches this architecture: a BERT/ProtBERT backbone +
`LayerNorm` + `Linear(hidden, 1)` regression head (loaded with `strict=True`),
space-separated residue tokenization, output = `log10(MIC [µM])`. Models from
[peptideTransformer](https://github.com/dtischler95/peptideTransformer) fit by
construction. Arbitrary third-party models need code changes, but `model.py` is the
single place to make them.

The A. baumannii model ships as a working reference. Other organism models aren't bundled
(model weights live on the HF Hub, not in this repo).

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The tests mock the model, so they download no weights and need no network. They run
in CI on every push and pull request, and a push to `master` is only synced to the
Hugging Face Space if they pass.
