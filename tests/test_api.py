"""API tests via TestClient with a mocked model (see conftest.py)."""


def test_root_redirects_to_ui(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (307, 308)
    assert response.headers["location"] == "/ui/"


def test_frontend_is_served(client):
    response = client.get("/ui/")
    assert response.status_code == 200
    assert "<html" in response.text.lower()


def test_single_predict(client):
    response = client.post("/predict", json={"sequence": "GWKRKRFG"})
    assert response.status_code == 200
    assert response.json() == {"sequence": "GWKRKRFG", "predicted_log10_mic": 1.5}


def test_batch_fasta_marks_invalid_per_line(client):
    fasta = ">good1\nGWKRKRFG\n>bad_char\nGWXRKR\n>empty\n>good2\nILPWKWPWWPWRR"
    response = client.post("/predict-batch", json={"text": fasta})
    assert response.status_code == 200

    results = response.json()["results"]
    assert [row["id"] for row in results] == ["good1", "bad_char", "empty", "good2"]

    # Valid rows: prediction present, no error.
    assert results[0]["error"] is None and results[0]["predicted_log10_mic"] == 1.5
    assert results[3]["error"] is None and results[3]["predicted_log10_mic"] == 1.5

    # Invalid rows: error present, no prediction - but the batch is not rejected.
    assert "X" in results[1]["error"] and results[1]["predicted_log10_mic"] is None
    assert results[2]["error"] is not None and results[2]["predicted_log10_mic"] is None


def test_batch_plain_mode_has_no_ids(client):
    response = client.post("/predict-batch", json={"text": "GWKRKRFG\nILPWKWPWWPWRR"})
    results = response.json()["results"]
    assert [row["id"] for row in results] == [None, None]
    assert all(row["error"] is None for row in results)


def test_batch_empty_input_returns_422(client):
    response = client.post("/predict-batch", json={"text": "   "})
    assert response.status_code == 422


def test_batch_over_cap_returns_422(client):
    response = client.post("/predict-batch", json={"text": "\n".join(["GWKR"] * 201)})
    assert response.status_code == 422
