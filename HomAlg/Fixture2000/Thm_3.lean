import HomAlg.Fixture2000.Def_1
import HomAlg.Fixture2000.Lem_1

/-!
```yaml node
{
  "id": "Fixture2000.Thm_3",
  "kind": "theorem",
  "doc": "Fixture2000",
  "source": {
    "chapter": "1",
    "section": "1.1",
    "label": "Theorem 3",
    "pages": [
      3
    ]
  },
  "title": "Theorem 3",
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
      "Fixture2000.Lem_1"
    ]
  },
  "decls": [
    "Fixture2000.degree_le_mul_one_add_zero"
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

For every toy chain complex $C$, $\deg C \leq (\deg C)\cdot 1+0$.

## Proof

Apply Lemma 1, then use that adding zero leaves its right side unchanged. [uses `Fixture2000.Lem_1`]

## Description

The proof is written, but the separate lemma on which it depends still contains sorry.
-/

namespace Fixture2000

/-- **Theorem 3** (Fixture2000). Apply Lemma 1 and remove the final addition of zero. -/
theorem degree_le_mul_one_add_zero (c : ChainComplexToy) : c.degree ≤ c.degree * 1 + 0 := by
  simpa only [Nat.add_zero] using degree_le_mul_one c

end Fixture2000
