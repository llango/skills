---
name: code-review-and-quality
description: Multi-axis code review for the mojo-tiktoken repo before merge — your own code, another agent's, or a phase branch. Adds oracle-fidelity/exhaustiveness, syntax-drift, and performance-honesty checks on top of the standard correctness / readability / architecture review. Use whenever you are about to merge, or when asked "is this ready?", "review this", "check this", "look this over". Reviewing AI-generated Mojo is a stronger trigger, not a weaker one — obsolete syntax, plausible-but-wrong merge semantics, and sampled "exhaustive" tests are the dominant failure modes.
---

# Code Review & Quality (mojo-tiktoken)

Multi-axis review for this repo. The product is **a tokenizer provably
identical to tiktoken, then fast** — so a review here checks two things a
generic reviewer misses: that the *semantics are exactly the oracle's, proven
without sampling*, and that any *speed claim is honest*. The output is a
**structured Markdown report** — findings grouped by severity, each with a
`file:line` reference and a quoted snippet, then a clear verdict.

This is the *review* moment. Companion skills own the *production* rules; when
a finding is "this violates rule X", **cite the owning skill, don't restate it**:

- [mojo-coding-guidance](../mojo-coding-guidance/SKILL.md) — byte discipline,
  exactness, named errors, allocation, the performance doctrine.
- [test-driven-development](../test-driven-development/SKILL.md) —
  failing-test-first, golden/doll-house/exhaustive patterns, exact equality.
- [git-conventions](../git-conventions/SKILL.md) — commit shape, scope,
  golden provenance in messages, no-AI-attribution.
- [improve-architecture](../improve-architecture/SKILL.md) — layering, seams,
  module depth.
- the global **`mojo-syntax`** skill — the authority on current Mojo syntax.

Project rules live in [AGENTS.md](../../../AGENTS.md) and override this skill.
The triage prompts below name *what to look for*; they are not the rules.

---

## Before reading a line

1. **Reproduce the floor.** Run the chain yourself, in order:
   `pixi run fmt`, `pixi run encodings-check`, `pixi run goldens-check`,
   `pixi run test` — or `pixi run ci`, which is the same chain, fail-fast
   (AGENTS.md defines it). A red gate is finding #1 — stop and report it, and
   name *which* stage went red (a hash mismatch in `encodings-check` and a
   byte diff in `goldens-check` indict different things — see axis 2).
   *Exception:* for a **docs-only diff** (Markdown, docstrings, comments —
   nothing under `src/`, `tests/`, `scripts/`, `benchmarks/`, `data/`,
   `goldens/`), a `fmt-check` and a read are enough.
2. **Read the diff with its commit messages.** Does each commit do one thing
   with an honest scope and a *why* body? Does a `refactor` commit actually
   preserve behavior (goldens untouched, no test weakened)? Does a `perf`
   commit cite its before/after numbers?
3. **Check the frozen zones.** Did the change touch committed data
   (`data/encodings/`, `data/corpora/`, `goldens/`), a pin (Mojo, tiktoken,
   regex, the UCD version), a golden/rank/corpus on-disk format, or a public
   API? Those are Ask-first boundaries (AGENTS.md) — if crossed, was it raised
   *before* the commit? **Any regenerated committed data must name the
   oracle-side reason in the commit body**; "regenerated goldens" with no
   reason reads as hand-fixing a failing gate.

---

## The axes

Walk the diff once per axis. The triage prompts are starting points, not a script.

### 1. Correctness

- Does it do what the commit says, on the stated inputs and the edge inputs
  (empty piece, single byte, the whole piece being one token, a 10k-byte
  single "word", an id one past the max)?
- Off-by-one in byte offsets, loop bounds, scan direction? Integer division
  where the value is a byte count vs a codepoint count?
- Error paths: does invalid input **raise a named, located error**
  (`"ranks line N: …"`), or crash / silently produce garbage? Is the message
  pinned by an `assert_raises(contains=...)` test?

### 2. Oracle fidelity & provenance (this repo's signature axis)

- **Is the algorithm semantically tiktoken's?** For the merge: fast path fires
  only when the *entire* piece is a token; lowest rank wins; **leftmost on
  ties**; neighbor ranks recomputed after each merge; final parts mapped with
  no escape hatch. For the scanner: the hand-compiled pattern must reproduce
  `_pat_str`, including the ugly corners (contraction groups are ASCII-only
  case-insensitive; `\s+` is Unicode White_Space; possessive/lookahead
  subtleties). Verify against the spec, not against the code's own comments.
- **Is every committed byte traceable to a script and a pinned version?** A
  golden traces to `gen_goldens.py` and the tiktoken `0.12.0` header line it
  stamps into every golden file; a rank file traces to `fetch_encodings.py`
  and its pinned sha256 in `MANIFEST.txt`; a corpus traces to `gen_corpus.py`.
  A value that cannot be traced to a script plus a pinned version does not get
  committed — full stop.
- **`goldens-check` regenerates and diffs — it does not trust a hash.** If a
  change to `goldens_check.sh` (or a golden-adjacent script) makes it compare
  a hash, a size, or a sampled slice instead of regenerating every golden to a
  temp dir and diffing byte-for-byte, that's a **Critical** finding — it
  silently weakens the strongest gate in the repo. `encodings-check` is the
  hash-pinned one (rank files against `MANIFEST.txt`'s sha256s); don't let the
  two swap roles.
- **Are the generator's self-asserts hard failures, on every record?**
  `gen_goldens.py` must hard-assert, for every corpus record, that the Python
  `regex` split reproduces tiktoken's own tokenization and that every piece is
  a split fixed point — not for a sample, not as a warning. An engine
  disagreement belongs at generation time, not as a baffling Mojo failure
  later.
- **Is the harness still hermetic?** After `fetch-encodings` has run once, CI
  must touch the network only through pixi's locked install. A new script or
  CI step that downloads anything on demand is a **High** finding regardless
  of how it's justified — see AGENTS.md *Hermetic by construction*.
- **Do the test loops actually cover everything they claim?** Every golden
  record × every encoding; all 0x110000 codepoints; every invalid-UTF-8
  class. A loop bound below the domain, a silent single-encoding loop, a
  sampled subset, or a missing record-count assert is a **High** finding —
  sampling is how a wrong table ships.
- **Any tolerance, anywhere?** Ids are integers; bytes are bytes. An
  `assert_almost_equal`, a "close enough" comparison, or a skipped-record
  counter is a finding, not a fix. So is a test weakened (skip/sample/delete)
  to get green — that's an Ask-first violation.
- **Byte-level edge cases exercised, not assumed:** empty text, NUL (`U+0000`
  — a valid token in every target encoding, not an error case), CRLF,
  `U+2028`/`U+2029` (line/paragraph separator), a BOM, ZWJ sequences, and
  NFC/NFD forms of the same string. A change touching UTF-8, the scanner, or
  decode that doesn't visibly account for these is under-tested.
- **Any hand edit to generated artifacts?** Goldens, rank files, corpus
  files, and generated `.mojo` tables are regenerated by scripts only. A
  hand-edited byte in any of them is **Critical** — it breaks the provenance
  argument the whole repo stands on.
- Hand-pinned constants (entry counts, spot-checked ranks): does each carry a
  provenance comment saying where the value came from?

### 3. Readability & teaching value

- This repo backs a build-it-from-scratch write-up: would a reader follow the
  code without running it? Names carry units (`offset` is bytes, `cp` is a
  codepoint)? Any clever trick that saves three lines but hides the algorithm?
- Every module, struct, and public function has a triple-quoted
  **Google-style** docstring (`Args:` / `Returns:` / `Raises:`, short, folding
  in units / mutate / allocate / raise)? Flag `#`-comment doc blocks and any
  plan/spec reference ("Phase 3", "D2", "per the handoff") left in code,
  docstrings, or comments — those documents are unpublished; the reference
  dangles publicly.

### 4. Architecture

- Does every new import point **down** the layering
  ([AGENTS.md](../../../AGENTS.md#the-layering-plan--one-direction-only))?
  An "up" import or a cycle is a High finding — cite
  [improve-architecture](../improve-architecture/SKILL.md).
- **Python containment:** anything Python-flavored under `src/` is Critical.
  Oracle logic belongs in `scripts/` / `tests/oracles/` only.
- **Seams intact?** No caller reaching into `MergeableRanks` internals; the
  scanner API not leaking its engine choice; generated table modules holding
  data + accessors only. A leaked internal today is a blocked optimization in
  the performance phase.
- Is new code in the right home (`src/tiktoken` vs `tests` vs `scripts` vs
  `benchmarks`)? Does `__init__.mojo` re-export the intended surface and hold
  no top-level code?

### 5. Mojo currency & safety

- **Any obsolete syntax?** `fn`, `let`, `alias`, `@parameter`,
  `read`/`inout`/`owned`/`borrowed`, `InlineArray`, `__del__`, `UnsafePointer`,
  `alloc[T](n)`+`.free()`, `unsafe_ptr()`, `Variant.take()`, non-`std.` imports,
  `s[i]` string indexing — all of these are hard errors or removals on the
  pinned `1.1.0`. A build script or doc example that shells out to
  `mojo package` or writes `.mojopkg` is stale too — that subcommand doesn't
  exist and `.mojopkg` support was removed in 1.1.0; only `mojo precompile` and
  `.mojoc` (see AGENTS.md *Lessons*). Also flag a missing `var` on a new
  binding: implicit declaration no longer compiles. Cite the `mojo-syntax`
  skill. This is the most common defect in generated Mojo — check explicitly,
  including in ```mojo blocks inside docs.
- `raises` present iff the function can raise? Named errors at boundaries,
  total functions documented as total?
- Correct `.copy()` / `^` transfer for non-`ImplicitlyCopyable` types? Any
  `Pointer` owner: allocated with `alloc(Layout[T](count=n))`, explicit origin,
  holding the `Allocation` and `dealloc`-ing it in `__deinit__`, leak-tested?
- **Determinism.** Does a new or touched generator (`gen_goldens.py`,
  `gen_corpus.py`, `fetch_encodings.py`) avoid timestamps, absolute paths, and
  unsorted `dict`/`set` iteration in anything it writes? `benchmarks/baseline.json`
  is the one deliberately machine-stamped, non-deterministic file in the repo
  (AGENTS.md) — everything else committed must reproduce byte-for-byte on a
  second run.

### 6. Performance honesty (a headline axis here — after correctness)

- **A `perf` commit needs numbers:** before/after on the *same committed
  corpora*, per encoding, recorded in `notes/`. An unmeasured "optimization"
  that muddies the code is a net loss — flag it and ask for the number. A
  measured one whose golden sweep is red is just faster wrongness — Critical.
- **Per-corpus regressions:** did the ASCII fast path slow down or break the
  CJK/emoji/mixed corpora? The scoreboard is per-corpus precisely so a
  headline number can't hide a multilingual regression.
- Accidental quadratics where linear was meant; allocation inside the merge
  or scan loop; a `List` copy where a `Span` would do; a `String` round-trip
  on a bytes path; an implicit copy a `.copy()` would have made visible.
- **Scope discipline, both directions:** the layering plan
  (AGENTS.md) fixes an arrival order — `bpe` before `unicode` before
  `scanner` before `api` — so "too much" looks like a stray split/scanner
  reimplementation landing inside a `bpe`-scoped change before its own phase,
  or performance work landing inside a correctness phase. "Too little" looks
  like a naive-but-correct reference skipped as a "placeholder" instead of
  shipped and proven against the oracle. Check the diff's claimed scope
  (commit type/scope) against what it actually touches before crediting or
  flagging it.
- Benchmarks stay **printed, never gated** — a bench file asserting a
  throughput number is a flaky CI gate in the making.

---

## Reviewing AI-generated code

False confidence is the dominant failure mode. Generated Mojo tends to: emit
last-year's syntax; write a merge that looks right but ties break rightmost
(or the fast path fires on partial matches); claim a loop is exhaustive while
bounding it at 0x10000; convert bytes through `String` and corrupt invalid
UTF-8; add tests that mirror the implementation instead of the oracle; and
write commit messages with an AI trailer this repo forbids. Check each
explicitly — polish is not correctness.

---

## Severity and output

Group findings by severity; each carries `file:line` and a quoted snippet.

| Severity | Meaning |
|---|---|
| **Critical** | wrong ids/bytes, hand-edited generated data, Python under `src/`, red gate merged, perf change with red goldens |
| **High** | wrong merge/scan semantics vs the oracle, non-exhaustive "exhaustive" test, tolerance or weakened test, up-graph import, leaked seam, obsolete syntax that will break |
| **Medium** | missing test for new behavior, vague/unlocated error message, unpinned magic constant, missing provenance comment, unmeasured perf claim |
| **Low** | naming, a redundant copy, a docstring gap |
| **Nit** | subjective; label it as such |

End with a **verdict**: *approve*, *approve with nits*, or *request changes*,
and the one or two findings that gate the merge. Prefer few high-confidence
findings over a long list; a review the author trusts is one they act on.
