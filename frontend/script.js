const API_BASE = "https://danielt95-mic-prediction-api.hf.space";

const resultSection = document.getElementById("result");
const resultSequence = document.getElementById("result-sequence");
const resultValue = document.getElementById("result-value");
const errorSection = document.getElementById("error");
const errorMessage = document.getElementById("error-message");

function showResult(sequence, value) {
  errorSection.hidden = true;
  resultSequence.textContent = sequence;
  resultValue.textContent = value;
  resultSection.hidden = false;
}

function showError(message) {
  resultSection.hidden = true;
  errorMessage.textContent = message;
  errorSection.hidden = false;
}

async function handleResponse(response) {
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail ?? "Request failed");
  }
  return data;
}

document.getElementById("sequence-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const sequence = document.getElementById("sequence").value;

  try {
    const response = await fetch(`${API_BASE}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sequence }),
    });
    const data = await handleResponse(response);
    showResult(data.sequence, data.predicted_log10_mic);
  } catch (err) {
    showError(err.message);
  }
});

document.getElementById("uniprot-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const accession = document.getElementById("accession").value;

  try {
    const response = await fetch(`${API_BASE}/predict-by-uniprot/${accession}`);
    const data = await handleResponse(response);
    showResult(data.sequence, data.predicted_log10_mic);
  } catch (err) {
    showError(err.message);
  }
});
