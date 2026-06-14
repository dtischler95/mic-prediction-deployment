"""
Inference code for the Acinetobacter baumannii MIC regression model.

Loads a fine-tuned ProtBERT checkpoint (config + weights + tokenizer) from
https://huggingface.co/danielt95/acinetobacter-baumannii-mic-bert and exposes a
simple predict(sequence) -> float function (predicted log10 MIC).

This is a simplified, inference-only re-implementation of PeptideBertForRegression
from the peptideTransformer thesis repo: the backbone is built directly from config
(no separate ProtBERT-BFD download) and all weights come from the fine-tuned checkpoint.
"""

import torch
import torch.nn as nn
from transformers import BertConfig, BertModel, BertTokenizer
from huggingface_hub import hf_hub_download
from safetensors.torch import load_file

MODEL_REPO = "danielt95/acinetobacter-baumannii-mic-bert"
MAX_LENGTH = 36


class PeptideBertForRegression(nn.Module):
    """ProtBERT backbone with a LayerNorm + linear regression head on the pooled [CLS] output."""

    def __init__(self, config: BertConfig):
        super().__init__()
        self.bert = BertModel(config)
        self.norm = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
        self.dropout = nn.Dropout(0.15)
        self.regression = nn.Linear(config.hidden_size, 1)

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask, return_dict=True)
        pooled_output = outputs.pooler_output
        pooled_output = self.norm(pooled_output)
        pooled_output = self.dropout(pooled_output)
        return self.regression(pooled_output)


def load_model() -> tuple[PeptideBertForRegression, BertTokenizer]:
    config = BertConfig.from_pretrained(MODEL_REPO)
    model = PeptideBertForRegression(config)

    weights_path = hf_hub_download(repo_id=MODEL_REPO, filename="model.safetensors")
    state_dict = load_file(weights_path)
    model.load_state_dict(state_dict, strict=True)
    model.eval()

    tokenizer = BertTokenizer.from_pretrained(MODEL_REPO, do_lower_case=False)
    return model, tokenizer


@torch.no_grad()
def predict(sequence: str, model: PeptideBertForRegression, tokenizer: BertTokenizer) -> float:
    """Predict log10(MIC) [µM] against Acinetobacter baumannii for a peptide sequence."""
    spaced = " ".join(sequence.strip().upper())
    encoding = tokenizer(spaced, padding="max_length", truncation=True, max_length=MAX_LENGTH, return_tensors="pt")
    output = model(input_ids=encoding["input_ids"], attention_mask=encoding["attention_mask"])
    return output.item()


@torch.no_grad()
def predict_batch(sequences: list[str], model: PeptideBertForRegression, tokenizer: BertTokenizer) -> list[float]:
    """Predict log10(MIC) for a list of sequences in a single forward pass."""
    if not sequences:
        return []
    spaced = [" ".join(s.strip().upper()) for s in sequences]
    encoding = tokenizer(spaced, padding="max_length", truncation=True, max_length=MAX_LENGTH, return_tensors="pt")
    output = model(input_ids=encoding["input_ids"], attention_mask=encoding["attention_mask"])
    return output.squeeze(-1).tolist()


if __name__ == "__main__":
    model, tokenizer = load_model()

    samples = ["AAGKVLKLLKKLL", "AAKKGCWTVSIPPKPCF", "AAKKVLKLLKKLL", "AAWKKAAKKAAKSAKKAG"]
    for seq in samples:
        print(f"{seq:20s} -> predicted log10(MIC) = {predict(seq, model, tokenizer):.4f}")
