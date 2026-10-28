import Mathlib.Algebra.Group.Defs

/-!
```yaml node
{
  "id": "Fixture2000.Def_2",
  "kind": "definition",
  "doc": "Fixture2000",
  "source": {
    "chapter": "1",
    "section": "1.1",
    "label": "Definition 2",
    "pages": [
      1
    ]
  },
  "title": "Definition 2",
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
    "Fixture2000.AbelianGroup"
  ],
  "fidelity": {
    "status": "faithful"
  },
  "mathlib": {
    "relation": "same",
    "decls": [
      "AddCommGroup"
    ],
    "note": "A recall of the background notion, awaiting the foundation review workflow in M1-T8."
  }
}
```

## Statement

We recall the usual notion of an abelian group, written additively. In this text AbelianGroup means that background structure.

## Description

A recall entry for the foundational additive abelian group structure.

## Formalization notes

M0 keeps this recall entry faithful until M1-T8 can create a human-reviewed foundation lock.
-/

namespace Fixture2000

/-- **Definition 2** (Fixture2000). The usual additive abelian group structure. -/
abbrev AbelianGroup (A : Type) := AddCommGroup A

end Fixture2000
