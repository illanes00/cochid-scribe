"""Utilities for claim positioning in document text."""


def find_claim_offsets(text: str, claim_text: str) -> tuple[int | None, int | None]:
    """Locate claim text within document text and return offsets."""
    if not text or not claim_text:
        return None, None

    haystack = text.lower()
    needle = claim_text.lower()
    start = haystack.find(needle)
    if start < 0:
        return None, None
    return start, start + len(claim_text)
