import HomAlg.Fixture2000.Def_1

/-!
```yaml node
{
  "id": "Fixture2001.Def_1",
  "kind": "definition",
  "doc": "Fixture2001",
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
    "Fixture2001.PointedToyComplex"
  ],
  "fidelity": {
    "status": "faithful"
  }
}
```

## Statement

A pointed toy chain complex is a toy chain complex in the sense of Fixture2000, together with a chosen natural number.

## Description

A later source extends the earlier definition while retaining an explicit cross-document dependency.
-/

namespace Fixture2001

/-- **Definition 1** (Fixture2001). A toy complex equipped with a chosen natural number. -/
structure PointedToyComplex where
  /-- The underlying earlier toy complex. -/
  complex : Fixture2000.ChainComplexToy
  /-- The distinguished natural number. -/
  point : Nat

end Fixture2001
