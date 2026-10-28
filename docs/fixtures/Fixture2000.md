# Toy chain complexes (Fixture2000)

This is an original synthetic test document. Its erroneous statements, flawed proofs, and erratum are deliberate. All fixture-reviewer records and dates in the metadata are fictitious test data. No source-fidelity lock or real human approval is asserted.

<!-- page 1 -->

We use ordinary natural numbers and elementary arithmetic as background.

## Definition 1

A toy chain complex consists of a natural number called its degree and a family of functions $d_n : \mathbb{N} \to \mathbb{N}$ such that $d_n(0)=0$ and $d_n(d_{n+1}(x))=0$ for every $n,x \in \mathbb{N}$.

## Definition 2

We recall the usual notion of an abelian group, written additively. In this text AbelianGroup means that background structure.

<!-- page 2 -->

## Definition 3

The zero complex has degree one and every differential is the constant zero function.

## Lemma 1

For every toy chain complex $C$, its degree satisfies $\deg C \leq (\deg C)\cdot 1$.

Proof. Multiplication by one fixes every natural number. The assertion therefore follows from reflexivity of the order.

## Lemma 2

For every natural number $n$, $n+0=n$.

Proof. This is the defining identity for addition of zero.

## Theorem 1

For every toy chain complex $C$, $\deg C+0=\deg C$. If $\deg C=0$, then $\deg C+0=0$.

Proof. Apply Lemma 2 to the degree, proving the first assertion. [uses `Fixture2000.Lem_2`] Substitute the assumed equality into that assertion to obtain the second.

## Theorem 2

The sum $2+2$ is $4$.

Proof. Evaluate the sum of the two displayed natural numbers.

<!-- page 3 -->

## Theorem 3

For every toy chain complex $C$, $\deg C \leq (\deg C)\cdot 1+0$.

Proof. Apply Lemma 1, then use that adding zero leaves its right side unchanged. [uses `Fixture2000.Lem_1`]

## Proposition 1

Every toy chain complex has strictly positive degree.

Proof. Every natural number is strictly positive. Apply this observation to the degree.

## Proposition 2

For every toy chain complex $C$, $\deg C=\deg C$.

Proof. Every natural number equals its successor. It follows in particular that the degree equals itself.

## Remark 1

The distinguished degree of the zero complex is zero.

<!-- page 4 -->

## Cited result (p. 4)

Multiplication of natural numbers is commutative: $mn=nm$.

Proof. Not proved in the document; see cited.source.

## Theorem 4

For every toy chain complex $C$ and natural number $n$, $(\deg C)n=n(\deg C)$.

Proof. Use the well-known commutativity of multiplication, taking the first factor to be the degree. [uses `Fixture2000.Cited_mul_comm`]

## Erratum to Definition 3

The zero complex has degree zero and every differential is the constant zero function. The word "one" in Definition 3 is a misprint for "zero".

## Fixture coverage

`Def_1` is proved; `Def_2` is a recall alias awaiting M1-T8; `Def_3` records the erratum; `Lem_1` is stated; `Lem_2` is proved and used by `Thm_1`; `Thm_1` has two main declarations including `eq_degree_zero`; `Thm_2` uses compiled evaluation; `Thm_3` depends on a separate sorry lemma; `Thm_4` depends only on a cited sorry; `Rem_1` is planned; `Prop_1` is an unconfirmed statement dispute; `Prop_2` is a synthetic confirmed proof dispute. Auxiliary and bridge nodes are editorial additions, not source entries. Headline locks and all-rule negative fixtures are introduced with their M1 implementations.
