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
model that predicts the minimum inhibitory concentration (log₁₀ MIC, µM) of a peptide
sequence against *Acinetobacter baumannii*, served via a FastAPI API and deployed as a
Hugging Face Space (Docker), with GitHub Actions syncing pushes to the Space.

Model weights: [danielt95/acinetobacter-baumannii-mic-bert](https://huggingface.co/danielt95/acinetobacter-baumannii-mic-bert)
(fine-tuned as part of my [peptideTransformer](https://github.com/) Master's thesis project).

## Status

- [x] Inference code (`app/model.py`)
- [x] FastAPI service (`app/main.py`)
- [x] Dockerfile
- [ ] Hugging Face Space
- [ ] GitHub Actions sync

## Endpoints

- `GET /` - health check.
- `POST /predict` - predict the log10 MIC for a peptide sequence given in the request body.
  Sequence is validated: only the 20 standard amino acids, non-empty, max 36 residues.
- `GET /predict-by-uniprot/{accession}` - fetch a sequence from UniProt by accession ID
  (e.g. `P01308`) and predict its log10 MIC. Same validation as `/predict` applies to the
  fetched sequence.

## Local setup

```bash
pip install -r requirements.txt
python -m app.model                                   # quick CLI check
uvicorn app.main:app --reload --port 8000             # start the API
```

Then open http://127.0.0.1:8000/docs for the interactive Swagger UI.

## Docker

```bash
docker build -t mic-prediction-api .
docker run -d -p 8000:7860 mic-prediction-api
```

Then open http://127.0.0.1:8000/docs as above. The container listens on port 7860
internally (the port Hugging Face Spaces expects); `-p 8000:7860` maps it to 8000
on the host.
