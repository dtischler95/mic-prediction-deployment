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
- [ ] Dockerfile
- [ ] Hugging Face Space
- [ ] GitHub Actions sync

## Local setup

```bash
pip install -r requirements.txt
python -m app.model                                   # quick CLI check
uvicorn app.main:app --reload --port 8000             # start the API
```

Then open http://127.0.0.1:8000/docs for the interactive Swagger UI.
