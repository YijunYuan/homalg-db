/-!
```yaml node
{
  "id": "Fixture2000.Def_1",
  "kind": "definition",
  "doc": "Fixture2000",
  "source": {
    "chapter": "1",
    "section": "1.1",
    "label": "Definition 1",
    "pages": [
      1
    ]
  },
  "title": "Definition 1",
  "tags": [
    "chain-complex",
    "basic"
  ],
  "concepts": {
    "defines": [
      "chain-complex"
    ],
    "uses": []
  },
  "deps": {
    "statement": [],
    "proof": []
  },
  "decls": [
    "Fixture2000.ChainComplexToy"
  ],
  "fidelity": {
    "status": "faithful"
  },
  "mathlib": {
    "relation": "variant",
    "decls": [
      "Function.comp"
    ],
    "bridge": "Fixture2000.Bridge_Def_1_mathlib",
    "note": "The square-zero law can equivalently be expressed using function composition; this toy complex is not an alias for a Mathlib complex."
  }
}
```

## Statement

A toy chain complex consists of a natural number called its degree and a family of functions $d_n : \mathbb{N} \to \mathbb{N}$ such that $d_n(0)=0$ and $d_n(d_{n+1}(x))=0$ for every $n,x \in \mathbb{N}$.

## Description

A deliberately elementary model of a square-zero differential, indexed by natural numbers.
-/

namespace Fixture2000

/-- **Definition 1** (Fixture2000). A natural-number-indexed toy chain complex. -/
structure ChainComplexToy where
  /-- The distinguished degree. -/
  degree : Nat
  /-- The differential at each degree. -/
  differential : Nat → Nat → Nat
  /-- Each differential preserves zero. -/
  differential_zero : ∀ n, differential n 0 = 0
  /-- Consecutive differentials compose to zero. -/
  square_zero : ∀ n x, differential n (differential (n + 1) x) = 0

end Fixture2000
