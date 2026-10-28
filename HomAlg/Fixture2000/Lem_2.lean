/-!
```yaml node
{
  "id": "Fixture2000.Lem_2",
  "kind": "lemma",
  "doc": "Fixture2000",
  "source": {
    "chapter": "1",
    "section": "1.1",
    "label": "Lemma 2",
    "pages": [
      2
    ]
  },
  "title": "Addition of zero",
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
    "Fixture2000.add_zero_natural"
  ],
  "fidelity": {
    "status": "faithful"
  },
  "nl_proof_source": {
    "follows": "document"
  }
}
```

## Statement

For every natural number $n$, $n+0=n$.

## Proof

This is the defining identity for addition of zero.

## Description

A proved lemma used explicitly by the two-part theorem, testing exported proof dependencies.
-/

namespace Fixture2000

/-- **Lemma 2** (Fixture2000). The defining identity for addition of zero. -/
theorem add_zero_natural (n : Nat) : n + 0 = n := Nat.add_zero n

end Fixture2000
