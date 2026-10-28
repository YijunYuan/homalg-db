import HomAlg.Fixture2000.Def_1
import HomAlg.Fixture2000.Cited_mul_comm

/-!
```yaml node
{
  "id": "Fixture2000.Thm_4",
  "kind": "theorem",
  "doc": "Fixture2000",
  "source": {
    "chapter": "1",
    "section": "1.1",
    "label": "Theorem 4",
    "pages": [
      4
    ]
  },
  "title": "Theorem 4",
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
    "proof": [
      "Fixture2000.Cited_mul_comm"
    ]
  },
  "decls": [
    "Fixture2000.degree_mul_comm"
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

For every toy chain complex $C$ and natural number $n$, $(\deg C)n=n(\deg C)$.

## Proof

Use the well-known commutativity of multiplication, taking the first factor to be the degree. [uses `Fixture2000.Cited_mul_comm`]

## Description

A complete proof modulo the single unproved cited arithmetic result.
-/

namespace Fixture2000

/-- **Theorem 4** (Fixture2000). Specialize the cited commutativity law to the degree. -/
theorem degree_mul_comm (c : ChainComplexToy) (n : Nat) : c.degree * n = n * c.degree :=
  cited_mul_comm c.degree n

end Fixture2000
