/-!
```yaml node
{
  "id": "Fixture2000.Cited_mul_comm",
  "kind": "theorem",
  "doc": "Fixture2000",
  "source": {
    "chapter": "1",
    "section": "1.1",
    "label": "Cited result (p. 4)",
    "pages": [
      4
    ]
  },
  "title": "Cited result (p. 4)",
  "tags": [
    "basic"
  ],
  "concepts": {
    "defines": [],
    "uses": []
  },
  "deps": {
    "statement": [],
    "proof": []
  },
  "decls": [
    "Fixture2000.cited_mul_comm"
  ],
  "fidelity": {
    "status": "faithful"
  },
  "nl_proof_source": {
    "follows": "other",
    "ref": "Elementary arithmetic of natural numbers"
  },
  "cited": {
    "source": {
      "kind": "folklore",
      "ref": "Elementary arithmetic of natural numbers",
      "locator": "Commutativity of multiplication"
    },
    "used_at": [
      4
    ],
    "formulation": "verbatim"
  }
}
```

## Statement

Multiplication of natural numbers is commutative: $mn=nm$.

## Proof

Not proved in the document; see cited.source.

## Description

A background result cited without proof and intentionally left as an external proof obligation.
-/

namespace Fixture2000

/-- **Cited result (p. 4)** (Fixture2000). Not proved in the document. A standard proof
uses induction on the first argument, distributivity in the successor case, and the zero case. -/
theorem cited_mul_comm (m n : Nat) : m * n = n * m := by
  sorry

end Fixture2000
