import HomAlg.Fixture2000.Def_1

/-!
```yaml node
{
  "id": "Fixture2000.Bridge_Def_1_mathlib",
  "kind": "lemma",
  "doc": "Fixture2000",
  "source": {
    "chapter": "1",
    "section": "1.1",
    "label": "Bridge for Definition 1",
    "pages": [
      1
    ]
  },
  "title": "Bridge for Definition 1",
  "tags": [
    "chain-complex",
    "bridge"
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
    "Fixture2000.differential_comp_zero"
  ],
  "fidelity": {
    "status": "faithful"
  },
  "nl_proof_source": {
    "follows": "agent"
  },
  "aux": {
    "parent": "Fixture2000.Def_1",
    "kind": "bridge",
    "reason": "Relate the pointwise source formulation to library function composition."
  }
}
```

## Statement

The composite of consecutive differentials of a toy chain complex is the constant zero function.

## Proof

Apply function extensionality and the square-zero law of Definition 1.

## Description

An extensional reformulation of the square-zero law using library function composition.
-/

namespace Fixture2000

/-- **Bridge for Definition 1** (Fixture2000). Function extensionality converts the pointwise square-zero law into an equality of functions. -/
theorem differential_comp_zero (c : ChainComplexToy) (n : Nat) :
    Function.comp (c.differential n) (c.differential (n + 1)) = fun _ => 0 := by
  funext x
  exact c.square_zero n x

end Fixture2000
