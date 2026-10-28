# Hochschild 1945 pilot notes

The inventory records the 29 source items identified in the approved pilot plan.
Unnumbered labels are unique; the article's six sections serve as chapters.
The separate citation and auxiliary nodes do not increase the source-item count.

## Citation boundary

These nodes record external facts the source invokes. All seven now have concrete
Lean statements, with nine explicit cited `sorry` boundaries in total. Their
existence is not proof or automatic fidelity approval. The
`editorial` formulations explicitly restore contextual hypotheses and separate
the imported fact from the local argument. The quoted source context remains in
each node's formalization notes.

| Node | Used at printed pages | Boundary |
| --- | --- | --- |
| `Cited_separable_identity` | 61 | A separable algebra has an identity. |
| `Cited_separable_splitting` | 61 | A finite splitting extension makes a separable algebra a sum of full matrix algebras. |
| `Cited_semisimple_representations` | 62 | Semisimplicity is characterized by complete reducibility or invariant complements. |
| `Cited_inseparable_simple_component` | 62 | A semisimple inseparable algebra has an actual inseparable simple ideal factor and algebra retraction. |
| `Cited_simple_inseparable_center` | 62 | The center of a simple inseparable algebra is an inseparable algebraic field extension. |
| `Cited_radical_structure` | 64 | Nilpotence of the finite-dimensional radical and semisimplicity of the quotient in the source's non-nilpotent case. |
| `Cited_semisimple_ideal_structure` | 64–65 | Ideals inside a semisimple algebra are semisimple and have ideal complements. |

The first two retain footnote 7's broad references to Deuring, van der Waerden
and Jacobson, without inventing theorem locators. The other facts are invoked as
classical background without precise citations. The proof of Lemma 4.1 is local:
footnote 9's derivation literature motivates that lemma and does not replace its
proof with an imported theorem. The descent of a finite linear system from an
extension field is an elementary linear-algebra step.

The source's footnote 2 prints volume 64 with the year 1941. This is retained in
the reviewed transcription. Bibliographic reconciliation belongs in editorial
metadata, not a silent correction of the quotation.

The foundation proposal uses a nonunital associative algebra and field-linear
scalar compatibility. Its finite-dimensional algebra assumption is evidenced by
the basis of length `n` on printed page 59. That paragraph does not explicitly
impose finite dimension on every coefficient space. The standalone wording of
Lemma 4.1 and its finite-dimensional application are checked separately from
the algebra foundation. Under the user-approved independent-agent policy of
2026-10-28, all 13 foundations have actual independent, content-bound confirmations.
The matrix and field entries retain their distinct source evidence and reviewer
identities alongside the original ten and the nonunital radical convention.

## Transcription rehearsal

The ten body pages, PDF 2–11, were visually transcribed in batches of five and
independently reviewed against the images. No OCR or extracted text supplied the
transcription. Three concrete differences were corrected before final review:

- PDF 3, footnote 5: the locator is `pp. 4–5`.
- PDF 8: the kernel symbol in the extension definition was restored.
- PDF 9, equation (1): the printed congruence sign was restored.

Two suspected differences on PDF 10 were false positives from the 200 dpi view:
a higher-resolution render confirmed the italic `f` after “cocycle” and the short
bar over the cohomology-class symbol. The printed lowercase Fraktur `p` on PDF 8
and the unbarred first `g` in the equivalence on PDF 4 were retained. Custom
Fraktur macros on PDF 2–6 were mechanically expanded and independently checked
again before node extraction.

Per-page wall times were not measured. Initial feedback was exchanged before
the final satisfactory records; it was not persisted as intermediate partial or
mismatch states. No numeric review-failure rate is inferred from that history.
The private review manifest retains exact hashes of the delivered page files.

## Completed local arguments and remaining boundaries

Theorem 4.1 now has a complete local proof in both directions. Its forward
argument constructs the printed matrix-unit primitive after actual scalar
extension and descends it by a coefficient functional fixing one. Its converse
constructs invariant complements, reduces through an actual inseparable simple
ideal factor, and applies a center derivation entrywise to the faithful regular
matrix representation. The coefficient space is arbitrary throughout. The five
classical structural results it invokes remain explicit cited boundaries.

Lemma 4.1 now has a complete local proof for the explicitly recorded finite
extension scope. A maximal proper intermediate field supplies a simple purely
inseparable final step; differentiation descends through the evaluation kernel
because the minimal polynomial has derivative zero. The proof retains the source
construction, with generator derivative one, while recording that it does not
separately establish the printed degree-p presentation. It uses no local `sorry`
and no classical cited assumption.

Proposition 6.2 now proves both directions of the extension classification and
realizes every cohomology class by the actual cocycle extension. The reverse
classification constructs coordinates from a linear section, applies the
kernel isomorphism and coboundary shear, and proves that the resulting linear
equivalence is multiplicative and commutes with the quotient maps. There is no
local `sorry` in that node.

The quotient-separability corollary now has a complete local proof using one
corrected cocycle, its descent to the two-sided annihilator module, and one
primitive. It never invokes the false kernel isomorphism in Theorem 5.1. The
valid quotient-module constructions were moved to a technical auxiliary so
that the logical dependency graph can distinguish them from the false claim.
The owner confirmed the Theorem 5.1 statement error on 2026-10-28; its literal
statement and owner-decision evidence are retained.

Both separability corollaries now inherit only explicitly cited classical
boundaries. Proposition 6.1 also has a complete local proof: an actual radical quotient
and ideal complement reduce to a nilpotent kernel, followed by the source
induction on kernel dimension through the quotient by its square. Its universal
predicates quantify finite extension algebras, with the scope clarification and
direct radical-reduction variant recorded as deviations. Theorem 6.1 therefore
now depends only on the explicit classical citation boundaries. The
finite-support auxiliary is proved and preserves arbitrary coefficient modules in the cohomology statements. The separate
classical cited results remain visible external boundaries throughout.


## Final workflow evidence

The normal CLI completed both transcription tasks, six inventory tasks, six DAG
tasks, the citation task, all twelve statement tasks, the independent
first-chapter checkpoint, and all six proof tasks. These are evidence-based
completion results, including the explicitly confirmed source error, rather
than a claim that the false theorem was proved.

An actual default Codex/Horizon run (`0001`, session
`0002-horizon-Hochschild1945.PROOF.1`) independently rechecked the completed
first chapter without changing its statements or proofs. Its separate honesty
reviewer checked twelve declaration axiom closures against the original page.
The real after-session hook passed scope and compiled validation, archived local
discussions, and pushed the private backup. The source transcription and
provenance were committed to the private Git-LFS repository as `02615f4`; no PDF
or page image is included in the public submission.

All source items except the confirmed false Theorem 5.1 have complete local
proofs or constructions. The quotient-separability corollary retains the source
Theorem 5.1 edge for auditability; its repaired compiled proof does not use that
false theorem. The conservative declared-dependency status consequently remains
`statement-complete` for this corollary despite its `proved` local record.
The other 27 source items are `proof-complete`; applicable classical citations
remain visible. Eight heuristic dependency/comparison warnings have specific
explanations in their nodes' formalization notes; no rule was disabled.
