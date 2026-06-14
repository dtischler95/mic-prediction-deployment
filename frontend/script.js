const API_BASE = "";

const resultSection = document.getElementById("result");
const resultSequence = document.getElementById("result-sequence");
const resultMic = document.getElementById("result-mic");
const errorSection = document.getElementById("error");
const errorMessage = document.getElementById("error-message");

const batchResult = document.getElementById("batch-result");
const batchTbody = document.getElementById("batch-tbody");
const batchText = document.getElementById("batch-text");
const fileInput = document.getElementById("fasta-file");
const fileName = document.getElementById("file-name");

let lastBatchResults = [];

function micFromLog10(value) {
  return (10 ** value).toFixed(3);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

function showResult(sequence, value) {
  errorSection.hidden = true;
  batchResult.hidden = true;
  resultSequence.textContent = sequence;
  resultMic.textContent = micFromLog10(value);
  resultSection.hidden = false;
}

function showError(message) {
  resultSection.hidden = true;
  batchResult.hidden = true;
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

fileInput.addEventListener("change", async () => {
  const file = fileInput.files[0];
  if (!file) return;
  batchText.value = await file.text();
  fileName.textContent = file.name;
});

document.getElementById("batch-form").addEventListener("submit", async (event) => {
  event.preventDefault();

  try {
    const response = await fetch(`${API_BASE}/predict-batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: batchText.value }),
    });
    const data = await handleResponse(response);
    renderBatch(data.results);
  } catch (err) {
    showError(err.message);
  }
});

function renderBatch(results) {
  lastBatchResults = results;
  batchTbody.innerHTML = results.map((row) => {
    const mic = row.error
      ? `⚠ ${escapeHtml(row.error)}`
      : escapeHtml(micFromLog10(row.predicted_log10_mic));
    return `
      <tr class="${row.error ? "bg-red-50" : "border-t border-slate-100"}">
        <td class="px-3 py-2 text-slate-700 break-all">${escapeHtml(row.id ?? "")}</td>
        <td class="px-3 py-2 font-mono text-slate-600 break-all">${escapeHtml(row.sequence)}</td>
        <td class="px-3 py-2 text-right whitespace-nowrap ${row.error ? "text-red-600" : "text-emerald-700 font-semibold"}">${mic}</td>
      </tr>`;
  }).join("");

  resultSection.hidden = true;
  errorSection.hidden = true;
  batchResult.hidden = false;
}

function csvCell(value) {
  const text = String(value);
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

document.getElementById("download-csv").addEventListener("click", () => {
  if (!lastBatchResults.length) return;

  const header = ["id", "sequence", "predicted_log10_mic", "predicted_mic_uM", "error"];
  const rows = lastBatchResults.map((row) => [
    row.id ?? "",
    row.sequence,
    row.error == null ? row.predicted_log10_mic : "",
    row.error == null ? 10 ** row.predicted_log10_mic : "",
    row.error ?? "",
  ].map(csvCell).join(","));

  const csv = [header.join(","), ...rows].join("\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "mic-predictions.csv";
  link.click();
  URL.revokeObjectURL(url);
});
