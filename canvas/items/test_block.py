from __future__ import annotations


def should_show_test_block(direction: str, signal_nature: str) -> bool:
    """Return True when B.P. should be rendered for a direction/nature pair."""
    dir_norm = (direction or "").upper()
    nature_norm = (signal_nature or "").upper()
    if nature_norm == "ANALOG":
        return dir_norm == "IN"
    return dir_norm == "OUT"
