import HomAlg.Fixture2000.Def_1
import HomAlg.Fixture2000.Lem_2

/-!
```yaml node
{
  "id": "Fixture2000.Thm_1",
  "kind": "theorem",
  "doc": "Fixture2000",
  "source": {
    "chapter": "1",
    "section": "1.1",
    "label": "Theorem 1",
    "pages": [
      2
    ]
  },
  "title": "Theorem 1",
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
    "proof": ["Fixture2000.Lem_2"]
  },
  "decls": [
    "Fixture2000.degree_add_zero",
    "Fixture2000.eq_degree_zero"
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

For every toy chain complex $C$, $\deg C+0=\deg C$. If $\deg C=0$, then $\deg C+0=0$.

## Proof

Apply Lemma 2 to the degree, proving the first assertion. [uses `Fixture2000.Lem_2`] Substitute the assumed equality into that assertion to obtain the second.

## Description

Two parts of one theorem share a node; the second declaration deliberately starts with eq_.
-/

namespace Fixture2000

/-- **Theorem 1** (Fixture2000). Apply Lemma 2 to the distinguished degree. -/
theorem degree_add_zero (c : ChainComplexToy) : c.degree + 0 = c.degree := by
  exact add_zero_natural c.degree

/-- **Theorem 1 (ii)** (Fixture2000). Substitute the assumed zero degree in part (i). -/
theorem eq_degree_zero (c : ChainComplexToy) (h : c.degree = 0) : c.degree + 0 = 0 := by
  exact (degree_add_zero c).trans h

end Fixture2000
