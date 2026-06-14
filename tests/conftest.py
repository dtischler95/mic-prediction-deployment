"""Shared fixtures for the test suite.

The API tests use the ``client`` fixture, which mocks the model loader and the
predictors *before* importing the app - so the tests download no weights and need
no network, and predictions are deterministic. The parser tests in test_fasta.py
don't use this fixture and run without torch/transformers installed.
"""

import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def client():
    """A FastAPI TestClient backed by a mocked model (no weights, no network)."""
    # Run from the repo root so app.main's StaticFiles(directory="frontend") resolves.
    os.chdir(Path(__file__).resolve().parents[1])

    # Patch the heavy bits before importing the app, so importing it loads no
    # weights and predictions are deterministic.
    import app.model as model_module

    model_module.load_model = lambda: ("model", "tokenizer")
    model_module.predict = lambda sequence, model, tokenizer: 1.5
    model_module.predict_batch = lambda sequences, model, tokenizer: [1.5] * len(sequences)

    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
