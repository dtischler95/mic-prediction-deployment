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
Spaces expects); `-p 8000:7860` maps it to 8000 on the host.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The tests mock the model, so they download no weights and need no network. They run
in CI on every push and pull request, and a push to `master` is only synced to the
Hugging Face Space if they pass.
