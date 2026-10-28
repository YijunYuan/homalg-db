import HomAlg.Fixture2000.Def_1

/-!
```yaml node
{
  "id": "Fixture2000.Prop_2",
  "kind": "proposition",
  "doc": "Fixture2000",
  "source": {
    "chapter": "1",
    "section": "1.1",
    "label": "Proposition 2",
    "pages": [
      3
    ]
  },
  "title": "Proposition 2",
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
    "Fixture2000.degree_self_disputed"
  ],
  "fidelity": {
    "status": "faithful"
  },
  "nl_proof_source": {
    "follows": "document"
  },
  "dispute": {
    "status": "open",
    "kind": "proof",
    "reason": "The proof relies on the false claim that every natural number equals its successor.",
    "opened_by": "fixture-author",
    "on": "2000-01-01",
    "confirmed_by": "fixture-reviewer",
    "confirmed_on": "2000-01-02",
    "inbox": "I-0002"
  }
}
```

## Statement

For every toy chain complex $C$, $\deg C=\deg C$.

## Proof

Every natural number equals its successor. It follows in particular that the degree equals itself.

## Description

A true assertion with an explicitly invalid source proof and a synthetic confirmed proof dispute.
-/

namespace Fixture2000

/-- **Proposition 2** (Fixture2000). PROOF-DISPUTED: the source claims every number equals its successor.
The source proof asserts n + 1 = n for every natural number and infers reflexivity of the degree;
that argument is invalid and must not be silently replaced by the trivial alternative proof. -/
theorem degree_self_disputed (c : ChainComplexToy) : c.degree = c.degree := by
  sorry

end Fixture2000
