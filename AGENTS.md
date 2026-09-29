# AGENTS.md — mojo-tiktoken

A from-scratch, **pure-Mojo** reimplementation of OpenAI's
[tiktoken](https://github.com/openai/tiktoken) BPE tokenizer: `encode` /
`encode_ordinary` / `decode` for `gpt2`, `r50k_base`, `p50k_base`, `cl100k_base`,
and `o200k_base`, with hand-compiled pattern scanners in place of a regex engine,
chasing the throughput of the Rust core. The point is the *building* — every
layer written from the byte up, tested against Python tiktoken as an oracle.

This file is the **source of truth** for how to work in this repo. The skills
under [`.agents/skills/`](.agents/skills/) go deeper on specific moments
(coding, tests, review, architecture, git — see the Skills index at the end);
when a skill and this file disagree, **this file wins**.

## Scope and non-goals

**In scope:** applying published BPE merges (encode/decode) for the five
encodings; a byte-level BPE core over the committed `mergeable_ranks`; a
pre-tokenizer built from hand-written pattern scanners that reproduce each
encoding's split regex (`_pat_str`); special-token handling; then performance.

**Out of scope:** *learning* merges (this applies published ones, it does not
train); a runtime regex engine; new encodings beyond the five; any model or
inference code; a Python-importable module (Python is the oracle only).

## The layering plan — one direction only

`src/tiktoken/` is pure Mojo, built foundational-to-high-level. **Lower layers
never import higher ones**; a cycle is a bug.

```text
Layer 0  unicode   character-class tables (letters, numbers, marks, ...)   [Phase 2]
Layer 1  scanner   hand-compiled per-encoding split of the _pat_str        [Phase 3]
Layer 2  bpe       byte-pair merges over the committed mergeable ranks      [Phase 1]
Layer 3  api       encode / encode_ordinary / decode, special tokens        [Phase 4]
```

Arrival order differs from layer order: **Phase 1 lands `bpe` first** (it needs
only the committed ranks and a trivial splitter), Phase 2 adds `unicode`, Phase 3
the `scanner` that consumes it, Phase 4 the `api`. Phase 5 is performance, behind
benchmarks and passing tests.

The byte-pair core is real: `ranks` (the byte-string <-> rank table and its
`.tiktoken` loader) and `bpe` (`encode_piece` and `decode_bytes` over it), with
`bpe` importing `ranks` and nothing higher. The unicode layer is real too and
sits at the bottom: `utf8` (the strict codepoint decoder), `unicode_tables` (the
generated, data-only General_Category and White_Space tables), and `unicode` (the
`category` / `in_categories` / `is_whitespace` predicates over those tables,
importing only `unicode_tables`). Nothing in the unicode layer imports
ranks/bpe or vice versa. `scanner` reproduces each `_pat_str` split over the
unicode layer, and `api` — the top — composes ranks + bpe + scanner and adds
special tokens: `get_encoding` builds an `Encoding` from committed data, which
offers `encode_ordinary` / `encode` (default-strict) / `decode_bytes` / `decode`.
Nothing imports `api` except tests, tools, and benchmarks. (In **Phase 0** the
package was an intentionally EMPTY but compiling shell — the deliverable then was
the oracle harness, not tokenizer code.)

## Mojo, not Python

Mojo evolves fast and pretrained models emit obsolete syntax. **The global
`mojo-syntax` skill is the authority on Mojo syntax** — consult it before writing
or reviewing any Mojo, and prefer it over your own recollection.

The **syntax contract** for all Mojo here (same as the sibling llm repo):

- `def`, never `fn` — `fn` was removed in 1.1.0 and is now a hard parse error.
  Add `raises` explicitly when a function can raise.
- `comptime`, never `alias` or `@parameter` (the `@parameter if` / `@parameter for`
  forms are gone too; `@__parameter` only declares a legacy closure).
- `var`, never `let`, and every new binding needs `var` — implicit declaration
  is an error in 1.1.0. Argument conventions are `imm` / `mut` / `var` / `out` /
  `deinit` — never `read` / `inout` / `owned` / `borrowed` (`read` is a hard
  error in 1.1.0).
- Imports are `std.`-prefixed (`from std.testing import ...`); GPU primitives come
  from `max.gpu`, not `std.gpu`. Prelude types need no import.
- `Pointer`, not `UnsafePointer`; `Array[T, N]`, not `InlineArray[T, N]`;
  `__deinit__`, not `__del__`.
- `StringSlice` byte-slicing needs the keyword form `s[byte=i]`; there is no
  `s[i]` / `s[0:10]`. Prefer `startswith` / `removeprefix` / `split` for parsing.
- Tests use `TestSuite` discovery run with `mojo run` (`mojo test` was removed).
- No stdlib `Tensor[T]`; this project owns its types.
- Never compare floats with `==` for a numerical result. Exact equality is for
  contracts that are exact by nature (byte round-trips, integer ids, counts).

The pinned toolchain (`1.1.0`) shares the llm repo's compiler gotchas; the ones
Phase 0 actually hit are in **Lessons** below. Consult it before non-trivial Mojo.
The `1.0.0b2` → `1.1.0` bump moved spellings this repo leans on: `read`→`imm`,
`InlineArray`→`Array`, `__del__`→`__deinit__`, `alloc[T](n)`+`.free()`→
`alloc(Layout[T](count=n))`+`dealloc()`, `unsafe_ptr()`→`ptr()`,
`init_pointee_move()`→`unsafe_write()`, `List.steal_data()`→
`unsafe_take_allocation()`, `Variant.take()`→`unwrap()`, and the precompiled
package is now `.mojoc` — `.mojopkg` support was removed.

## Docstrings — Google style, triple-quoted, mandatory

**Every module, struct, and public function has a Google-style docstring.**
Triple-quoted, short (what it does and why), with `Args:` / `Returns:` / `Raises:`
folding in the four facts a caller needs — what it *reads*, what it *mutates*,
what it *allocates*, and what it *raises*. Not `#`-comment doc blocks. This is
ported from the sibling llm repo's
[mojo-coding-guidance](.agents/skills/mojo-coding-guidance/SKILL.md) skill
("Docstrings — Google style, triple-quoted, mandatory"); consult it for the full
format and a worked example.

**No plan or spec references in code, docstrings, or comments.** The working
plans under `docs/plans/` are gitignored and unpublished; "D3", "Phase 1", a
handoff section name, or any plan vocabulary must never appear in a source file.
State the reason itself — describe the architecture and the invariant, not the
document that decided them.

## Python containment — src/ is pure Mojo

**Python lives ONLY in `scripts/` and `tests/oracles/`, never under `src/`.**
This is stricter than the llm repo and it is the whole point of the project:
`src/tiktoken/` is pure Mojo from the first commit. tiktoken (the pypi package)
is the *oracle* — it appears only in `scripts/` (generators, baseline) to produce
frozen data the Mojo code is checked against. A `from tiktoken import ...` line
inside `src/` is a Mojo import of *our* package, never the Python one.

## Toolchain and the quality floor

Everything runs through **pixi** (see [pixi.toml](pixi.toml)); there is no `make`.

```bash
pixi install  # set up the environment from pixi.lock
pixi run ci   # fmt-check -> encodings-check -> unicode-check -> goldens-check -> test -> fuzz-smoke
```

**The floor before you call any change done** — all green, in this order:

```bash
pixi run fmt              # mojo format (rewrites src/ and tests/ in place)
pixi run encodings-check  # verify the committed rank files against their pinned sha256
pixi run goldens-check    # regenerate every golden to a temp dir, diff byte-for-byte
pixi run test             # build the package, then run the Mojo tests
```

`pixi run ci` chains those fail-fast and is what CI runs. The tasks:

| Task | What it is |
| ---- | ---------- |
| `fmt` / `fmt-check` | format; the `-check` spelling then `git diff --exit-code` (CI never edits) |
| `fetch-encodings` | ONE-TIME, networked: download + sha-verify the rank files, derive gpt2, write MANIFEST |
| `encodings-check` | CI gate: verify each committed rank file's sha256 against its pinned value (hermetic) |
| `fetch-unicode` | ONE-TIME, networked: download + sha-verify the pinned UCD files, write `data/unicode/` + MANIFEST |
| `unicode-check` | CI gate: verify each committed UCD file's sha256 against its pinned value + MANIFEST (hermetic) — the UCD counterpart to `encodings-check` |
| `goldens` | regenerate the encode/pieces/piece_tokens and special/decode_replace `goldens/` IN PLACE from the committed corpora — local use only |
| `unicode-tables` | regenerate the unicode goldens + `src/tiktoken/unicode_tables.mojo` IN PLACE from the committed UCD files — local use only |
| `goldens-check` | the CI gate: regenerate every golden AND the generated table module to a temp dir and diff byte-for-byte |
| `build` | `mojo precompile src/tiktoken` — the package-compiles gate |
| `test` | build the package, then run every `tests/test_*.mojo` against it |
| `fuzz-smoke` | CI gate: differential-fuzz the scanners vs the split oracle at a FIXED seed + count (deterministic, seconds) |
| `fuzz` | open-ended local differential fuzz (`pixi run fuzz --seed S --n N`) — not a gate |
| `bench-baseline` | rerun the Python throughput baseline (writes the one machine-stamped file) |
| `bench-split` | split-only MB/s per scanner family over the committed corpora — reference point, never a gate |
| `bench-encode` | full-pipeline MB/s per encoding over the committed corpora vs `baseline.json` — reference point, never a gate |

## Hermetic by construction

After `fetch-encodings` runs once, **CI touches the network only through pixi's
locked install.** The rank files (`data/encodings/`) and goldens (`goldens/`) are
committed; tiktoken comes from the lock; `gen_goldens` builds its oracle from the
committed ranks, not from the network. Do not add a CI step that downloads
anything — a download-on-demand encoding was explicitly rejected.

## The golden lifecycle — doctrine

The Mojo suite is hermetic and doll-house-scale; the *goldens* are how the
tokenizer is held to tiktoken's exact behavior. The lifecycle mirrors the llm
repo's:

- **A red `goldens-check` after a code change indicts THE CHANGE, not the
  goldens.** Regenerating (`pixi run goldens`) is legitimate ONLY when the oracle
  side *visibly* changed: a tiktoken version bump (which shows up in the pinned
  header line) or a deliberate corpus edit (which moves the header's `corpora
  sha256`). "The new number looks close enough" is never evidence.
- **Goldens are regenerated ONLY by `gen_goldens.py`, never by hand.** The same
  holds for the rank files (`fetch_encodings.py`) and the corpus
  (`gen_corpus.py`). If a value cannot be traced to a script and a pinned
  version, it does not get committed.
- The generator **self-verifies its oracle split**: for every corpus record it
  hard-asserts that the Python `regex` split reproduces tiktoken's tokenization
  at the token level and that every piece is a split fixed point. An engine
  disagreement dies at generation time, never as a baffling Mojo failure later.
- When `goldens-check` goes red, suspect in order: **(1)** nondeterminism in a
  generator (iteration order, environment leakage), **(2)** a tiktoken version
  mismatch vs the header, **(3)** byte mangling from a missing `.gitattributes`
  entry on a new path. NEVER hand-edit a golden to make it pass.

**Machine-stamped files live in `benchmarks/` and are exempt** from
`goldens-check` — they are reference points, not gates; everything else
regenerates byte-identical. The two are `benchmarks/baseline.json` (Python
tiktoken throughput) and `benchmarks/results-mojo.json` (the pure-Mojo
tokenizer's throughput); each carries a machine block because the numbers are
comparable only within one machine. `goldens-check` never looks under
`benchmarks/`, so the exemption is structural, not a special case.

## Pin policy and Ask-first boundaries

Pins are provenance, not preference. **Ask before bumping any of these:**

- **Mojo `==1.1.0`** (`pixi.toml` / `pixi.lock`). CI must match local; a bump
  can silently change valid syntax — the 1.1.0 bump removed the 1.0 deprecations
  outright (`fn`, `alias`, `read`, `InlineArray`, `.mojopkg`, the pre-`unsafe_`
  memory spellings), so pin and syntax must move together. After a bump, re-audit
  against `mojo-syntax`.
- **tiktoken `==0.12.0`** — the oracle version is part of golden provenance
  (it is in every goldens header and the encodings MANIFEST). Bumping it means
  regenerating and re-committing every golden, with the bump named as the reason.
  This includes `data/encodings/special_tokens.txt` (the special-token ids, read
  from the pinned tiktoken registry): it shares this pin, its header names the
  version, a MANIFEST section records its sha256, and `goldens-check` regenerates
  and diffs it — so a bump that moved a special id is caught mechanically.
- **regex `==2025.11.3`** — the split oracle for the `pieces/` goldens.
- **The Unicode Character Database version `16.0.0`** — the committed UCD text
  (`data/unicode/`) that the character-class tables are generated from, pinned
  by sha256 in `data/unicode/MANIFEST.txt` and echoed in every unicode golden and
  in `src/tiktoken/unicode_tables.mojo`. Bumping it means re-fetching, regenerating
  and re-committing the unicode goldens and the generated table module.

  The version is chosen to match the Unicode tables inside tiktoken's regex
  engine so this project's `\p{L}` / `\p{N}` / `\s` agree with the oracle.
  Selection evidence: pinned `tiktoken 0.12.0` (2025-10-06) requires
  `regex = "1.10.3"` (`<2.0.0`) with no committed `Cargo.lock`, so a build
  resolves the newest compatible `regex` (1.11.x) → `regex-syntax 0.8.6`, whose
  generated `general_category.rs` / `property_bool.rs` carry
  `ucd-generate ... ucd-16.0.0` / `Unicode version: 16.0.0.`. The behavioral
  referee is the text goldens plus Phase 3's differential fuzz. Full chain in
  `notes/phase-02-notes.md`.

Also Ask-first: **changing the on-disk golden/rank/corpus format**, **adding a
runtime dependency** or reaching for Python where native Mojo would do,
**weakening a test** (tolerance, skip, delete) to reach green, and **changing a
public API** used by examples/tests (`!` commit + `BREAKING CHANGE:` footer).

## Commits

Conventional Commits with a **required scope**, atomic, imperative subject ≤72
chars, a body explaining *why*. **No AI/assistant attribution anywhere** — no
`Co-Authored-By` for an AI, no "Generated with" line, no 🤖. **No internal-plan
references** (the working plans under `docs/plans/` are gitignored and unpublished
— state the reason itself, not the document). Full rules in
[git-conventions](.agents/skills/git-conventions/SKILL.md).

**The *type* is one of the fixed set** (`feat`, `fix`, `refactor`, `perf`,
`docs`, `test`, `bench`, `build`, `ci`, `chore`). `skills` is a **scope, not a
type** — a docs change to a skill is `docs(skills): …`. **Merge commits** are
exempt from the grammar.

**Scope vocabulary** (authoritative; keep in sync as modules emerge):

| Scope | Area |
| ----- | ---- |
| `scaffold` | repo skeleton, dirs, license/readme/gitignore/gitattributes |
| `encodings` | `data/encodings/` + `scripts/fetch_encodings.py` |
| `corpora` | `data/corpora/` + `scripts/gen_corpus.py` |
| `goldens` | `goldens/` + `scripts/gen_goldens.py` + `scripts/goldens_check.sh` |
| `oracle` | `scripts/oracle.py` and `tests/oracles/` (shared Python oracle plumbing) |
| `bpe` | `src/tiktoken/bpe` (Phase 1) |
| `unicode-data` | `data/unicode/` + `scripts/fetch_unicode.py` (the pinned UCD source) |
| `unicode-gen` | `scripts/gen_unicode_tables.py` (the table + goldens generator) |
| `utf8` | `src/tiktoken/utf8` (strict codepoint decoder, Phase 2) |
| `unicode` | `src/tiktoken/{unicode,unicode_tables}` (Phase 2) |
| `scanner` | `src/tiktoken/scanner` (Phase 3) |
| `api` | `src/tiktoken/api` (Phase 4) |
| `test` | test infrastructure (`scripts/test_all.sh`, `scripts/build_pkg.sh`, shared helpers) — a module's own tests use `test` + that module's scope |
| `bench` | `benchmarks/` + `scripts/bench_baseline.py` |
| `docs` | README, AGENTS.md, docstrings, `notes/` |
| `build` | `pixi.toml`, `pixi.lock`, packaging |
| `ci` | `.github/workflows/` |
| `skills` | `.agents/skills/` |

## Lessons

Accumulated the hard way; append as later phases teach more.

- **`mojo package` does not exist in 1.1.0 — only `mojo precompile`,** and
  **`.mojopkg` support was removed in 1.1.0**. `scripts/build_pkg.sh` must emit
  `tiktoken.mojoc` (not `tiktoken.mojopkg`) so `-I build` resolves
  `from tiktoken import ...`; a `.mojopkg` artifact silently stops being found.
  Importing a precompiled package also now resolves *its* recorded dependencies
  from the importing file's location.
- **`import tiktoken` on an empty package compiles and links** — an `__init__.mojo`
  with only a module docstring is a valid, importable package, which is what lets
  Phase 0 ship a compiling-but-empty `src/tiktoken/`.
- **`String` byte-slicing (`s[0:10]`, `s[i]`) is gone** — use the keyword form
  `s[byte=i]`, or parse with `startswith` / `removeprefix` / `removesuffix` /
  `split`, which is what the golden parser does. `len(String)` warns — prefer
  `.byte_length()`. `std.base64.b64decode(String)` returns `List[UInt8]`.
- **`TestSuite` per-test timings are unreliable on 1.1.0** (the bracketed
  `[47.0]` numbers can be orders of magnitude off). Measure with `time` instead.
  The #6554 discovery-table compile stall scales with a module's function count —
  keep test modules small; when a file starts stalling, split it and add it to a
  `SLOW_6554` exclusion in `scripts/test_all.sh`, exactly as the llm repo does.
- **The corpus uses LENGTH-PREFIXED record framing, not a separator.** There is
  no byte a tokenizer corpus can safely reserve as a separator — NUL (0x00) is a
  valid scalar that every target encoding tokenizes (to id 188), so a NUL
  separator would exclude a real input (an early draft's mistake). Each record is
  written `<ascii-len>\n<raw bytes>`, which represents any byte sequence including
  NUL and the empty string, while `.gitattributes -text` keeps git from
  normalizing the CRLF/U+2028/BOM bytes. Generating the corpus (not hand-typing
  it) is what makes invisible control characters byte-exact and reviewable.
- **gpt2 and r50k_base share one BPE table** (byte-identical `.tiktoken`,
  differing only in `pat_str`), so both files carry the same sha256 — expected,
  not a dedup bug.
- **The throughput baseline is corpus-shaped:** the ~10k-char single word makes
  the r50k/cl100k-family regexes emit one giant piece (a pathological O(n²)
  merge), so their MB/s is far below o200k's, which splits on case. See
  `benchmarks/baseline.json`'s note.
- **`std.base64.b64decode` ABORTS the process on malformed input** — an assert
  inside the decoder, not a catchable `Error`, so a `try`/`except` around it never
  runs. The rank loader validates base64 itself (length a multiple of four, the
  alphabet, only trailing pads) *before* decoding, which is the only way to turn a
  bad token field into a named, line-numbered error instead of a crash.
  (1.1.0 moved the ground a little: `b64decode()` now raises for a length that is
  not a multiple of four instead of reading past the end, always validates —
  drop `validate=True`, which was removed — and ignores ASCII whitespace. The
  loader still validates first: the raise is a backstop, not the contract.)
- **A custom `Dict` key needs `Copyable, Movable, Hashable, Equatable` and the
  classic `def __hash__(self) -> UInt`** (FNV-1a over the bytes works). In 1.1.0
  hashing lives in `std.hashlib` (`Hashable`, `hash()`, `Hasher`), but a
  `Hasher`-based `__hash__` is still the wrong shape here: `Hasher.update()` now
  takes an `ImmSpan[Byte, _]`, so the recursive form is `sub.__hash__(hasher)`,
  not `hasher.update(sub)`. There is still no `EqualityComparable` trait — the
  D2 `Dict[ByteKey, Int]` path worked; the sorted-array fallback was not needed.
- **User structs conforming only to `Copyable, Movable` are not
  `ImplicitlyCopyable`** — indexing them out of a `List`/`Dict` (`records[i]`,
  a dict-key insert) errors until you `.copy()`, transfer with `^`, or iterate by
  reference (`for ref rec in records:`). This bit both `ByteKey` inserts and
  `GoldenRecord` iteration.
- **Naive merge cost, measured:** `encode_piece` on the 10k-char word is ~1.6 s
  optimized (~15 s at `-O0`), emitting 7085 tokens — the O(n²) rank-scan doing a
  fresh slice + `ByteKey` hash per pair each round. Correct by design; Phase 5's
  target. Recorded in `notes/phase-01-notes.md`.
- **Shared, non-test helper modules live in `tests/` and load via `-I tests`.**
  `tests/golden_harness.mojo` holds the golden-record parser the byte-pair and
  decode suites share; the runner's `tests/test_*.mojo` glob never executes it.
- **A Mojo string literal is UTF-8; `\xNN` means codepoint U+00NN, not a raw
  byte.** Below 0x80 the two coincide (one-byte UTF-8), so a byte-blob table of
  values under 0x80 round-trips exactly and reads with `StaticString.as_bytes()[i]`
  without allocating. At or above 0x80 the literal stores the *two-byte* UTF-8 of
  U+00NN, and `s[byte=i]` on the second byte asserts (not a codepoint boundary).
  The generated `unicode_tables.mojo` keeps every blob byte below 0x80 by splitting
  any value over 127 (block indices) into two 7-bit bytes. A ~205 KB
  single-string-literal data module compiles in ~1 s with no #6554 stall — string
  literals are cheap where large `comptime` array aggregates are not.
- **A tuple return needs the explicit `-> Tuple[Int, Int]` spelling** in 1.1.0;
  the `-> (Int, Int)` shorthand fails to resolve the tuple constructor. Unpack with
  `r[0]` / `r[1]`.
- **A generated `.mojo` is subject to BOTH `fmt-check` and the goldens byte-diff,**
  so the generator must emit exactly what `mojo format` produces — keep emitted
  expressions on short lines the formatter will not rewrap, or the two gates
  contradict each other. `benchmarks/` is outside `mojo format src tests`, so
  bench files are not held to this.
- **`Array[T, N](a, b, ...)` has no variadic positional constructor** (same
  as `List`; the `InlineArray` alias was removed in 1.1.0 — write `Array`, and
  `concat()` / `repeat()` / `fill_with=` now cover the old manual-fill idioms);
  the byte-blob-plus-accessor form avoids needing one.
- **A mutated `Int` parameter must be declared `var p: Int`.** Arguments default
  to the immutable `imm` convention (spelled `read` before 1.1.0), so an in-place
  `p += ...` on a plain `p: Int` parameter fails with "expression must be
  mutable"; `var p: Int` makes it an owned, mutable copy. The scanner's run-scan
  helpers use this.
- **A `def(...) -> T` function-type parameter does not accept a named `def`.** A
  higher-order helper `def drive[f: def(List[UInt8], Int) raises -> Int](...)`
  rejects `drive[next_piece_gpt2]` ("value has type 'def next_piece_gpt2(...)'").
  Inline the loop per caller (or wrap in a closure) instead of parameterizing on
  a named function.
- **`std.time.perf_counter_ns()` returns `UInt`,** so `t1 - t0` is `UInt` and
  must be wrapped `Int(t1 - t0)` before it reaches an `Int` parameter — there is
  no implicit `UInt -> Int` conversion.
- **The Python `regex` module's bundled Unicode drifted ahead of the 16.0.0 pin,**
  so it classifies a post-16.0.0 codepoint (e.g. U+1E6C1) as a letter while the
  frozen tables — and tiktoken's regex-syntax — see it unassigned. The split
  differs but is byte-pair-token-invariant, so it hid behind gen_goldens'
  token-level self-verify until the scanner (which splits) exposed it. Resolution:
  restrict generated test inputs (random corpus + fuzzer) to codepoints on which
  `regex` and 16.0.0 agree for EVERY predicate a scanner asks — whitespace,
  `\p{L}`, `\p{N}`, and o200k's `X`/`Y` word classes, not just the coarse
  four-way class (`scripts/unicode16.py`) — so the split oracle is only consulted
  where it and the scanner share a Unicode view; no pin change, no frozen-zone
  change. Full account in `notes/phase-03-notes.md`.
- **cl100k's and o200k's letter/word prefix `[^\r\n\p{L}\p{N}]?` accepts ANY
  single non-newline non-alnum codepoint** — a space, tab, NBSP, punctuation, or
  combining mark — and attaches it to the following word (cl100k's is possessive,
  so if no letter follows the whole alternative fails; o200k's is plain and
  retries empty once, which is what lets a lone mark still match). The gpt2
  family's ` ?` prefix, by contrast, is a LITERAL space only. A single leading
  punctuation joins a word in cl100k/o200k but splits off in gpt2 — an
  equivalence worth pinning, not assuming.
- **`String(from_utf8_lossy=Span(bytes))` matches Python's `errors="replace"`
  byte-for-byte** — including the maximal-subpart counts a naive decoder gets
  wrong (an overlong `C0 80` → two U+FFFD, a surrogate `ED A0 80` → three, a
  `80 E2 41` run → FFFD FFFD 'A'). `decode` uses it instead of a hand-rolled
  replacement pass, and the generated `decode_replace/` goldens pin the equality
  exhaustively — so the FFFD semantics stay oracle-defined, never reasoned. There
  are also `String(from_utf8=...)` (validating, raises) and
  `String(unsafe_from_utf8=...)` (no check); there is no `String(bytes=...)`.
- **Importing `scanner.Span` shadows the prelude `Span`**, so
  `String(from_utf8_lossy=Span(list))` then fails to resolve (it tries the
  piece-span constructor). Alias the domain type on import
  (`from .scanner import Span as _PieceSpan`) so the prelude `Span` stays
  available for stdlib calls.
- **`MergeableRanks` exposes no maximum-rank accessor**, and `max_token_value`
  needs it for p50k_base (top rank 50280 outranks the mid-range special 50256).
  Rather than touch the frozen ranks module, the api recovers it by scanning the
  rank file's rank column (`_file_max_rank`) — no line-order assumption, one extra
  read at construction. A missing lower-surface accessor is worked around at the
  layer that needs it, not patched into a frozen module.
- **1.1.0 arity overloads resolve, but there is no signature to distinguish a
  third same-arity spelling.** `encode(text)` and `encode(text, allowed:
  List[String])` overload cleanly; the allow-all variant needs a distinct name
  (`encode_with_all_special`) because it would otherwise collide with
  `encode(text)`. The allowed-specials argument is a `List[String]` — Mojo has no
  `str | set` union, and the special sets are ≤5 elements, so linear membership is
  fine.
- **A "special id ≤ max_token_value" load check is tautological** when
  `max_token_value = max(ranks ∪ specials)` — a larger doctored id just enlarges
  the maximum. The loader instead bounds a special id to `[0, top_rank + 256]` (a
  corruption sanity band; real specials sit within ~21 of the top rank) alongside
  the genuine rank-collision and prefix-free checks.

- **SIMD in 1.1.0: the `>=` / `<=` / `==` operators on `SIMD` return a scalar
  `Bool`** (an all-lanes reduction for `if`), NOT an element-wise mask. Element-wise
  compares are the methods `.ge()` / `.gt()` / `.le()` / `.lt()` / `.eq()` /
  `.ne()`, which return `SIMD[.bool, W]` (1.1.0 lets you write the leading-dot
  form wherever the type is already known); `&` / `|` / `~` and `.reduce_and()`
  and lane subscripts then work on those. `simd_width_of` lives in `std.sys.info`
  (not `std.sys`), and a splat needs the keyword form `SIMD[dt, W](fill=v)` for
  W > 1 (bare `SIMD[dt, W](v)` errors "must be a scalar; use `fill`"). Load a
  chunk with `ptr.unsafe_load[width=W](offset)` off `list.ptr()` — `load()` and
  `unsafe_ptr()` are the deprecated spellings and still compile on 1.1.0, but
  write the new ones. The scanner's ASCII fast path is built entirely from these.
- **A struct with a defaulted comptime parameter is inferred bare in a function
  argument but must bind the parameter to be concrete as a field or return type.**
  `def f(r: MergeableRanks)` infers the backend from the argument, but
  `var _ranks: MergeableRanks` and `def build() -> MergeableRanks` fail with "not
  concrete, use '[]'"; write `MergeableRanks[]` (bind defaults) there. Inside the
  struct, reference the parameter as `Self.use_flat`, never bare.
- **Large string-literal blobs stay cheap to compile** (measured: 256 KB ~0.97 s,
  1 MB ~1.03 s, 2 MB ~1.10 s to compile-and-run) — the Phase 2 lesson holds at
  megabyte scale, so comptime-baking a rank table would not stall. But the
  measured lookup win (flat open-addressing 2.75× over the stdlib `Dict`) is a
  property of the flat-array REPRESENTATION and no-allocation lookup, available at
  runtime; baking would only additionally remove one-time load construction. The
  flat backend therefore landed at runtime behind the ranks seam; compile-time
  baking is future work in `docs/plans/perf-roadmap.md`.

## Performance knobs — comptime, fast default, reference always compiled

Every optimization is a compile-time parameter with the FAST value as the default,
and its slower reference stays compiled and selectable so a dual-path test can pin
them equal. The knobs, where they live, and how both paths are tested:

- **`scanner.split_*[simd: Bool = True]`** (and every `next_piece_*` / run
  primitive it threads through) — the SIMD ASCII fast path vs the scalar decoder.
  `tests/test_scanner_dual_path.mojo` runs `split_*[simd=False]` and
  `split_*[simd=True]` over every pieces golden.
- **`ranks.MergeableRanks[use_flat: Bool = True]` / `load_tiktoken_file[use_flat]`**
  — the flat open-addressing forward backend vs the stdlib `Dict` reference.
  `tests/test_ranks_dual_path.mojo` instantiates both and cross-checks every
  committed pair both directions.

A dual-path test that exercises only the default instantiation is a defect: name
BOTH explicitly.

These knobs are defaulted, so every CALL is unchanged — `split_gpt2(text)`,
`load_tiktoken_file(path)`, and a bare `MergeableRanks` function argument all still
resolve to the fast default, and `api`/`bpe`/`tools`/`benchmarks` never pass a
value. What DID change is the arity of the exported type names: a bare
`MergeableRanks` or `split_*` used as a FIELD or RETURN-type annotation must now
bind the defaults (`MergeableRanks[]`), because a defaulted parameter is inferred
in an argument but must be concrete in a type position. The **frozen Phase-4 public
API — `Encoding`'s methods and `get_encoding` — is byte-for-byte unchanged**; the
parameterized symbols are the lower surfaces exported for tests and tools, and the
knobs are the mechanism the dual-path discipline requires, not a contract break.

## Skills index

- [mojo-coding-guidance](.agents/skills/mojo-coding-guidance/SKILL.md) — the coding contract: byte/unit discipline, exactness, named errors, docstrings, allocation, the performance-comes-last discipline. Apply on every Mojo edit.
- [test-driven-development](.agents/skills/test-driven-development/SKILL.md) — failing-test-first, TestSuite mechanics, the golden / doll-house / exhaustive / roundtrip patterns, exact equality only.
- [code-review-and-quality](.agents/skills/code-review-and-quality/SKILL.md) — pre-merge review axes: oracle fidelity & exhaustiveness, syntax drift, performance honesty.
- [improve-architecture](.agents/skills/improve-architecture/SKILL.md) — layering and seam protection; module-deepening refactors as plan documents.
- [git-conventions](.agents/skills/git-conventions/SKILL.md) — commits, scopes, PRs, golden provenance, no-AI-attribution.
- **`mojo-syntax`** (global skill) — the authority on current Mojo syntax.
