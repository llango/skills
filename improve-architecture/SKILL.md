---
name: improve-architecture
description: Explore the mojo-tiktoken codebase, surface architectural friction, and propose module-deepening refactors as actionable plan documents under docs/plans/. Use when asked to review architecture, "make this cleaner", "reduce coupling", "this file is doing too much", or to evaluate whether a module pulls its weight. Tuned to this repo's one-directional layering (unicode → scanner, ranks → bpe, joining at api), its swap-the-internals performance seams, its pure-Mojo src/ rule, and the Phase 0 reality that src/tiktoken/ is still an empty package — right now the modules worth this scrutiny are the harness scripts under scripts/. Produces a durable refactor plan, not edits — execution is a separate, approved step.
---

# Improve Architecture (mojo-tiktoken)

Explore the codebase organically, surface architectural friction, and propose
**module-deepening refactors as durable plan documents** under `docs/plans/`
(gitignored — plans are working documents, never published, never cited in
commits or code). This repo chases Rust-core throughput: here, architecture
work serves *the ability to make it fast later without breaking it* — the
seams are where the performance phase will operate, so protecting them **is**
the performance work you can do before the benchmarks say go.

A **deep module** (Ousterhout, *A Philosophy of Software Design*) has "a small
interface hiding a large implementation." Deep modules are more testable, more
navigable for humans and agents, and let you test at the boundary instead of
poking internals. This skill finds *shallow* modules — interface nearly as
complex as implementation — and this repo's higher-stakes variant: a **leaked
seam**, where callers see internals that a later phase must be free to replace.

Project rules live in [AGENTS.md](../../../AGENTS.md) and override this skill.
For the per-edit coding contract, cite
[mojo-coding-guidance](../mojo-coding-guidance/SKILL.md); this skill is about
*structure*, not line-level style.

**When it produces a plan, that plan is a document, not edits** — execution is
a separate, approved step, because refactors touch many files and each is its
own atomic commit. But don't reach for a `docs/plans/` file reflexively: a
quick structural question ("does this import point the wrong way?", "where
should this helper live?") is answered **inline**. Write a durable plan only
when the work is a genuine multi-commit refactor *and* a durable plan was
asked for (or the friction clearly warrants one) — say which you're doing
before you do it.

---

## Where the codebase actually is right now

As of Phase 0, `src/tiktoken/` is one file: `__init__.mojo` with a module
docstring — a compiling, intentionally empty package (see
[AGENTS.md](../../../AGENTS.md#the-layering-plan--one-direction-only)). Most of
the layering and seam guidance below describes the *target* shape for Phase 1
onward. Applying it to `src/` today means judging a codebase that isn't there
yet — don't manufacture findings against files that don't exist.

What *is* fair game today is the harness. `scripts/oracle.py` is shared oracle
plumbing — rank parsing, sha256 verification, and `tiktoken_ext` registry
access — that every generator imports: `gen_corpus.py`, `gen_goldens.py`,
`fetch_encodings.py`, `verify_encodings.py`, `bench_baseline.py`. That's
already a one-directional graph worth protecting (`oracle.py` sits underneath;
grep confirms none of the generators import each other), and `oracle.py`'s
`build_oracle(encodings_dir, name) -> tiktoken.Encoding` is the harness's own
deep module today: one call hides the sha256 check against
`data/encodings/<name>.tiktoken`, the `tiktoken_ext.openai_public` redirect
that swaps in our committed ranks, and the `tiktoken.Encoding` construction —
none of that leaks to the scripts that call it. Treat a generator that forks
its own rank-parsing or sha check instead of calling `oracle.py`, or
`oracle.py` growing a generator-specific special case, exactly like a layering
violation in `src/` — same discipline, different layer names. Once modules
land under `src/tiktoken/`, this skill's center of gravity moves there; until
then, `scripts/` is where an architecture pass earns its keep.

---

## The invariants to protect

### One-directional layering (the target, Phase 1 onward)

Lower layers never import higher ones, once there are layers to violate. The
intended graph — authoritative in
[AGENTS.md](../../../AGENTS.md#the-layering-plan--one-direction-only) — is:

```text
utf8, unicode_tables → unicode → scanner ─┐
                                          ├→ api
                       ranks → bpe ───────┘
```

(`ranks`/`bpe` and the `unicode`/`scanner` line are independent branches until
`api` joins them; the layer numbering in AGENTS.md is the teaching order, not
extra edges.) The first check in any architecture pass: **grep the real
`from tiktoken.` / `from .` imports and confirm every one points down.** An
"up" import or a cycle is the highest-priority finding — the fix is almost
always to move the shared thing *down*, or to invert the dependency so the
lower layer exposes a hook the higher layer fills.

### The performance seams

The Phase 5 performance work (swap internals without touching callers) only
works if these seams hold:

- **`MergeableRanks` hides its map.** The runtime `.tiktoken` loader and the
  future comptime-baked perfect-hash backend must be interchangeable behind
  one surface. Any caller that can tell which backend it got — or that
  reaches into the underlying `Dict`/key type — has broken the seam.
- **The scanner API hides its engine.** Three hand-written scanners vs one
  parameter-specialized generic engine is an implementation decision; the
  call site must not encode it.
- **Generated modules hold data + accessors only.** Logic creeping into a
  generated file (`unicode_tables.mojo` and successors) can't be regenerated
  and can't be reviewed — move it to the hand-written module above.

### Python containment

`src/tiktoken/` is pure Mojo, always. Oracle plumbing lives in `scripts/` and
`tests/oracles/`. Any structural proposal that would put Python-derived logic
under `src/` (rather than Python-*generated data*) is dead on arrival.

---

## Friction to look for

Walk the tree and the imports. Common findings, roughly by value:

1. **Up-graph imports / cycles** — as above. Always a plan item.
2. **A leaked seam** — a test asserting on `MergeableRanks` internals, an
   `api`-layer function special-casing one scanner, a caller depending on map
   iteration order. Fix the surface *now*; the performance phase pays the
   price otherwise. Today's version of the same smell: a generator reaching
   past `oracle.py` to hand-roll rank parsing or a sha256 check instead of
   calling `oracle.verified_rank_bytes` / `oracle.parse_ranks` — same fix,
   call the shared plumbing.
3. **A file owning two responsibilities.** A `bpe.mojo` that grows special-
   token handling, or a scanner that also classifies codepoints. Splitting
   usually reveals the hidden dependency (special tokens sit *above* the
   merge; classification sits *below* the scan).
4. **A shallow module.** A wrapper whose interface is as wide as its body —
   e.g. a "tokenizer" struct that forwards `scan` + `merge` and exposes both.
   Either deepen it (hide the pipeline) or inline it.
5. **A leaky public surface.** `__init__.mojo` re-exporting internal helpers,
   or callers importing past the package (`from tiktoken.bpe import
   _byte_pair_merge`) because the clean name isn't exported. Fix the surface,
   not the callers.
6. **Duplicated parsing/fixture logic across tests.** Three test files each
   re-implementing the golden-record walker — extract a shared helper the
   suite owns, don't let the fourth copy land.
7. **A struct exposing raw fields** that callers mutate directly, so an
   invariant (ranks map ↔ reverse table consistency) can't be enforced.
   Deepen behind methods.
8. **Flat pile with no boundary.** Many files in one package with no
   re-exported surface — navigational friction; the fix is a package split +
   `__init__.mojo`, not a rewrite.

---

## What "deeper" looks like here

- **Today's example is already in the harness.** `build_oracle(encodings_dir,
  name) -> tiktoken.Encoding` (`scripts/oracle.py`) is deep: one call hides
  the sha256 verification, the `tiktoken_ext` registry redirect, and the
  `Encoding` construction, and nothing about the monkeypatch trick leaks to
  `gen_goldens.py` or `fetch_encodings.py`.
- **Interface stays small, implementation grows.** Phase 1's `bpe` layer will
  earn the same shape: `encode_piece(ranks, piece) -> ids` hides the fast
  path, the rank scan, the tie-break, and the final mapping. Good — and it's
  exactly the boundary the goldens will test at.
- **Test at the boundary.** If testing a module forces you to construct its
  internals, the boundary is in the wrong place. A deep module is tested
  through its public functions on small inputs (see
  [test-driven-development](../test-driven-development/SKILL.md)).
- **The `__init__.mojo` is the contract.** Re-export the names callers should
  use so files can move inside the package without breaking
  `from tiktoken import encode_piece`.
- **Units are the interface too.** A public function whose byte-vs-codepoint
  contract is unclear is shallow *for a reader* even if the code is fine.
  Deepening sometimes just means stating the units and hiding the offset
  arithmetic.
- **Totality is depth.** `category(cp)` that is total on its domain (never
  raises, unassigned → `Cn`) is deeper than one that raises — callers need no
  error path, and the hot loop needs no branch.

### The deep modules to come

Frame deepening opportunities in `src/tiktoken/` around the four the layering
plan already names — each should end up a simple interface over a
substantial implementation:

- **`bpe`** — `encode(bytes) -> ids` over the committed rank table. The rank
  scan, tie-break, and merge loop stay internal.
- **`scanner`** — `split(text) -> pieces` over a hand-compiled DFA per
  encoding's `_pat_str`. Whether it's three hand-written scanners or one
  specialized engine must not show at the call site.
- **`unicode`** — `is_letter` / `is_number` / … over generated character-class
  tables. The table format and lookup strategy stay internal to the module
  that owns the generator.
- **`api`** — `encode` / `encode_ordinary` / `decode` over the three layers
  below it, plus special-token handling. This is the layer callers actually
  use; the other three exist to give it a small surface to stand on.

---

## The exploration → plan flow

1. **Map before judging.** While `src/tiktoken/` is still just
   `__init__.mojo` (Phase 0), map `scripts/` instead: list what each
   generator imports from `oracle.py` and confirm nothing reaches sideways
   between generators. Once modules land under `src/tiktoken/`, list them,
   read each `__init__.mojo`, and sketch the actual import graph (grep the
   import lines); compare it to the intended layering above.
2. **Collect friction**, not fixes yet. Note each smell with a `file:line`
   and one sentence on why it costs the reader, the tests, or the
   performance phase.
3. **Cluster into refactors.** Group related smells into a handful of named
   refactors, each independently shippable. A good refactor has a clear
   before → after and a way to prove behavior is unchanged — here that proof
   is free: **the golden sweeps must be byte-identical on both sides.**
4. **Write the plan** to `docs/plans/<short-name>.md`:
   - **Problem** — the friction, with evidence (`file:line`, the import that
     points up, the internal that leaked).
   - **Proposed structure** — the target layout / interface, and why it's
     deeper (or why the seam is now sealed).
   - **Migration** — the ordered atomic commits (`refactor(<scope>): …`),
     each green under `pixi run ci` on its own.
   - **Risk & proof** — what could break, and the test that guards it. Call
     out any AGENTS.md Ask-first boundary the refactor would cross (a public
     API rename → `!` commit; anything touching committed data formats →
     confirm first).
   - **Explicitly out of scope** — what you are *not* changing, so the plan
     stays reviewable.

Remember the no-internal-references rule: the plan file may cite phases and
decisions freely, but the *commits that execute it* state reasons directly —
never "per the plan".

---

## Guardrails

- **Don't rename for taste.** A rename churns `git blame` and the write-up's
  cross-references. Rename only when the current name actively misleads.
- **No premature abstraction.** Two similar scanners are cheaper to read than
  one clever generic — the one-engine-vs-three-scanners call belongs to the
  phase that has all three patterns on the table, not to a cleanup. Extract a
  shared helper on the *third* occurrence, not the second.
- **No optimization dressed up as architecture.** Perf work is a separate
  track behind benchmarks and green goldens (see the doctrine in
  [mojo-coding-guidance](../mojo-coding-guidance/SKILL.md)). The architecture
  pass *protects seams*; it does not swap backends, add SIMD, or bake tables.
- **Keep the plan small.** A plan proposing to move ten files at once is a
  plan nobody will execute safely. Prefer several small plans over one grand
  redesign.
- **Match the size of the fix to the size of the problem.** A navigational
  pile needs a package split, not a redesign; a cycle needs one dependency
  inverted, not a new layer.
