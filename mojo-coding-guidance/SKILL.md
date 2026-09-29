---
name: mojo-coding-guidance
description: Mojo implementation and review guidance for the mojo-tiktoken repo — how to write clear, correct, tested, allocation-conscious library Mojo for a from-scratch BPE tokenizer chasing the throughput of tiktoken's Rust core. Use every time you write, modify, refactor, or review Mojo in this codebase — byte/id exactness, named errors, docstrings, module boundaries, allocation, and the performance doctrine all matter here. Apply on every Mojo edit, not only when the user asks for "clean code" or "make it fast". Defers to the global mojo-syntax skill for language syntax and to AGENTS.md for project rules.
---

# Mojo Coding Guidance (mojo-tiktoken)

How to write library Mojo in this repo: modern, clear, correct, tested,
**byte-exact** code with a straight path to Rust-core throughput. Performance is
a headline goal of this project — and the way it is reached here is discipline,
not cleverness: a naive-but-correct reference proven against the oracle first,
then measured optimization behind benchmarks, with the goldens as the safety
net that lets the optimizer be aggressive.

**Where this applies today.** `src/tiktoken/` is Phase 0's intentionally empty,
compiling package — there is no `bpe`/`unicode`/`scanner`/`api` code yet to hold
this bar (AGENTS.md). Concretely this skill governs the Mojo that *does* exist
now (`tests/test_smoke.mojo`, `tests/test_harness_smoke.mojo`,
`src/tiktoken/__init__.mojo`'s docstring) and is the contract each later phase's
module must meet the day it lands — read it before writing `bpe` (Phase 1) just
as much as before touching today's harness tests.

## Sources of truth (read these first)

- **Language syntax → the global `mojo-syntax` skill.** Mojo evolves fast and
  pretrained models emit obsolete syntax. That skill is the authority on `def`
  vs `fn`, `comptime` vs `alias`/`@parameter`, argument conventions
  (`imm`/`mut`/`var`/`out`/`deinit` — `read` and `borrowed` were removed in
  1.1.0), `std.`-prefixed imports, lifecycle methods, traits, SIMD, strings,
  and pointers. **Do not rely on your own recollection of Mojo syntax; consult
  it.** This skill does not restate it.
- **Project rules → [AGENTS.md](../../../AGENTS.md).** The layering plan, the
  Python-containment rule, the golden lifecycle, the pin policy, the Lessons
  section, and the "Ask first" boundaries. AGENTS.md wins over this skill.
- **When in doubt, compile it.** `pixi run build`, or
  `pixi run mojo run --no-optimization -I build <file>` against the package.
  The syntax moves; a green build is the only proof a snippet is current.

The rest of this skill is the project's *coding* contract on top of that syntax.

---

## The floor

Before any Mojo change is done:

```bash
pixi run fmt   # mojo format — never hand-format, let the tool decide
pixi run ci    # the aggregate gate, fail-fast (AGENTS.md defines the chain); the file you touched must be covered and green
```

`mojo format` is the arbiter of layout. Don't argue with it in review — if it
reformats your code, that's the house style. Remember tests run against the
**precompiled package**: after a `src/` edit, `pixi run build` before running a
single test file by hand, or the test exercises stale code.

---

## Byte discipline — the most important convention

This codebase moves between five unit systems: **bytes**, **codepoints**,
**pieces**, **ranks**, and **token ids**. Most quiet tokenizer bugs are unit
confusions — a codepoint count used as a byte offset, a rank compared to an id
from a different encoding, a `String` conversion applied to bytes that are not
valid UTF-8. So every public function states its units, and every value keeps
its unit in its name.

Canonical vocabulary (keep it consistent across files):

```text
piece      one pre-tokenizer output: a byte span the merge runs inside
rank       merge priority from the .tiktoken file (== the token id in BPE)
token_id   an id the encoder emits / the decoder consumes (ids in the plural)
cp         a decoded Unicode codepoint (an integer scalar value)
offset     a BYTE offset into the input (never a codepoint index)
width      the encoded byte width of one codepoint (1..4)
```

Hard rules that follow:

- **Bytes are the ground truth.** Input scanning, piece boundaries, and decode
  output are all byte-level. `decode_bytes` returns **bytes, never `String`** —
  arbitrary id sequences produce invalid UTF-8, and a `String` round-trip would
  corrupt exactly the inputs the corpus exists to protect.
- **Never mix byte and codepoint counts.** `String` is UTF-8 and byte-indexed;
  `.byte_length()` and `.count_codepoints()` differ on non-ASCII. When both
  appear in one function, the names say which is which (`byte_len`, `n_cps`).
- **An offset travels with what it indexes.** A function returning a position
  states "byte offset into `text`" in its docstring, not just "the position".

---

## Docstrings — Google style, triple-quoted, mandatory

**Every module, struct, and public function/method carries a real triple-quoted
docstring in Google style.** Not `#`-comment doc blocks. The formatter/linter
validates them, so this is the house style, not a preference. Keep them
**short: what it does and why, nothing more.** Fold the four facts a caller
needs — **units (bytes/codepoints/ids), whether it mutates, whether it
allocates, whether it can raise** — into the sections below.

Rules:

- **Module docstring** is the first statement in the file, **before the
  imports**, and states the module's place in the layering.
- **Struct docstring** is the first statement in the struct body — usually one line.
- **Function/method docstring** is the first statement in the body, with
  `Args:` / `Returns:` / `Raises:` sections. **Omit any section that does not
  apply.** Put each argument's unit in the text; note **allocation and
  mutation** tersely in `Returns:`; document raising via `Raises:`
  (`Error: <when>`).
- Summary line starts with a capital; wrap a leading code identifier in
  backticks if it would otherwise be lowercase.
- **No plan/spec references** anywhere in docstrings or comments — no
  "Phase 1", "D3", "per the handoff", `docs/plans/…`. Those documents are
  gitignored; the reference dangles in the public repo. State the reason
  itself. External prior art ("OpenAI's tiktoken", `minbpe`, a Rust port,
  the Unicode standard) is fine to cite.

Public function — the canonical shape:

```mojo
def encode_piece(ranks: MergeableRanks, piece: Span[Byte]) raises -> List[Int]:
    """Byte-pair-merge one pre-tokenized piece into token ids.

    Applies tiktoken's rank-scan merge: repeatedly merge the adjacent pair
    with the lowest rank, leftmost on ties, until nothing is mergeable.

    Args:
        ranks: The loaded merge table; not mutated.
        piece: The piece's raw bytes (a single pre-tokenizer output).

    Returns:
        The token ids, in order. Allocates the returned list; does not
        mutate the inputs. Empty piece returns an empty list.

    Raises:
        Error: If a final part has no rank (a corrupt table that passed load).
    """
    ...
```

Comments inside dense loops are for what the code *can't* say — the
leftmost-on-ties rule, why a lookup cannot miss — never for narrating steps.

---

## Naming

Clear over clever. Types `UpperCamelCase` (`MergeableRanks`, `ByteKey`);
functions, methods, variables `snake_case` (`encode_piece`, `byte_len`);
compile-time constants `UPPER_SNAKE_CASE` (`comptime MAX_INLINE_PIECE = 32`).
Type parameters `PascalCase` (`T`, `ErrorType`); value parameters
`lower_snake_case` (`capacity`, `simd_width`) — the manual's convention.

| Concept | Name |
|---|---|
| the merge table | `ranks` (a `MergeableRanks`) |
| one pre-tokenized span | `piece` |
| emitted/consumed ids | `ids` (one: `token_id`) |
| a codepoint | `cp` |
| byte offset / encoded width | `offset` / `width` |
| an encoding's name | `encoding_name` (`"cl100k_base"`) |

Never shadow the reserved convention words `ref`, `mut`, `out`, `deinit`,
`imm`, `var` — not as parameter names, not as locals. (`read` and `borrowed`
are gone in 1.1.0; `imm` is the immutable-borrow spelling. See the `mojo-syntax`
skill for why.)

---

## Exactness correctness

This is a byte-exactness project; the subtle bugs are semantic, and the oracle
is merciless about them.

- **Ids are integers; bytes are bytes. Compare exactly, always.** There is no
  tolerance anywhere in this library — "close enough" does not exist for a
  tokenizer. If output "almost" matches a golden, the code is wrong. (See
  [test-driven-development](../test-driven-development/SKILL.md).)
- **The merge semantics are tiktoken's, precisely:** whole-piece fast path
  only when the *entire* piece is a token; otherwise lowest rank wins,
  **leftmost on ties**; neighbor ranks recomputed after each merge. An
  off-by-one in the scan direction produces golden mismatches that cluster on
  whitespace runs and long words — that signature means tie-break, not golden.
- **Invariants are enforced where they're cheapest to name.** The
  256-single-byte invariant (every encoding contains all 256 single-byte
  tokens) is verified at load — that is what makes the merge's final lookups
  infallible, so a corrupt table dies at load with a named error, not
  mid-merge. Validate at the boundary; trust inside.
- **UTF-8 handling is strict by default:** truncated sequences, stray
  continuations, overlong encodings, surrogates, and > U+10FFFF are each their
  own named rejection. Any lenient/replacement policy is a deliberate,
  documented API-level decision, never an implementation shrug.
- **Totality is a documented contract.** A function like a category lookup
  that is *total on its domain* (never raises, unassigned → a defined answer)
  says so in its docstring, and out-of-domain input is a caller-contract
  violation guarded by `debug_assert` — not an error path in the hottest loop.

---

## Error handling — named, actionable, cheap

Mojo errors are alternate return values, not unwinding exceptions — raising is
about as cheap as returning a checked `Bool`, so **there is no performance
excuse for a vague error**. `raises` is explicit: add it when a function can
fail; omit it (compiler-enforced) when it cannot — the signature is a contract
the reader relies on.

- **Every raise is NAMED and LOCATED.** The message states *what* failed, the
  *offending value*, and *where*: `"ranks line 412: duplicate rank 50256"`,
  `"decode: id 100999 out of range (max 100276; special tokens are not
  handled here)"`, `"utf8 offset 17: overlong 2-byte encoding"`. A named error
  teaches and is pinned by `assert_raises(contains=...)`; `"bad input"` does
  neither. Include what the caller should conclude when it isn't obvious.
- **Raise at the boundary, keep the core total.** Loaders and decoders
  validate exhaustively with per-case messages; the merge loop then runs on
  invariants the load already proved. Don't sprinkle re-validation through hot
  loops — name the invariant once, enforce it once, `debug_assert` it after.
- **One failure, one message shape.** All errors from one module share a
  prefix (`"ranks line N: …"`, `"utf8 offset N: …"`) so tests and humans can
  triage on sight.
- Default to the built-in `Error` with a well-shaped message. Reach for
  **typed errors** (`raises RankFileError`, a `Writable` struct) only when a
  caller genuinely branches on error kind — note a function declares at most
  one error type, and typed errors don't capture stack traces. Don't invent an
  error-type hierarchy speculatively.
- Re-raise with `raise e^` after adding context; wrap foreign errors at API
  boundaries rather than letting a low-level message leak through a public
  function whose docstring never mentioned it.
- Use `comptime assert` for invariants knowable at compile time (inside a
  function body); `debug_assert` for caller contracts on hot paths — active in
  debug builds, free in release.

---

## Memory, allocation, and the hot path

- **Say whether a function allocates** in its docstring. Allocation is the
  dominant cost in the encode hot path (the fast Rust ports win largely by
  not allocating per piece); a reader tracking performance must know without
  reading the body.
- **Know your conventions.** The default `imm` convention (spelled `read`
  before 1.1.0) is a free borrow (small trivial types ride in registers). Take
  `Span[Byte]` views instead of copying byte lists; pass `mut` to fill a
  caller's buffer; transfer with `^` at last use. Keep big types `Copyable`
  but **not** `ImplicitlyCopyable`, so every copy of a rank table or token
  list is a visible `.copy()` in review.
- Prefer the safe types (`List`, `Span`, `Array[T, N]`, `Pointer`,
  `OwnedPointer`) over raw `UnsafePointer` (a deprecated alias of `Pointer`).
  When a struct genuinely owns heap bytes, allocate with
  `alloc(Layout[T](count=n))`, hold the returned `Allocation[T]` as the field
  and `dealloc(self._alloc^)` in `__deinit__` (renamed from `__del__`), and
  prove the round-trip with a construct-and-drop test.
- Pre-size what you can: `List[Int](capacity=n)` when the bound is known;
  `Array[T, N]` (the old name was `InlineArray`) when the bound is a
  compile-time parameter (the planned stack path for short pieces). Reuse
  buffers across loop iterations instead of reallocating inside one. Note
  `List.extend()`/`resize()` now grow geometrically, so `capacity()` can
  exceed what you asked for; `reserve()` still allocates exactly.

## Performance — not yet, but not never

Performance is this project's headline goal, and it is deliberately the
**last** thing in scope: Phase 5, after `bpe`, `unicode`, `scanner`, and `api`
are correct and their goldens are green (AGENTS.md's layering plan). Nothing
in `src/` today is a hot path to optimize, and picking a SIMD/comptime
strategy in this skill file ahead of the phase that owns that decision would
be exactly the kind of unproven claim the rest of this skill asks you to
avoid — that detail belongs in the phase's own plan when it lands, not here.

What already holds, and will keep holding once Phase 5 starts:

- **No optimization before its oracle.** A scalar-correct version, proven
  against every relevant golden, comes first and stays as the reference the
  fast path is checked against. An "optimization" without a before/after
  number is a style change; one that turns a golden red is a bug, full stop.
- **Benchmark before, benchmark after**, same committed corpora, numbers
  recorded in `notes/` — printed, never asserted, never a CI gate (see
  [test-driven-development](../test-driven-development/SKILL.md)). Watch
  per-corpus numbers separately: an ASCII fast path must not hide a
  CJK/emoji regression it never measured.
- **`benchmarks/` + `scripts/bench_baseline.py`** already define the
  scoreboard (vs Python tiktoken, per encoding, per corpus) — extend that
  scoreboard rather than inventing a parallel one when Phase 5 starts.

What stays out of any future hot path on general principle: raising error
paths (keep cores total), `String` construction where bytes will do (bytes
stay bytes; a `Writer` only accepts valid UTF-8), implicit copies, and
Python anything.

---

## Module boundaries

- **One responsibility per file**, layered one direction (authoritative graph
  in [AGENTS.md](../../../AGENTS.md#the-layering-plan--one-direction-only)):
  `unicode` (with `utf8`, `unicode_tables`) → `scanner`; `ranks` → `bpe`; the
  `api` layer ties them together on top. Never import "up"; a cycle is a bug.
  Structure findings and refactor planning live in
  [improve-architecture](../improve-architecture/SKILL.md).
- **`src/` is pure Mojo.** Python exists only in `scripts/` and
  `tests/oracles/`. A `from tiktoken import ...` under `src/` is a Mojo import
  of *this* package, never the pypi oracle.
- **Generated source is a golden that happens to be source.** Files emitted by
  a generator (`unicode_tables.mojo` and successors) contain data + accessors
  only, carry a provenance header, and are **never hand-edited** — fix the
  generator and regenerate, exactly like any golden.
- **Internals behind seams.** `MergeableRanks` hides its map so the runtime
  loader and the baked fast path stay interchangeable; the scanner API must
  not leak whether it's three hand-written scanners or one specialized engine.
  If a caller can tell which backend it got, the seam has failed.
- **`__init__.mojo` is the package's public surface** — re-export the clean
  names so callers write `from tiktoken import encode_piece`, and files can
  move inside the package without breaking them. No executable top-level code.

---

## Language gotchas that bite in this repo

The `mojo-syntax` skill has the full language list; AGENTS.md **Lessons** has
the pinned-toolchain incident log (read it before non-trivial Mojo). The pin is
Mojo `1.1.0`, which finished the 1.0 deprecation cleanup — `fn`→`def` (a hard
error now, not a warning), `alias`→`comptime`, `read`/`borrowed`→`imm`,
`@parameter if/for`→`comptime if/for`, `InlineArray`→`Array`,
`__del__`→`__deinit__`, `Variant.take()`→`unwrap()`,
`alloc[T](n)`+`.free()`→`alloc(Layout[T](count=n))`+`dealloc()`, and the
precompiled package is `.mojoc`, not `.mojopkg`. The ones
that recur in byte/collection/table code:

- **`String` is UTF-8 and byte-indexed.** No `s[i]` / `s[0:10]` — the keyword
  form `s[byte=i]` is the only index. `len(s)` warns; use `.byte_length()` or
  `.count_codepoints()` (they differ!). Prefer `startswith` / `removeprefix` /
  `split` for parsing. `std.base64.b64decode(String)` returns `List[UInt8]`;
  since 1.1.0 it always validates (no `validate=` parameter — drop it) and
  ignores ASCII whitespace, so wrapped base64 text decodes directly.
- **Every binding needs `var`.** Bare `x = 1` no longer declares a variable —
  it is an error — and `x := 1` only updates one that already exists. A value
  assigned only inside branches needs a predeclared `var x: T`.
- **`List` has no variadic constructor** — bracket literals: `var v = [1, 2, 3]`.
  **Negative indices are rejected** at compile time — `lst[len(lst) - 1]`.
- **Explicit copy/transfer** for non-`ImplicitlyCopyable` types (`List`,
  `Dict`, most structs here): `.copy()` or `^`. You cannot `^` a single field
  out of a still-live aggregate — copy the field or move the whole value.
- **SIMD comparisons changed:** `==` on vectors is a scalar `Bool`; elementwise
  masks come from the named methods (`eq`, `lt`, …). Old mask code compiles
  wrong-looking or not at all — check `mojo-syntax` before writing scanner SIMD.
- **Self-qualify struct parameters** inside a struct: `var data: Self.T`.
- **Iterate `Dict` directly**: `for e in d.items(): …(e.key, e.value)` — and
  never let map iteration order leak into anything committed or golden-shaped.
- **Compiler stalls (#6554-class):** a file that takes minutes to compile —
  test modules with many functions, giant comptime aggregates — is a known
  toolchain bug. Restructure (split the file, shrink the aggregate), record
  the pattern in AGENTS.md Lessons; don't sit waiting.

---

## Review checklist for a Mojo change

- [ ] `pixi run fmt` clean, `pixi run ci` green (build + goldens + tests)
- [ ] Every public function states units (bytes/cps/ids) + mutate/allocate/raise
- [ ] Bytes never round-trip through `String`; decode paths return bytes
- [ ] All comparisons exact — no tolerance anywhere
- [ ] Every raise named and located (`module context: what + value`); tested with `assert_raises(contains=...)`
- [ ] `raises` present iff the function can raise; hot cores total, boundaries validating
- [ ] Allocating functions say so; buffers pre-sized or reused in hot loops
- [ ] Perf claims carry before/after numbers on the committed corpora; goldens green
- [ ] Imports point down the layering; `src/` pure Mojo; generated files untouched by hand
- [ ] Syntax matches `mojo-syntax` (no `fn`/`let`/`alias`/`@parameter`/`inout`/`owned`/`read`/`borrowed`); every binding has `var`
- [ ] New behavior has a test that would fail without it
