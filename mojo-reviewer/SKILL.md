---
name: mojo-reviewer
description: Use this skill for Mojo-focused code review and migration audits. Prioritize findings-first output, identify syntax/ownership/import/package regressions, and provide modern rewrites aligned with current Mojo conventions.
license: Apache-2.0
compatibility: Portable Agent Skills skill for Codex- and Claude Code-style clients. Optimized for review and migration tasks, not general authoring.
metadata:
  version: "1.0"
  distribution: provider-agnostic
---

# Mojo Reviewer

Independent community-created skill. Not affiliated with or endorsed by
Modular, Inc. Mojo is a trademark of Modular, Inc.

## Purpose

Use this skill when the user asks to review, audit, or migrate Mojo code:

- findings-first code review for `.mojo` files
- migration of stale syntax to current forms
- ownership/origin correctness checks
- package/import/test layout checks
- interop risk checks when Python <-> Mojo boundaries are present

Do not use this skill for generic Python review or MAX architecture-only
discussions without Mojo code.

## Review output contract

For review requests, always:

1. list concrete findings first, ordered by severity
2. provide file/line references when available
3. include corrected snippets or targeted rewrites
4. include a brief summary only after findings

If no issues are found, state that explicitly and note any residual risk areas
(for example: not compiled, no runtime coverage, no GPU test coverage).

## Source priority

When available, resolve conflicts using this order:

1. official online sources — `mojolang.org/docs` (raw Markdown via `.md`
   suffix), `mojolang.org/releases`, and the `modular/modular` stdlib source
   under `mojo/stdlib/std/` (see `mojo-official-sources`)
2. local Modular docs/examples and stdlib usage in the active checkout
3. bundled references in this skill
4. proposal docs only as migration history

Treat proposal-era material as non-authoritative for new code.

## Workflow

### 1. Classify review type

- **Syntax migration**: removed forms and stale conventions
- **Ownership review**: mutability/transfer/ref-origin issues
- **Package/import review**: `std.` imports, `__init__.mojo`, package layout
- **Interop review**: `std.python` usage and Mojo-from-Python caveats
- **Testability review**: runnable/compilable shape and command realism

### 2. Load only needed references

- `references/review-checklist.md`
- `references/migration-maps.md`

### 3. Enforce modern Mojo defaults in rewrites

- generate `def`, not new `fn`
- use `var`, not `let`
- use `comptime` replacements for removed forms
- use modern conventions (`mut`, `out`, `deinit`, `ref`)
- prefer explicit `std.` imports for non-prelude modules

### 4. Validate claims

- do not claim compile/test/run unless executed
- distinguish confirmed behavior from inference
- avoid invented flags/env/workflows

## Findings rubric

- **P0**: correctness/safety breakage likely in normal use
- **P1**: strong likelihood of malfunction, migration breakage, or API mismatch
- **P2**: quality/maintainability issues with moderate impact
- **P3**: low-risk style/clarity improvements

Use the smallest severity that still captures user impact.

## Common checks

- removed syntax (`let`, `inout`, `borrowed`, `owned`, `alias`, `@parameter if/for`)
- fresh code still using `fn`
- mutation through non-`mut` parameter
- implicit copies of non-`ImplicitlyCopyable` values
- missing `std.` import paths
- package imports without `__init__.mojo`-based structure
- interop code not using `std.python` patterns

## Companion relationship

This skill is designed to pair with `mojo-expert`:

- use `mojo-expert` for broad Mojo authoring/debugging
- switch to `mojo-reviewer` when the user asks for review/audit/migration depth

