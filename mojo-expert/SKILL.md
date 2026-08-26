---
name: mojo-expert
description: Use this skill for Mojo-specific authoring, review, migration, packaging, testing, ownership, or Python interop tasks that need current Mojo syntax and idioms. Do not use it by default for generic Python work, MAX architecture planning, or GPU optimization unless the task includes concrete Mojo code or APIs.
license: Apache-2.0
compatibility: Portable Agent Skills skill for Codex- and Claude Code-style clients. Works offline via bundled references; with network access it verifies against official sources (mojolang.org docs/releases, modular/modular stdlib) for maximum freshness.
metadata:
  version: "1.2"
  distribution: provider-agnostic
---

# Mojo Expert

Independent community-created skill. Not affiliated with or endorsed by
Modular, Inc. Mojo is a trademark of Modular, Inc.

## Purpose

Use this skill when the user needs current, Mojo-specific help:

- writing or reviewing `.mojo` code
- fixing ownership, origin, or mutability issues
- migrating older Mojo syntax to current forms
- setting up packages, imports, or tests
- calling Python from Mojo or exposing Mojo to Python

This skill is intentionally narrow. It should not trigger by default for:

- generic Python coding
- MAX architecture or product questions without Mojo code authoring
- deep GPU/kernel tuning unless the task includes Mojo code to write or debug

## Official baseline alignment

This skill incorporates the same correction intent as Modular's official skill
set:

- `mojo-syntax` baseline for modern language syntax and removed forms
- `mojo-python-interop` rules when Python and Mojo interact
- `mojo-gpu-fundamentals` patterns when authoring accelerator-targeted Mojo

Apply this baseline before relying on model priors.

Critical defaults from that baseline:

- Use `def` for new functions. Treat `fn` as legacy and avoid generating it in
  fresh code.
- Use `var` bindings (no `let`).
- Use `comptime` forms instead of removed `alias`/`@parameter if`/`@parameter for`.
- Use modern conventions (`mut`, `out`, `deinit`, `ref`) rather than
  `inout`/`borrowed`/`owned`.
- Prefer explicit `std.` imports in examples.
- Treat proposal docs as migration context, not authoritative current syntax.

## Companion subskill mode

Agent Skills does not define true nested subskills, so this skill uses a
companion pattern:

- Keep `mojo-expert` as the primary Mojo authoring/debugging skill.
- For review/audit/migration-heavy requests, switch behavior to the
  `mojo-reviewer` companion skill if it is available in the workspace.
- Preserve `mojo-expert` safety and source-priority guardrails while using that
  review mode.

## Compatibility and environment assumptions

This skill is designed to be standalone for common Mojo tasks.

- Bundled `references/` files are enough for common authoring, review, migration,
  package, and interop answers.
- If a sibling Modular checkout exists, prefer it as the freshest local source of
  truth; when network is available, official online sources
  (`mojolang.org/docs`, `mojolang.org/releases`, `modular/modular` stdlib — see
  `mojo-official-sources`) are fresher still.
- Assume the `mojo` CLI may or may not be installed. If the user asks for build,
  test, or package commands, say when those commands require a local Mojo toolchain.
- Pixi and Bazel examples are advisory patterns, not required prerequisites.
- Python interop guidance assumes the active environment provides CPython and
  the needed Python packages at runtime.
- Python extension-module APIs stabilized in Mojo v1.0.0 (use
  `@export def PyInit_<module>() abi("C")`). Still flag any surface whose
  stability is uncertain.

## Safety and reproducibility guardrails

- Default to a chat answer unless the user explicitly asks you to create or edit
  files. Do not write sample files just to demonstrate a solution.
- Do not claim code was compiled, tested, packaged, or run unless you actually
  executed the relevant command in the current environment.
- Prefer commands, imports, and APIs that are confirmed by the sibling Modular
  checkout or bundled references. If a detail is not confirmed, label it as an
  inference instead of presenting it as settled Mojo behavior.
- Avoid inventing environment variables, build flags, or repo workflows that do
  not appear in the local checkout or bundled references.
- Avoid network, package-install, or global-environment steps unless the user
  explicitly asks for setup help.
- If asked to "review", prioritize concrete findings first: syntax drift,
  ownership mistakes, package/import breakage, and interop hazards.

## Source priority

When available, use sources in this order:

1. official online sources — `mojolang.org/docs` (raw Markdown via `.md`
   suffix), `mojolang.org/releases` (version changes), and the
   `modular/modular` stdlib source under `mojo/stdlib/std/` (see
   `mojo-official-sources`)
2. local Modular manual docs and current examples
3. local stdlib source and tests
4. bundled `references/*.md` in this skill (aligned to official patterns)
5. local proposal docs only for migration or historical context

If the local Modular repo is missing, rely on the bundled references and be
clear that the answer is based on the skill's packaged guidance rather than a
fresh repo check.

## Workflow

### 1. Classify the request

- **Authoring**: new files, modules, APIs, examples
- **Review/debugging**: syntax, ownership, imports, package layout, tests
- **Migration**: older Mojo syntax or stale recommendations
- **Interop**: Python-from-Mojo or Mojo-from-Python
- **GPU**: accelerator code that should follow the official GPU fundamentals
- **Advanced**: performance-sensitive or repo-specific behavior that may need a
  live Modular checkout

### 2. Load only the needed references

Start with the smallest relevant file:

- `references/core-language.md`
- `references/ownership-and-lifecycles.md`
- `references/packages-testing-and-interop.md`
- `references/style-and-repo-idioms.md`
- `references/migrations-and-outdated-patterns.md`

Avoid loading every reference unless the task truly spans them.

### 3. Apply official correction rules before drafting

Before drafting code, enforce these checks:

- no removed syntax (`let`, `inout`, `borrowed`, `owned`, `alias`,
  `@parameter if`, `@parameter for`)
- `def` for newly generated functions
- ownership conventions are explicit when mutation or transfer occurs
- interop code uses `std.python` and current module-init patterns
- package examples include `__init__.mojo` when showing package imports

### 4. Prefer current truth over inferred or historical guidance

- Prefer documented current syntax and real examples over memory.
- Treat proposal docs as migration context, not final authority.
- If a live repo example disagrees with an older pattern, follow the current
  example and explain the drift briefly.

### 5. Verify the answer before returning it

Check for:

- explicit `std.` imports when names come from the standard library
- intentional ownership conventions such as `imm`, `mut`, `out`, or owned args
- no generated legacy syntax in new code snippets
- package layouts that include `__init__.mojo`
- realistic test layout and run commands
- Python interop caveats about environment coupling and beta surfaces
- no claims of execution or file edits that did not actually happen
- no unverified environment variables or hidden setup steps presented as facts

### 6. Communicate uncertainty honestly

Say what is confirmed and what is inferred when:

- the task depends on a repo feature not covered by bundled references
- the user asks about beta Python extension behavior
- the only support is proposal-era or historical material

## Reference guide

### `references/core-language.md`

Load for syntax modernization, removed-form replacements, ownership signatures,
struct patterns, and explicit stdlib import behavior.

### `references/ownership-and-lifecycles.md`

Load for `imm` vs `mut`, ownership transfer, constructor/destructor patterns,
and review/debugging of mutation-heavy APIs.

### `references/packages-testing-and-interop.md`

Load for package layout, `__init__.mojo`, test organization, `mojo precompile`,
Python-from-Mojo (`std.python`) and Mojo-from-Python (`PyInit_<name>`,
`PythonModuleBuilder`, `mojo.importer`) caveats.

### `references/style-and-repo-idioms.md`

Load for naming, formatting, file organization, and Modular-style repo idioms.

### `references/migrations-and-outdated-patterns.md`

Load when modernizing old code or correcting stale advice. Use it to explain
drift, then return to current syntax and examples for the final answer.

## Output expectations

When producing code or review feedback:

- keep the answer Mojo-specific and current
- prefer small concrete examples over broad theory
- distinguish standalone guidance from repo-verified guidance when it matters
- call out stale syntax, ownership bugs, package mistakes, and interop caveats
- avoid presenting proposal text or generic Python intuition as current Mojo truth
- prefer inline snippets over creating files unless the user asked for files
- for review tasks, list findings before summary

## Maintenance note

Refresh this skill when any of these change in the upstream Mojo docs or source:

- removed syntax and migration rules tracked by official Modular skills
- ownership or lifecycle rules
- package or import behavior
- Python interop APIs
- GPU authoring patterns used in official examples
- testing or repo idioms used in official examples

Re-run the evals and validation checks after those updates.

## Provider notes

- Treat this folder as the portable skill root for any Agent Skills-compatible
  client.
- Keep provider-specific files optional and additive. A Codex-style UI metadata
  file may be present under an `agents/` directory, but the skill must remain
  usable without it.
- Do not move core instructions into provider-specific config files. Keep the
  shared behavior in this `SKILL.md` and the bundled `references/` and `scripts/`
  directories.
