"""One prospective source-bound map-label profile; this is not a source verdict.

The profile identifies a candidate lexical correction for two fresh independent
reviews. It grants no approval, proof credit or permission to rewrite the Proof.
Changing this profile requires a matching policy digest in a new trusted START.
"""

import hashlib

from homalg.headers import parse_header

CATEGORY = "proof-map-label-typo"
PROFILE = {
    "id": "ce1956-i3-2-extension-labels-v1",
    "node": "CartanEilenberg1956.Thm_I_3_2",
    "source": {
        "label": "Theorem 3.2 (Chapter I)",
        "pages": [8, 9],
        "chapter": "I",
        "section": "3",
    },
    "pdf_sha256": "1e0915f23ec4a4bd638f469561931f5659a7a47faf92d48468bd290ddd726365",
    "statement_sha256": "de460996bc75f0152945f1ea5da2fc7ada7e76ff7583bd61ff576bfb82c9e94e",
    "proof_sha256": "b5612e68451f02ced1404e05633fefb3c5f7441239b1b2fbf9fda4becc5ac802",
    "original": (
        "yields then a map $f''$ of the submodule $A_0+\\Lambda x$ of $A$ which is an extension\n"
        "of $f'$."
    ),
    "corrected": (
        "yields then a map $f'$ of the submodule $A_0+\\Lambda x$ of $A$ which is an extension\n"
        "of $f_0$."
    ),
}


def eligible(source: str, original: str, corrected: str) -> None:
    """Accept only this exact source and passage, never a general proof rewrite."""
    header = parse_header(source)
    proof = header.sections.get("Proof", "")
    if (
        header.metadata["id"] != PROFILE["node"]
        or header.metadata["source"] != PROFILE["source"]
        or hashlib.sha256(header.sections.get("Statement", "").encode()).hexdigest()
        != PROFILE["statement_sha256"]
        or hashlib.sha256(proof.encode()).hexdigest() != PROFILE["proof_sha256"]
        or original != PROFILE["original"]
        or corrected != PROFILE["corrected"]
        or proof.count(original) != 1
        or corrected in proof
    ):
        raise ValueError("Map-label correction must match the exact source-bound profile")
