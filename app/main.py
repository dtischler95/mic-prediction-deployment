"""FastAPI service exposing the Acinetobacter baumannii MIC regression model."""

import anyio
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError, field_validator

from app.fasta import parse_input
from app.model import MAX_LENGTH, load_model, predict, predict_batch

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
MAX_BATCH = 200


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


class BatchRequest(BaseModel):
    """Request body for /predict-batch: raw text, either one sequence per line or FASTA."""

    text: str


class BatchItem(BaseModel):
    """One row of a batch result: prediction on success, error string on failure."""

    id: str | None = None
    sequence: str
    predicted_log10_mic: float | None = None
    error: str | None = None


class BatchResponse(BaseModel):
    """Response body for /predict-batch: one item per input record, order preserved."""

    results: list[BatchItem]


def _first_error(exc: ValidationError) -> str:
    """Extract a concise message from a sequence ValidationError."""
    return exc.errors()[0]["msg"].removeprefix("Value error, ")


@app.get("/")
def root():
    """Redirect the bare URL to the web frontend."""
    return RedirectResponse(url="/ui/")


@app.post("/predict", response_model=PredictionResponse)
def predict_endpoint(request: PredictionRequest) -> PredictionResponse:
    """Predict the log10 MIC for a peptide sequence given directly in the request body."""
    value = predict(request.sequence, model, tokenizer)
    return PredictionResponse(sequence=request.sequence, predicted_log10_mic=value)


@app.post("/predict-batch", response_model=BatchResponse)
def predict_batch_endpoint(request: BatchRequest) -> BatchResponse:
    """Predict the log10 MIC for many sequences at once (plain lines or FASTA).

    Invalid sequences are not rejected wholesale: each gets an ``error`` while the
    valid ones are still scored, in a single batched forward pass.
    """
    records = parse_input(request.text)
    if not records:
        raise HTTPException(status_code=422, detail="no sequences found in input")
    if len(records) > MAX_BATCH:
        raise HTTPException(
            status_code=422,
            detail=f"too many sequences ({len(records)} > {MAX_BATCH})",
        )

    items: list[BatchItem] = []
    valid_indices: list[int] = []
    valid_sequences: list[str] = []

    for label, raw_sequence in records:
        try:
            validated = PredictionRequest(sequence=raw_sequence)
        except ValidationError as exc:
            items.append(BatchItem(id=label, sequence=raw_sequence, error=_first_error(exc)))
            continue
        valid_indices.append(len(items))
        valid_sequences.append(validated.sequence)
        items.append(BatchItem(id=label, sequence=validated.sequence))

    for index, value in zip(valid_indices, predict_batch(valid_sequences, model, tokenizer)):
        items[index].predicted_log10_mic = value

    return BatchResponse(results=items)


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
