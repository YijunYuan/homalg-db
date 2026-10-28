import HomAlg.Fixture2000.Def_1

/-!
```yaml node
{
  "id": "Fixture2000.Prop_1",
  "kind": "proposition",
  "doc": "Fixture2000",
  "source": {
    "chapter": "1",
    "section": "1.1",
    "label": "Proposition 1",
    "pages": [
      3
    ]
  },
  "title": "Proposition 1",
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
    "Fixture2000.degree_positive"
  ],
  "fidelity": {
    "status": "faithful"
  },
  "nl_proof_source": {
    "follows": "document"
  },
  "dispute": {
    "status": "open",
    "kind": "statement",
    "reason": "Zero is a natural number; the zero complex is a counterexample.",
    "counterexample": "Fixture2000.zeroComplex",
    "opened_by": "fixture-author",
    "on": "2000-01-01",
    "inbox": "I-0001"
  }
}
```

## Statement

Every toy chain complex has strictly positive degree.

## Proof

Every natural number is strictly positive. Apply this observation to the degree.

## Description

An unconfirmed statement dispute; the zero complex supplies a counterexample.
-/

namespace Fixture2000

/-- **Proposition 1** (Fixture2000). STATEMENT-DISPUTED: the zero complex has degree zero.
The source argument says that every natural number is positive and applies this to the degree;
its first step is false, so the claimed proof is deliberately left open. -/
theorem degree_positive (c : ChainComplexToy) : 0 < c.degree := by
  sorry

end Fixture2000
