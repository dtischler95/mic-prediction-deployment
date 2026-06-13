"""FastAPI service exposing the Acinetobacter baumannii MIC regression model."""

from fastapi import FastAPI
from pydantic import BaseModel, field_validator

from app.model import load_model, predict

app = FastAPI(title="MIC Prediction API")
model, tokenizer = load_model()

VALID_AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")


class PredictionRequest(BaseModel):
    sequence: str

    @field_validator("sequence")
    @classmethod
    def validate_sequence(cls, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise ValueError("sequence must not be empty")
        invalid = set(value) - VALID_AMINO_ACIDS
        if invalid:
            raise ValueError(f"invalid amino acid character(s): {', '.join(sorted(invalid))}")
        return value


class PredictionResponse(BaseModel):
    sequence: str
    predicted_log10_mic: float


@app.get("/")
def root():
    return {"message": "MIC prediction API. See /docs for usage."}


@app.post("/predict", response_model=PredictionResponse)
def predict_endpoint(request: PredictionRequest) -> PredictionResponse:
    value = predict(request.sequence, model, tokenizer)
    return PredictionResponse(sequence=request.sequence, predicted_log10_mic=value)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
