import HomAlg.Fixture2001.Def_1
import HomAlg.Fixture2000.Def_1
import HomAlg.Fixture2000.Thm_1

/-!
```yaml node
{
  "id": "Fixture2001.Thm_1",
  "kind": "theorem",
  "doc": "Fixture2001",
  "source": {
    "chapter": "1",
    "section": "1.1",
    "label": "Theorem 1",
    "pages": [
      1
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
      "Fixture2001.Def_1",
      "Fixture2000.Def_1"
    ],
    "proof": [
      "Fixture2000.Thm_1"
    ]
  },
  "decls": [
    "Fixture2001.degree_add_zero"
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

If $C$ is a pointed toy chain complex, the degree of its underlying complex is unchanged by adding zero.

## Proof

Apply part (i) of Theorem 1 of Fixture2000 to the underlying complex. [uses `Fixture2000.Thm_1`]

## Description

A later theorem cites the earlier two-part theorem through an explicit fully qualified name.
-/

namespace Fixture2001

/-- **Theorem 1** (Fixture2001). Apply part (i) of Fixture2000 Theorem 1 to the underlying complex. -/
theorem degree_add_zero (c : PointedToyComplex) : c.complex.degree + 0 = c.complex.degree :=
  Fixture2000.degree_add_zero c.complex

end Fixture2001
