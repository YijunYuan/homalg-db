import Lean.Elab.Tactic.Decide

/-!
```yaml node
{
  "id": "Fixture2000.Thm_2",
  "kind": "theorem",
  "doc": "Fixture2000",
  "source": {
    "chapter": "1",
    "section": "1.1",
    "label": "Theorem 2",
    "pages": [
      2
    ]
  },
  "title": "Theorem 2",
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
    "Fixture2000.two_add_two"
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

The sum $2+2$ is $4$.

## Proof

Evaluate the sum of the two displayed natural numbers.

## Description

A decidable arithmetic statement whose compiled evaluation uses a nonstandard trust axiom.
-/

namespace Fixture2000

/-- **Theorem 2** (Fixture2000). Evaluate addition of the displayed natural numbers. -/
theorem two_add_two : (2 : Nat) + 2 = 4 := by
  native_decide

end Fixture2000
