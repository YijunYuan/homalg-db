import HomAlg.Fixture2000.Def_1

/-!
```yaml node
{
  "id": "Fixture2000.Def_3",
  "kind": "definition",
  "doc": "Fixture2000",
  "source": {
    "chapter": "1",
    "section": "1.1",
    "label": "Definition 3",
    "pages": [
      2
    ]
  },
  "title": "Definition 3",
  "tags": [
    "chain-complex",
    "erratum"
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
    "Fixture2000.zeroComplex"
  ],
  "fidelity": {
    "status": "deviates",
    "deviations": [
      {
        "kind": "erratum",
        "what": "The distinguished degree is zero instead of one.",
        "why": "The project-authored erratum on Fixture2000 p. 4 corrects Definition 3."
      }
    ]
  },
  "dispute_history": [
    {
      "status": "resolved",
      "kind": "statement",
      "reason": "The printed degree one conflicts with the zero complex convention.",
      "opened_by": "fixture-author",
      "on": "2000-01-01",
      "confirmed_by": "fixture-reviewer",
      "confirmed_on": "2000-01-02",
      "resolution": {
        "via": "erratum",
        "by": "fixture-reviewer",
        "on": "2000-01-03",
        "note": "Synthetic test adjudication: the source document contains the erratum on p. 4."
      }
    }
  ]
}
```

## Statement

The zero complex has degree one and every differential is the constant zero function.

## Statement (corrected)

The zero complex has degree zero and every differential is the constant zero function. [Erratum: Fixture2000, p. 4.]

## Description

The constant zero toy complex, with its published degree correction recorded explicitly.

## Formalization notes

The source erratum corrects the degree from one to zero. The dispute history is synthetic test data.
-/

namespace Fixture2000

/-- **Definition 3** (Fixture2000, corrected on p. 4). The zero toy complex. -/
def zeroComplex : ChainComplexToy where
  degree := 0
  differential := fun _ _ => 0
  differential_zero := fun _ => rfl
  square_zero := fun _ _ => rfl

end Fixture2000
