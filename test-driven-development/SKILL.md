---
name: test-driven-development
description: Test-driven development for the mojo-tiktoken repo — a from-scratch, pure-Mojo reimplementation of OpenAI's tiktoken BPE tokenizer. Use whenever you write or change observable behavior — a BPE merge step, a pattern scanner, an encode/decode path, a bug fix, a refactor of anything a test can see. Write the failing test first; reproduce a bug with a golden or fixture before fixing it. Apply on every behavioral change, not only when the user asks for tests. Covers this repo's TestSuite mechanics, the oracle / golden / tripwire patterns, and its integer-exact assertion policy (no float tolerances — token ids and byte round-trips are exact by construction). Defers to mojo-coding-guidance for how the code under test is written and to the global mojo-syntax skill for syntax.
---

# Test-Driven Development (mojo-tiktoken)

Write the failing test before the code. For a bug, reproduce it with a test —
or a golden record — *before* fixing it. Tests are proof — "looks right" is
not done. This is a BPE tokenizer, not a numerics project: there is
essentially no float math anywhere in `src/`. Encoding produces integer token
ids; decoding produces exact bytes; a pre-tokenizer split produces exact byte
spans. Every quiet bug here is a unit confusion or an off-by-one — a byte
offset used as a codepoint index, a merge applied in the wrong rank order, a
piece boundary one byte early — and every test locks one such invariant
exactly, not a coverage number.

This skill covers the *process* and *shape* of a good test here. It does not
restate how the code under test must be written — cite
[mojo-coding-guidance](../mojo-coding-guidance/SKILL.md) for that, and the
global `mojo-syntax` skill for test syntax. Project rules live in
[AGENTS.md](../../../AGENTS.md) and override this skill, including the
layering plan, the Python-containment rule, and the golden lifecycle doctrine
this skill leans on.

---

## The TestSuite mechanics

Tests are ordinary `def ... raises` functions discovered by `TestSuite` and
run with `mojo run` against the **precompiled package**
(`build/tiktoken.mojoc` — `mojo package` does not exist on `1.1.0`, only
`mojo precompile`, and `.mojopkg` support was removed in 1.1.0). Every test
file ends with the same runner, exactly as
`tests/test_harness_smoke.mojo` does today:

```mojo
from std.testing import assert_equal, assert_true, assert_raises, TestSuite
# from tiktoken.bpe import encode_bytes   # once Phase 1 lands


def test_bpe_matches_piece_tokens_golden() raises:
    var ids = encode_bytes(fixture_piece_bytes(), ranks_cl100k)
    assert_equal(ids, expected_ids_for("english_prose/3"))


def test_bad_rank_file_raises() raises:
    with assert_raises(contains="duplicate rank"):
        _ = load_ranks("tests/fixtures/dup_rank.tiktoken")


def main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()
```

Run the whole suite (the canonical green gate), or one file while iterating:

```bash
pixi run test                                                              # THE gate — build, then every tests/test_*.mojo
pixi run build && mojo run --no-optimization -I build tests/test_bpe.mojo  # one file
```

`scripts/test_all.sh` builds the package first (fail-fast on a broken
toolchain or a package that no longer compiles), then globs
`tests/test_*.mojo` in sorted order — no hand-maintained list to drift. A
stale `build/tiktoken.mojoc` is the classic "my change did nothing" trap:
after any `src/` edit, rebuild before running a single test file by hand, or
the test exercises stale code. One file per unit under test, named
`tests/test_<thing>.mojo`.

**Keep test modules small.** Mojo `#6554` is a `TestSuite`-discovery compile
stall that scales with a module's *function count*, not file size.
`tests/test_harness_smoke.mojo` has four `test_*` functions today and is fine;
a file that grows past a dozen or so is a stall risk. When a file starts
stalling, split it along the natural seam (`test_bpe.mojo`,
`test_scanner.mojo`, `test_api.mojo` rather than one giant `test_tiktoken.mojo`)
and add a `SLOW_6554` exclusion array to `scripts/test_all.sh`, exactly as the
sibling `mojo-llm-from-scratch` repo does (`AGENTS.md`'s Lessons section).
Per-test bracketed timings (`[47.0]`) are unreliable on `1.1.0` — measure
wall time with `time`, not the harness's own numbers.

**1.1.0 note:** `def`, not `fn` (a hard error now), and every new binding needs
`var` — implicit declaration no longer compiles. Benchmarks go through the
unified-closure API (`bench_function(fn, id, …)`, `iter_custom(f)`), not the
removed `benchmark.run[func]()` / `bench_function[fn]()` parameter forms.

---

## The test pyramid, by layer

`src/tiktoken/` is built foundational-to-high-level, but **arrival order
differs from layer order** (`AGENTS.md`'s layering plan): Phase 1 lands `bpe`
first, Phase 2 `unicode`, Phase 3 `scanner`, Phase 4 `api`. Each layer that
touches text has its own oracle among the three golden families already
frozen under `goldens/`:

| Layer | Phase | Tests against | Golden family |
|---|---|---|---|
| `bpe` — merges over committed ranks | 1 | one piece, encoded in isolation | `goldens/piece_tokens/<enc>.txt` |
| `unicode` — character-class tables | 2 | hand-picked codepoints per class | none — enumerate the domain instead (below) |
| `scanner` — hand-compiled `pat_str` split | 3 | the pre-tokenizer's byte spans | `goldens/pieces/<enc>.txt` |
| `api` — `encode`/`encode_ordinary`/`decode` | 4 | full text to ids, end to end | `goldens/encode/<enc>.txt` |

A layer's tests should reach for *its own* golden family first: `bpe` tests
run the merge over the pieces already listed in `piece_tokens/` and check the
ids match, without needing `scanner` to exist yet — which is exactly what
makes landing `bpe` in Phase 1, ahead of `scanner`, testable against a real
oracle rather than hand-waved. `unicode` has no golden family of its own; it
earns an *exhaustive* test instead (see below) — the character-class tables
are validated directly, not through a golden that would only prove the layer
above them.

Categories worth a dedicated file as they land: `harness_smoke` (today's one
file — proves the goldens parse from Mojo, the only real test right now),
`bpe` (merge correctness, rank ordering, byte round-trip), `unicode`
(character-class membership, boundary codepoints), `scanner` (split matches
each encoding's `pat_str`), `api` (encode/decode round-trip, special tokens,
`encode` vs `encode_ordinary`).

---

## Three patterns worth naming

### Oracle tests — compare against a trusted reference

Real tiktoken, run over the committed ranks, is the oracle — but it only ever
runs in `scripts/` and `tests/oracles/` (Python is not allowed under `src/`;
`AGENTS.md`'s containment rule). The Mojo suite never calls Python; it
compares against the oracle's *frozen output*, the goldens. A Mojo-level
oracle test decodes what the golden says to expect, runs the code under test,
and asserts equal — `test_harness_smoke.mojo`'s `ids_for` helper is the
pattern to build on once there is a real `bpe`/`scanner`/`api` to call.

If the code under test disagrees with the golden, it's wrong — the golden
already encodes tiktoken's exact behavior for that input, self-verified at
generation time (see below), so there is no ambiguity about which side is
right.

### Golden tests — freeze a known-good output, byte for byte

The goldens (`goldens/{encode,pieces,piece_tokens}/<enc>.txt`) are this
repo's golden tests at project scale: fixed corpora, a fixed oracle version,
a frozen expected output, diffed byte-for-byte by `pixi run goldens-check`.
**A red `goldens-check` after a code change indicts the change, not the
golden** — regenerating a committed golden is legitimate only when the oracle
side visibly changed (a tiktoken version bump, a deliberate corpus edit), it
happens only via `pixi run goldens` (never by hand), and it lands as its own
commit with the reason named (`AGENTS.md`'s golden lifecycle doctrine). A "no
behavior change" refactor commit that moves an expected value is lying.

### The tripwire record and the self-verifying generator

`test_harness_smoke.mojo`'s `test_tripwire_ids` and `gen_goldens.py`'s
self-verify (`AGENTS.md` calls this D9) are this repo's answer to what
overfit-one-batch is for a training loop: the cheapest possible check with
the highest chance of catching a *plausible-but-wrong* implementation.
Structural checks alone — well-formed, right record count, spans tile the
text — cannot catch a parser that reads the wrong field or a mixed-up file,
because a scrambled-but-consistent read can satisfy every structural
invariant at once.

- **The tripwire record**: hand-copy a handful of tiny known-value records
  from the committed goldens straight into the test, with the record id named
  in a comment (`test_tripwire_ids` pins `"A"` == id `32` in every encoding,
  and `edge_cases/2` — a BOM followed by `"hello"` — which differs *per
  encoding family* on purpose, so a mixed-up file read is caught, not just a
  mangled one). If a change makes the code read plausible-but-wrong bytes, the
  pinned values diverge even though every structural check still passes.
  Trust this over your reading of the code when it goes red.
- **The self-verifying generator**: `gen_goldens.py` hard-asserts, for every
  corpus record, that its own split oracle (Python `regex` against the
  `pat_str`) reproduces tiktoken's real tokenization at the token level, and
  that every split piece is a fixed point of its own split. An oracle
  disagreement dies loudly at generation time — never three phases later as a
  baffling Mojo test failure with no clue where the divergence started. Any
  new golden family or corpus should get the same shape: assert the property
  that makes the fixture trustworthy *before* freezing it, not after.

---

## Failing-test-first, applied to the golden format itself

For most code, "failing test first" means writing a test against code that
doesn't exist yet. Here it also applies one level up, to the golden format:
when a golden family gains a field or a new family is added, design the
Mojo-side parser test first, against a tiny hand-written fixture — three
lines you can read at a glance — confirm it fails against the old format,
*then* make the generator emit the new shape and confirm both sides agree.
`test_harness_smoke.mojo` is what the result looks like: it fails the moment
`gen_goldens.py` and the Mojo parser's ideas of the record format drift,
because both are exercised by the same base64-decode / int-parse / span-check
logic today.

For a bug in the tokenizer itself, reproduce it as a golden or fixture before
fixing: add the failing input as a corpus record (`data/corpora/`, regenerate
via `gen_goldens.py`) or, for something too narrow to earn a corpus entry, a
minimal literal byte string inline in the test. Confirm the Mojo output
actually disagrees with the oracle for the reason you claim, fix the code,
watch that specific case turn green.

---

## Exactness — there are no float tolerances here

**Assertions in this repo are exact.** Token ids are integers, decoded output
is bytes, piece spans are byte offsets — none of it approximates anything, so
`assert_equal`, never `assert_almost_equal`. `AGENTS.md`'s syntax contract
already says this: never compare floats with `==` for a numerical result —
but there is essentially no numerical result in this codebase to compare in
the first place.

| Contract | Assert |
|---|---|
| `encode_ordinary(text) == oracle ids` | `assert_equal` on the full `List[Int]` |
| `decode_bytes(ids) == original bytes` | `assert_equal`, byte for byte — `decode_bytes` never round-trips through `String` (arbitrary ids can be invalid UTF-8) |
| pre-tokenizer piece spans | `assert_equal` on `(start, end)`; spans are contiguous and tile the text exactly |
| a rank / token id / codepoint width | `assert_equal`, plain integer comparison |
| corpora / rank-file provenance | `assert_equal` on the sha256 hex digest string |
| a named error path | `assert_raises(contains="...")`, pinning the message substring |

A test that can only pass with a tolerance is a finding about the code, not a
reason to add one. **Loosening an assertion (or a golden) to make a red test
green is an Ask-first action** (`AGENTS.md`) — a widened check almost always
hides a real regression, because there is no encoding noise here to hide
behind.

The one place a float legitimately appears is `benchmarks/` throughput
(MB/s) — those numbers are **printed and recorded, never asserted**;
`benchmarks/baseline.json` is explicitly exempt from `goldens-check` because
it's a reference point, not a gate.

---

## Determinism and enumeration

- Encoding and decoding are pure functions of `(text, ranks)` — no seed, no
  RNG to thread through. A test that can't reproduce its input can't localize
  a failure, so keep unit-test inputs literal and inline; reach for a corpus
  record only when the golden's own provenance matters to the check.
- BPE merge order must be deterministic given the ranks. If two candidate
  merges ever tie, the tie-break rule is part of the contract, not an
  implementation detail — a test pinning a specific tie case is exact, not
  incidental.
- Where a domain is small and enumerable — the 256 leading bytes of a UTF-8
  sequence, a character-class table's boundary codepoints — enumerate it
  rather than sampling. A loop bound that quietly stops short of the full
  domain is a finding in review, not a style choice; it's how a wrong
  category table survives Phase 2 and turns into a baffling Phase 3
  `scanner` bug.
- Keep tests independent: no shared mutable state between tests, and no test
  writes under `goldens/`, `data/`, or `tests/fixtures/` — those are frozen
  inputs, not scratch space.

---

## Process

1. **Write the failing test first.** For a bug, reproduce it (Prove-It): add
   the case as a golden/fixture, confirm the test fails *for the reason you
   claim*, then the fix makes it pass. A bug fix without a test that would
   have caught it is not done.
2. **Smallest input that shows the behavior.** A 3-byte piece, a single BOM
   plus `"hello"`, one merge rule — not a full corpus record when a one-off
   literal proves the same point faster and reads clearer in review.
3. **One invariant per test**, named for what it locks
   (`test_bpe_matches_piece_tokens_golden`, not `test_bpe`).
4. **Reach for the layer's own golden family** (`piece_tokens` for `bpe`,
   `pieces` for `scanner`, `encode` for `api`) instead of re-deriving expected
   output by hand — the goldens are already the oracle, self-verified at
   generation time.
5. **Run the floor** — `pixi run fmt`, `pixi run test` (or `pixi run ci` for
   the full chain, including `goldens-check`) — before declaring done.

---

## Checklist

- [ ] Test written *before* the code (or before the fix, for a bug)
- [ ] It fails without the change, passes with it
- [ ] Smallest input that demonstrates the behavior
- [ ] Assertions are exact (`assert_equal` on ids/bytes/spans) — no tolerance
      anywhere; named errors use `assert_raises(contains="...")`
- [ ] New behavior checked against the layer's own golden family where one
      exists (`piece_tokens` / `pieces` / `encode`)
- [ ] A new golden-format field or family gets a self-verify assertion in the
      generator, mirroring `gen_goldens.py`'s D9 checks
- [ ] A refactor commit does not move a golden or a tripwire's pinned value
- [ ] Test module stays small (function count, not just file size) — split
      and add to `SLOW_6554` in `scripts/test_all.sh` if it starts stalling
- [ ] `pixi run test` green; the new file follows `tests/test_<thing>.mojo`
