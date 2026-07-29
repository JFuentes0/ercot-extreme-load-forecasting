# Track A — Model Mechanics Note v1

**Task:** TRACK-A-SCAFFOLD-001
**Date:** 2026-07-29
**Status:** Written before any model code, per `docs/project/NEXT_TASK.md`
**Controlling document:** `docs/track_a/EXPERIMENT_FREEZE_v1.md`

---

## 0. Purpose and reading protocol

This note records the model mechanics of standard CNP and AdaCNP as established from the two
hash-verified reference papers, and separates what the papers state from what this project
must decide. It exists so that the scaffold implementation can be audited against its
sources.

### 0.1 Sources

| Role | File | SHA-256 (first 16) | Pages |
| --- | --- | --- | --- |
| CNP | `cnp_arxiv_1807.01613.pdf` | `8f661c43330a4091` | 10 |
| AdaCNP | `adacnp_arxiv_2602.04609.pdf` | `be4c59938168df22` | 9 |

Both verified `OK` by `sha256sum -c paper_hashes.sha256` immediately before reading. The PDFs
were read in place at `/home/johnny_fuentes/ercot-model-references/`. Neither file was
modified, moved, or copied into this repository; hashes were re-verified after reading and
still match.

**Citation convention.** Page numbers are the PDF page numbers of the verified files.
Equation numbers are the papers' own. Where a claim cannot be traced to a specific location,
this note says so explicitly rather than implying a citation exists.

### 0.2 Provenance labels

Every material statement below carries exactly one label:

| Label | Meaning |
| --- | --- |
| `PAPER-SPECIFIED` | Stated in the cited paper |
| `ERCOT-APPLICATION CHOICE` | A choice this project makes to apply the method to ERCOT data |
| `ENGINEERING DEFAULT` | An implementation default not driven by the paper or the science |
| `NOT SPECIFIED BY PAPER` | The paper is silent; a project decision is required |

Where the experiment freeze already fixes an item, the label records the paper's stance and
the text names the freeze as controlling.

### 0.3 Short-form citation keys

- **[CNP]** = Garnelo et al., *Conditional Neural Processes*, arXiv:1807.01613v1 (ICML 2018).
- **[ADA]** = Hu, Ma, Wu, Hou, *Resilient Load Forecasting under Climate Change: Adaptive
  Conditional Neural Processes for Few-Shot Extreme Load Forecasting*, arXiv:2602.04609v1.

---

## 1. Standard CNP: context encoding and aggregation

**1.1** A CNP conditions on an observation set `O` through an embedding of fixed
dimensionality, and factorises the predictive distribution across target points.
`PAPER-SPECIFIED` — [CNP] p. 3, §2.2: "The defining characteristic of a CNP is that it
conditions on `O` via an embedding of fixed dimensionality"; factorisation
`Q_θ(f(T)|O,T) = ∏_{x∈T} Q_θ(f(x)|O,x)` on the same page.

**1.2** Each context pair is encoded independently by a shared network `h_θ`:

```
r_i = h_θ(x_i, y_i)      for all (x_i, y_i) ∈ O          [CNP] Eq. (1), p. 3
r   = r_1 ⊕ r_2 ⊕ … ⊕ r_n                                [CNP] Eq. (2), p. 3
φ_i = g_θ(x_i, r)        for all (x_i) ∈ T               [CNP] Eq. (3), p. 3
```

with `h_θ : X × Y → R^d` and `g_θ : X × R^d → R^e`, and `⊕` a commutative operation mapping
elements of `R^d` into a single element of `R^d`. `PAPER-SPECIFIED` — [CNP] p. 3, text
immediately following Eq. (3).

**1.3** The aggregator `⊕` is instantiated as the mean. `PAPER-SPECIFIED` — [CNP] p. 3,
§2.2: "In most of our experiments we take `a_1 ⊕ … ⊕ a_n` to be the mean operation
`(a_1 + … + a_n)/n`." [ADA] restates this as the standard-CNP aggregator in Eq. (6), p. 4:
`r = (1/n_c) Σ_{i=1}^{n_c} r_i`.

**1.4** The construction is permutation-invariant in the context set, and scales as `O(n+m)`
for `n` observations and `m` targets. `PAPER-SPECIFIED` — [CNP] p. 3 ("This architecture
ensures permutation invariance and `O(n+m)` scaling for conditional prediction"); p. 2, §2.2
intro; summary items 2 and 3 on p. 3.

**1.5** Concrete regression architecture used by the authors: a three-layer MLP encoder `h`
with a 128-dimensional output representation `r_i`; mean aggregation `r = (1/n) Σ r_i`;
`r` **concatenated to** the target input `x_t`; a five-layer MLP decoder `g`; Adam optimizer.
`PAPER-SPECIFIED` — [CNP] p. 5, §4.1.

---

## 2. AdaCNP: target-conditioned adaptive weighting

**2.1** AdaCNP's stated motivation is that uniform mean aggregation implicitly treats all
context points as equally informative, which dilutes the informative signal when `p(y|x)`
shifts across regimes and only a subset of contexts is relevant. `PAPER-SPECIFIED` — [ADA]
p. 2, §1; p. 3, §2.3; p. 4, end of §3.2.

**2.2** AdaCNP retains the CNP encoder unchanged. The context representations it aggregates
are the **same** `r_i = h_θ(x^C_i, y^C_i)` produced by the CNP encoder.
`PAPER-SPECIFIED` — [ADA] Eq. (5), p. 4, and Eq. (14), p. 5 ("Let `r_i = h_θ(x^C_i, y^C_i) ∈
R^{d_r}` be the CNP context representations produced by the encoder").

**2.3** An embedding network maps **inputs only** into a shared embedding space:

```
φ_ω : X → R^{d_e}                                        [ADA] Eq.  (9), p. 4
e^C_i = φ_ω(x^C_i),   e^T_j = φ_ω(x^T_j)                 [ADA] Eq. (10), p. 4
```

`PAPER-SPECIFIED`. **This is the leakage-critical fact:** the target-side argument to `φ_ω`
is `x^T_j`. Target outcomes `y^T_j` are not an argument to the embedding, the scoring
function, or the weighting. See §6.

**2.4** A scoring layer produces a scalar relevance score per (context, target) pair:

```
f_ψ : R^{d_e} × R^{d_e} → R                              [ADA] Eq. (11), p. 4
s_ij = f_ψ(e^C_i, e^T_j)                                 [ADA] Eq. (12), p. 4
```

`PAPER-SPECIFIED`. The paper states `f_ψ` "can be instantiated as a lightweight MLP or a
parametric similarity module; its role is to learn a task-specific notion of relevance
between contexts and targets" ([ADA] p. 4, §3.3). The exact form is therefore left open —
see §8.3.

**2.5** Scores are converted to normalised weights by a temperature-scaled softmax over
context indices:

```
w_ij = exp(s_ij / τ) / Σ_{i'=1}^{n_c} exp(s_{i'j} / τ)
Σ_{i=1}^{n_c} w_ij = 1,     w_ij ≥ 0,     τ > 0          [ADA] Eq. (13), p. 5
```

`PAPER-SPECIFIED`. The paper states the sum-to-one and non-negativity properties as part of
the equation itself. `τ` is "a temperature parameter controlling the concentration of
weights" ([ADA] p. 5).

**2.6** Aggregation is a target-specific weighted sum of the same context representations:

```
r_j = Σ_{i=1}^{n_c} w_ij r_i = Σ_{i=1}^{n_c} w_ij h_θ(x^C_i, y^C_i)   [ADA] Eq. (14), p. 5
```

`PAPER-SPECIFIED`.

**2.7** The weighting is permutation-invariant with respect to context ordering.
`PAPER-SPECIFIED` — [ADA] p. 5, sentence following Eq. (15): "This construction is
permutation-invariant with respect to the ordering of context points."

**2.8** Temperature interpolates between near-uniform aggregation and highly selective
reweighting. `PAPER-SPECIFIED` — [ADA] p. 2, §1: "a temperature controlled mechanism that
smoothly interpolates between near uniform aggregation and highly selective reweighting."

**2.9 The reduction that makes the controlled comparison valid.** Setting `w_ij = 1/n_c` for
all `i` reduces Eq. (14) to Eq. (6) exactly:
`Σ_i (1/n_c) r_i = (1/n_c) Σ_i r_i = r`. `PAPER-SPECIFIED` as algebra over the two cited
equations; the papers do not state this reduction in words. The condition is met whenever all
scores `s_ij` are equal for fixed `j` (softmax of a constant vector is uniform), and is
approached as `τ → ∞`. This is the mechanical basis of freeze §9 item 5.

---

## 3. Decoder inputs

**3.1** The decoder consumes the target input and the aggregated representation, and emits
distribution parameters:

```
φ_j = g_θ(x^T_j, r_j),   g_θ : X × R^{d_r} → Φ           [ADA] Eq. (7) and Eq. (15), pp. 4–5
```

`PAPER-SPECIFIED`. [CNP] Eq. (3), p. 3 is the same interface with the uniform `r`.

**3.2** The decoder interface is **identical** between the two arms; only the aggregated
representation passed to it differs. `PAPER-SPECIFIED` — [ADA] p. 5, preceding Eq. (15):
"The decoder predicts the target distribution parameters using the same interface as CNP";
[ADA] p. 2, §1: the weighting "remains compatible with the standard CNP decoding pipeline."

**3.3** The mechanism by which `r` and `x_t` are combined is concatenation.
`PAPER-SPECIFIED` — [CNP] p. 5, §4.1: `r` "is concatenated to `x_t` and passed to a decoder
`g`". [ADA] writes `g_θ(x^T_j, r_j)` without naming the combination rule; the concatenation
citation is [CNP] only.

---

## 4. Predictive distribution

**4.1** For regression, `φ` parametrises a Gaussian mean and variance:
`φ_i = (μ_i, σ²_i)`. `PAPER-SPECIFIED` — [CNP] p. 3, §2.2; [ADA] p. 4, §3.2, following
Eq. (7), which additionally specifies the variance is **diagonal**.

**4.2** For the 24-hour load task specifically, the model outputs a mean and a variance for
each of the 24 hourly time steps. `PAPER-SPECIFIED` — [ADA] p. 6, §4.2: "AdaCNP outputs both
the mean `μ` and variance `σ` for each of the 24 hourly time steps." This matches freeze §6
(24 means, 24 scales).

**4.3** Predictive intervals are read off the Gaussian output; [ADA] Fig. 5, p. 7 plots
"confidence intervals, denoted by the model's prediction variance (`μ ± σ`)".
`PAPER-SPECIFIED`. Freeze §6 states the same requirement ("Probabilistic intervals are
derived from the Gaussian output, not modeled separately") and is controlling.

**4.4 The positivity transform is not specified by either paper.**
`NOT SPECIFIED BY PAPER`. Neither [CNP] nor [ADA] states how the raw decoder output is mapped
to a strictly positive scale — no softplus, exponential, or floor appears in either text.
Freeze §6 fixes this for Track A: **softplus plus a small numerical floor, the floor being a
frozen constant recorded in configuration and not tuned.** The freeze controls. Any
implementation detail here must be attributed to the freeze, never to the papers.

**4.5** Whether the decoder emits a variance `σ²` or a standard deviation `σ` is not stated
consistently: [ADA] Eq. for `φ_j` uses `σ²_j`, while [ADA] §4.2 p. 6 and Fig. 5 p. 7 speak of
`σ` and `μ ± σ`. `NOT SPECIFIED BY PAPER` as a single convention. Freeze §6 says "24 positive
Gaussian **scales**" produced by softplus; this scaffold therefore treats the decoder's
positive output as the **scale** `σ`, and computes the likelihood accordingly.
`ERCOT-APPLICATION CHOICE`, resolved by the freeze.

---

## 5. Training objective

**5.1** CNP's stated objective conditions on a random subset `O_N ⊂ O` and scores the negative
conditional log probability of the targets:

```
L(θ) = −E_{f∼P}[ E_N[ log Q_θ({y_i}_{i=0}^{n-1} | O_N, {x_i}_{i=0}^{n-1}) ] ]   [CNP] Eq. (4), p. 3
```

`PAPER-SPECIFIED`. [CNP] p. 3 notes the scored targets "include **both** the observed and
unobserved values", and that Monte Carlo estimates of the gradient are taken by sampling `f`
and `N`.

**5.2** AdaCNP's stated objective is the negative log-likelihood over sampled targets:

```
L_CNP(θ)     = −E_{C,T⊆D_H}[ Σ_{j=1}^{n_t} log p_θ(y^T_j | φ_j) ]        [ADA] Eq. (8), p. 4
L_ADACNP     = − Σ_{j=1}^{n_t} log p_θ(y^T_j | φ_j)                      [ADA] Alg. 1 line 14, p. 4
```

`PAPER-SPECIFIED`. Parameters `(θ, ω, ψ)` — encoder/decoder, embedding, and scoring layer —
are updated jointly end-to-end by gradient descent ([ADA] Alg. 1 lines 1 and 15, p. 4).

**5.3** Training and inference procedures are given as explicit pseudocode: [ADA] Algorithm 1
(training, p. 4) and Algorithm 2 (inference, p. 4). Algorithm 1 samples a context set and a
target set each iteration, encodes contexts, embeds context and target inputs, computes
scores and weights, aggregates, decodes, and takes an NLL gradient step.
`PAPER-SPECIFIED`.

**5.4 Divergence between the two papers on what is scored.** [CNP] Eq. (4) scores targets
that include the conditioning set; [ADA] Eq. (8) and Alg. 1 sample `C` and `T` separately
from `D_H` without stating that they are disjoint. Neither regime matches the Track A episode
structure, which is fixed independently by freeze §3: one episode targets **one target day**,
and **all context days must precede the target issuance time**. The freeze controls; context
and target are necessarily disjoint under it. `ERCOT-APPLICATION CHOICE`. This is a
specificity gap, not a contradiction — see §7.2.

**5.5** The primary Track A metric, held-out event-period Gaussian NLL (freeze §7), is the
same functional form as the training objective in [ADA] Eq. (8). `PAPER-SPECIFIED` that
AdaCNP trains and reports NLL ([ADA] Tables 1–2, pp. 5, 7); the choice of NLL as the Track A
*primary adjudicating* metric is freeze §7 and is controlling.

---

## 6. Leakage: why target outcomes cannot reach the weighting

This section is load-bearing for freeze §3 and freeze §9 item 6.

**6.1** In AdaCNP the weights `w_ij` depend on `x^C_i` and `x^T_j` **only**, through
`e^C_i = φ_ω(x^C_i)` and `e^T_j = φ_ω(x^T_j)` (Eq. 10), then `s_ij = f_ψ(e^C_i, e^T_j)`
(Eq. 12), then the softmax (Eq. 13). No target outcome `y^T_j` appears anywhere in that
chain. `PAPER-SPECIFIED` — [ADA] Eqs. (9)–(13), pp. 4–5; Alg. 2 lines 4–7, p. 4, which at
inference embeds only `x^T_j`.

**6.2** Context **outcomes** `y^C_i` do enter, but only through the encoder `r_i = h_θ(x^C_i,
y^C_i)` (Eq. 5/14). This is the intended CNP conditioning path and is not leakage: context
days are historical observations that precede the target issuance time under freeze §3.
`PAPER-SPECIFIED` for the mechanism; the admissibility argument is freeze §3 and D-007.

**6.3** [ADA] p. 5, §3.4 states the sampling-side protection: "During inference, contexts are
sampled exclusively from `D_H` to prevent information leakage from the target split."
`PAPER-SPECIFIED`.

**6.4** Freeze §3 goes further than either paper: retrieval "may never use target outcomes
`y`", and freeze §9 item 6 requires a validation that target `y` **cannot** influence
retrieval. The papers describe an architecture in which `y^T` happens not to be used; they do
not require it to be structurally impossible. Making it structurally impossible is a Track A
requirement. `ERCOT-APPLICATION CHOICE`. The scaffold satisfies it by giving the retrieval
and scoring path no parameter through which a target outcome could be supplied, so the
property is enforced by the call signature rather than by discipline.

---

## 7. Paper mechanics versus the experiment freeze

Required by `NEXT_TASK.md`: compare, and stop if a material conflict exists.

### 7.1 Result

**No material conflict was found between the paper-described mechanics and
`docs/track_a/EXPERIMENT_FREEZE_v1.md`.** Implementation proceeded on that basis.

### 7.2 Item-by-item

| Freeze item | Paper stance | Assessment |
| --- | --- | --- |
| §1 aggregation is the only arm difference | [ADA] Eq. (6) vs Eq. (14) differ exactly in the weights; encoder and decoder interfaces identical ([ADA] pp. 4–5) | **Consistent** |
| §2 controlled comparison | [ADA] p. 5: decoder uses "the same interface as CNP" | **Consistent** |
| §3 episode = one target day, 24-h vector | [ADA] §4.2 p. 6: μ and σ for each of 24 hourly steps | **Consistent** |
| §3 context precedes issuance | Not addressed by either paper | Freeze is stricter; **specificity gap, not conflict** |
| §3 retrieval may use target `x`, never target `y` | [ADA] Eq. (10) embeds `x^T_j` only | **Consistent**; freeze additionally demands structural impossibility (§6.4) |
| §4 context sizes 64 / 32 | [ADA] uses 5/10/15 in the 1-D toy (p. 5, Fig. 2); real-data context size not stated | Freeze controls; **no conflict** |
| §6 24 means, 24 positive scales | [ADA] p. 6 confirms 24-step μ and σ | **Consistent** |
| §6 softplus + frozen floor | Silent in both papers (§4.4) | Freeze controls; **no conflict** |
| §7 primary metric Gaussian NLL | [ADA] trains and reports NLL (Eq. 8; Tables 1–2) | **Consistent** |
| §8 seeds | Not addressed | Freeze controls; **no conflict** |
| §9 item 5 uniform-weight reduction | Follows algebraically from Eq. (14) with `w = 1/n_c` (§2.9) | **Consistent and directly supported** |
| §10.1 fold count never hard-coded | Not addressed | Freeze and D-006 control; **no conflict** |

### 7.3 One interpretation recorded for PI visibility

AdaCNP introduces parameters that standard CNP does not have: the embedding network `φ_ω`
(Eq. 9) and the scoring layer `f_ψ` (Eq. 11). Freeze §2 requires the arms to share encoder,
decoder, normalization, optimizer settings, and seeds, and freeze §1 states that aggregation
is "the intended and only model difference."

This note treats `φ_ω` and `f_ψ` as **internal components of the aggregation mechanism**, not
as a second point of difference. The reading rests on freeze §1's own wording, which defines
the AdaCNP arm as "target-conditioned adaptive weighting of **the same context
representations**" — i.e. the encoder output `r_i` is shared and the weighting apparatus is
what distinguishes the arms. `ERCOT-APPLICATION CHOICE`.

The consequence is that AdaCNP necessarily has a larger parameter count than CNP. That is
inherent to the comparison the freeze specifies and is not, on this reading, a §2 violation.
**It is recorded here rather than buried in code** so the PI can reject the interpretation if
it is not what was intended. Nothing in this scaffold depends on the reading beyond the
existence of the adaptive module the freeze itself mandates.

#### PI determination (2026-07-29, Jonathan Fuentes) — adopted

The interpretation above is **retained**. The primary CNP-versus-AdaCNP comparison is a
**shared-backbone controlled comparison, not an equal-total-parameter comparison.** AdaCNP's
target embedding `φ_ω` and scoring network `f_ψ` are components of the adaptive aggregation
mechanism and are therefore **part of the intended model difference**, not a confound.

Consequences, binding on this and later Track A work:

- What is controlled is the **encoder and decoder architecture and initialisation**, together
  with the remaining freeze §2 items (data, partitions, context sets, normalization,
  optimizer settings, seeds). This scaffold enforces the initialisation half by constructing
  the aggregator after the shared encoder and decoder, and asserts it in test.
- **Total trainable parameter counts may differ between the arms.** A difference is expected
  and is not a defect.
- **Exact trainable parameter counts must be reported for both arms** in every future run
  manifest and result table, so the asymmetry is always visible alongside any result.
- A **parameter-matched CNP** may be introduced later **only as a secondary sensitivity**. It
  does not become the primary comparison and does not amend freeze §1 or §2.

The implementation must **not** be altered to force equal parameter counts.

---

## 8. Paper-stated tensor relationships

**8.1** Symbols and shapes stated or directly implied by the papers. `PAPER-SPECIFIED` except
where marked.

| Symbol | Shape | Source |
| --- | --- | --- |
| `x^C_i` | `R^{d_x}` | [ADA] §3.1, p. 3 (`x ∈ X ⊆ R^{d_x}`) |
| `y^C_i` | `R^{d_y}` | [ADA] §3.1, p. 3 (`y ∈ Y ⊆ R^{d_y}`) |
| `r_i` | `R^{d_r}` | [ADA] Eq. (5), p. 4; `d_r = 128` in [CNP] §4.1, p. 5 |
| `r` (uniform) | `R^{d_r}` | [ADA] Eq. (6), p. 4 |
| `e^C_i`, `e^T_j` | `R^{d_e}` | [ADA] Eqs. (9)–(10), p. 4 |
| `s_ij` | scalar | [ADA] Eqs. (11)–(12), p. 4 |
| `w_ij` | scalar in `[0,1]`, `Σ_i w_ij = 1` | [ADA] Eq. (13), p. 5 |
| `r_j` (adaptive) | `R^{d_r}` | [ADA] Eq. (14), p. 5 |
| `φ_j = (μ_j, σ²_j)` | `R^{d_y} × R^{d_y}` | [ADA] §3.2, p. 4; 24-dim per §4.2, p. 6 |

**8.2** Batched shapes used by this scaffold, with `B` episodes, `n_c` context days, `n_t`
targets, `H = 24` horizon. `ENGINEERING DEFAULT` — the papers state per-episode algebra, not
batch layout.

| Tensor | Shape |
| --- | --- |
| context `x` | `(B, n_c, d_x)` |
| context `y` | `(B, n_c, H)` |
| target `x` | `(B, n_t, d_x)` |
| target `y` | `(B, n_t, H)` |
| `r_i` | `(B, n_c, d_r)` |
| weights `w` | `(B, n_t, n_c)` |
| aggregated `r_j` | `(B, n_t, d_r)` |
| `μ`, `σ` | `(B, n_t, H)` each |

Under freeze §3 an episode has one target day, so `n_t = 1` and `H = 24`; the `n_t` axis is
retained so the weighting and decoding paths are exercised in their general form.
`ERCOT-APPLICATION CHOICE`.

**8.3** Neither paper states `d_e`, the hidden widths of `φ_ω` or `f_ψ`, activation
functions, or initialisation. `NOT SPECIFIED BY PAPER`.

---

## 9. Unspecified details requiring project engineering choices

Each item below is a decision this project must make because the papers do not fix it. None
is a scientific finding, and none may be attributed to a paper.

| # | Item | Label | Disposition in this scaffold |
| --- | --- | --- | --- |
| 9.1 | Positivity transform for the scale | `NOT SPECIFIED BY PAPER` | Fixed by freeze §6: softplus + frozen floor; floor recorded in configuration |
| 9.2 | Numerical value of the scale floor | `NOT SPECIFIED BY PAPER` | Frozen constant in `configs/track_a/`; not tuned |
| 9.3 | Temperature `τ` value | `NOT SPECIFIED BY PAPER` — [ADA] defines `τ > 0` but states no value | `ENGINEERING DEFAULT` `τ = 1.0`, recorded in configuration |
| 9.4 | Form of `f_ψ` | [ADA] p. 4 offers "lightweight MLP or a parametric similarity module" without choosing | `ENGINEERING DEFAULT`: MLP on the concatenated embedding pair |
| 9.5 | Embedding dimension `d_e` | `NOT SPECIFIED BY PAPER` | `ENGINEERING DEFAULT`, recorded in configuration |
| 9.6 | Encoder/decoder depth and width | [CNP] §4.1 p. 5 gives 3-layer encoder, `d_r = 128`, 5-layer decoder for *its* 1-D task; not for 24-h load | `ENGINEERING DEFAULT` for the synthetic scaffold; shared identically by both arms per freeze §2 |
| 9.7 | Optimizer, learning rate, batch size, stopping rule | [CNP] p. 5 names Adam only; no hyperparameters given | `ENGINEERING DEFAULT`; shared identically by both arms per freeze §2 |
| 9.8 | Normalization statistics and procedure | Not addressed by either paper | `NOT SPECIFIED BY PAPER`; deferred — no real data in this task |
| 9.9 | How the context set is selected from a candidate pool | [ADA] Alg. 1 line 3 says "sample", method unspecified | Freeze §4 controls: selected once per episode, persisted, identical for both arms |
| 9.10 | Whether context and target may overlap | [CNP] Eq. (4) includes observed points as targets; [ADA] does not state disjointness | Freeze §3 controls: context must precede target issuance, so disjoint |
| 9.11 | Weight initialisation scheme | Not addressed | `ENGINEERING DEFAULT`: framework default under a fixed seed |
| 9.12 | Tolerance for the uniform-equivalence check | Not addressed | `ERCOT-APPLICATION CHOICE`; freeze §9 item 5 requires a *recorded* tolerance |

---

## 10. What this note does not do

- It does not select a censoring treatment. Freeze §11.1 governs that, and it gates stage 4,
  not stages 1–2.
- It does not adopt any real-data convention beyond restating D-006 and D-007 as inherited.
- It does not authorise any execution stage. Freeze §10 authorises stages 1 and 2 only.
- It does not import, read, or reference any real ERCOT, EIA, weather, event, or censoring
  artifact.
