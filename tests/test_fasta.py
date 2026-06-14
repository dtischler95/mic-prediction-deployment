"""Unit tests for the batch input parser (no model, no network)."""

from app.fasta import parse_input


def test_plain_one_per_line_ignores_blanks_and_whitespace():
    assert parse_input("GWKR\n\nILPW\n  ELKK  ") == [
        (None, "GWKR"),
        (None, "ILPW"),
        (None, "ELKK"),
    ]


def test_fasta_headers_become_labels_and_multiline_seq_is_joined():
    assert parse_input(">pep1 desc\nGWKR\nKRFG\n>pep2\nILPW") == [
        ("pep1 desc", "GWKRKRFG"),
        ("pep2", "ILPW"),
    ]


def test_fasta_tolerates_blank_lines_and_indentation():
    assert parse_input("  >a\n\nMKK\n\n  >b\nLL\n") == [("a", "MKK"), ("b", "LL")]


def test_header_without_sequence_is_kept():
    # Downstream validation flags the empty sequence; the parser keeps the record.
    assert parse_input(">only_header") == [("only_header", "")]


def test_empty_input_returns_empty_list():
    assert parse_input("   \n  \n") == []
