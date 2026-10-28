/-!
```yaml node
{
  "id": "Fixture2000.Aux_Thm_1_step",
  "kind": "lemma",
  "doc": "Fixture2000",
  "source": {
    "chapter": "1",
    "section": "1.1",
    "label": "Auxiliary to Theorem 1",
    "pages": [
      2
    ]
  },
  "title": "Auxiliary to Theorem 1",
  "tags": [
    "technical"
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
    "Fixture2000.aux_add_zero"
  ],
  "fidelity": {
    "status": "faithful"
  },
  "nl_proof_source": {
    "follows": "agent"
  },
  "aux": {
    "parent": "Fixture2000.Thm_1",
    "kind": "lemma",
    "reason": "An initial separate arithmetic step, now supplied directly by the foundation library.",
    "pruned": true
  }
}
```

## Statement

For every natural number $n$, $n+0=n$.

## Proof

Apply the defining identity for addition by zero.

## Description

An unused auxiliary proof step marked as a pruning candidate.
-/

namespace Fixture2000

/-- **Auxiliary to Theorem 1** (Fixture2000). Addition by zero is an elementary identity. -/
theorem aux_add_zero (n : Nat) : n + 0 = n := Nat.add_zero n

end Fixture2000
