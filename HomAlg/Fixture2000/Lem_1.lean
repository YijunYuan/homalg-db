import HomAlg.Fixture2000.Def_1

/-!
```yaml node
{
  "id": "Fixture2000.Lem_1",
  "kind": "lemma",
  "doc": "Fixture2000",
  "source": {
    "chapter": "1",
    "section": "1.1",
    "label": "Lemma 1",
    "pages": [
      2
    ]
  },
  "title": "Lemma 1",
  "tags": [
    "chain-complex",
    "basic"
  ],
  "concepts": {
    "defines": [],
    "uses": []
  },
  "deps": {
    "statement": [
      "Fixture2000.Def_1"
    ],
    "proof": []
  },
  "decls": [
    "Fixture2000.degree_le_mul_one"
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

For every toy chain complex $C$, its degree satisfies $\deg C \leq (\deg C)\cdot 1$.

## Proof

Multiplication by one fixes every natural number. The assertion therefore follows from reflexivity of the order.

## Description

An elementary bound whose deliberately deferred proof tests direct sorry detection.
-/

namespace Fixture2000

/-- **Lemma 1** (Fixture2000). Since multiplication by one fixes each natural number,
replace the right side by the degree and apply reflexivity of the order. -/
theorem degree_le_mul_one (c : ChainComplexToy) : c.degree ≤ c.degree * 1 := by
  sorry

end Fixture2000
