"""Minimal input parser for batch prediction.

Turns a block of text into a list of (label, sequence) pairs. Two formats are
auto-detected:

- FASTA: records starting with a ``>`` header line; the label is the header text
  (without ``>``), the sequence is the concatenation of the following lines.
- Plain: one sequence per line; the label is ``None``.

Blank lines are ignored. Sequences are returned raw (only surrounding whitespace
stripped); validation and normalization happen downstream.
"""


def parse_input(text: str) -> list[tuple[str | None, str]]:
    """Parse batch input text into (label, sequence) pairs, preserving order."""
    text = text.strip()
    if not text:
        return []

    lines = text.splitlines()
    is_fasta = any(line.lstrip().startswith(">") for line in lines)
    if not is_fasta:
        return [(None, line.strip()) for line in lines if line.strip()]

    records: list[tuple[str | None, str]] = []
    label: str | None = None
    seq_parts: list[str] = []
    started = False

    def flush() -> None:
        if started:
            records.append((label, "".join(seq_parts)))

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            flush()
            label = line[1:].strip()
            seq_parts = []
            started = True
        else:
            seq_parts.append(line)
            started = True
    flush()
    return records
