"""FastAPI service exposing the Acinetobacter baumannii MIC regression model."""

import anyio
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError, field_validator

from app.model import MAX_LENGTH, load_model, predict

app = FastAPI(title="MIC Prediction API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.mount("/ui", StaticFiles(directory="frontend", html=True), name="frontend")
model, tokenizer = load_model()

VALID_AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")


class PredictionRequest(BaseModel):
    """Request body for /predict: a single peptide sequence."""

    sequence: str

    @field_validator("sequence")
    @classmethod
    def validate_sequence(cls, value: str) -> str:
        """Normalize and validate the sequence (non-empty, <=MAX_LENGTH residues, valid amino acids only)."""
        value = value.strip().upper()
        if not value:
            raise ValueError("sequence must not be empty")
        if len(value) > MAX_LENGTH:
            raise ValueError(f"sequence too long ({len(value)} > {MAX_LENGTH} residues)")
        invalid = set(value) - VALID_AMINO_ACIDS
        if invalid:
            raise ValueError(f"invalid amino acid character(s): {', '.join(sorted(invalid))}")
        return value


class PredictionResponse(BaseModel):
    """Response body: the (normalized) sequence and its predicted log10 MIC."""

    sequence: str
    predicted_log10_mic: float


@app.get("/")
def root():
    """Health check / entry point pointing to the Swagger docs."""
    return {"message": "MIC prediction API. See /docs for usage."}


@app.post("/predict", response_model=PredictionResponse)
def predict_endpoint(request: PredictionRequest) -> PredictionResponse:
    """Predict the log10 MIC for a peptide sequence given directly in the request body."""
    value = predict(request.sequence, model, tokenizer)
    return PredictionResponse(sequence=request.sequence, predicted_log10_mic=value)


@app.get("/predict-by-uniprot/{accession}", response_model=PredictionResponse)
async def predict_by_uniprot(accession: str) -> PredictionResponse:
    """Fetch a sequence from UniProt by accession ID and predict its log10 MIC."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://rest.uniprot.org/uniprotkb/{accession}.fasta")

    if response.status_code != 200:
        raise HTTPException(status_code=404, detail=f"UniProt accession '{accession}' not found")

    sequence = "".join(response.text.splitlines()[1:])
    try:
        validated = PredictionRequest(sequence=sequence)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    value = await anyio.to_thread.run_sync(predict, validated.sequence, model, tokenizer)
    return PredictionResponse(sequence=validated.sequence, predicted_log10_mic=value)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
