---
name: mojo-official-sources
description: Use this skill to pull the latest Mojo syntax, standard library APIs, CLI commands, and release changes from official sources instead of stale pretrained knowledge. Use when writing Mojo and unsure whether a syntax form or API is current, when asked what changed in a recent Mojo release, or when a bundled skill's guidance needs verification against mojolang.org, docs.modular.com, or the modular/modular GitHub repo.
license: Apache-2.0
compatibility: Portable Agent Skills skill for Codex- and Claude Code-style clients. Requires network access to fetch official pages.
metadata:
  version: "1.0"
  distribution: provider-agnostic
---

# Mojo Official Sources

Mojo changes quickly; pretrained knowledge and bundled references can drift.
Use this skill to verify against official sources before claiming something is
current Mojo.

## When to use

- Verify a syntax form or stdlib API against the official docs before writing
  or reviewing Mojo.
- Answer "what changed in the latest Mojo release / nightly?"
- Find the canonical official page for a manual topic, stdlib module, or CLI
  command.
- Fetch raw Markdown of any mojolang.org docs page.

## Source hierarchy

| Source | URL | Use for |
|--------|-----|---------|
| Homepage / install | https://mojolang.org/ | Version banner, install links, playground |
| Docs root | https://mojolang.org/docs/ | All manual, reference, stdlib, CLI pages |
| Releases | https://mojolang.org/releases/ | Stable + nightly versions and dates |
| LLM index | https://mojolang.org/llms.txt | All docs page URLs in one file |
| Manual | https://mojolang.org/docs/manual/ | Language fundamentals (values, pointers, functions, lifecycle) |
| Language reference | https://mojolang.org/docs/reference/ | Full grammar, keywords, operators, declarations |
| Standard library | https://mojolang.org/docs/std/ | All stdlib modules (algorithm, collections, memory, python, ...) |
| CLI | https://mojolang.org/docs/cli/ | `mojo build`, `run`, `precompile`, `repl`, `format`, `doc`, ... |
| MAX/Mojo docs | https://docs.modular.com/ | Modular Cloud, MAX, deployment docs |
| GitHub repo | https://github.com/modular/modular | Stdlib source, examples, proposals (source of truth) |

## Fetching raw content

- Append `.md` to any mojolang.org docs URL to get raw Markdown. Example:
  `https://mojolang.org/docs/manual/basics.md`
- Section LLM indexes: `https://mojolang.org/llms-manual.txt`,
  `https://mojolang.org/llms-stdlib.txt`,
  `https://mojolang.org/llms-reference.txt`, `https://mojolang.org/llms-cli.txt`.
- GitHub raw files: `https://raw.githubusercontent.com/modular/modular/main/<path>`
  (default branch is `main`).

## Version awareness

- The docs site has a version dropdown: **1.1.0** (latest stable) and **Nightly**.
- The llms.txt / docs reflect the stable version. `Nightly` documents the next
  release; a nightly-only form may not exist in the stable docs yet.
- As of 2026-09-29: stable `mojo==1.1.0` (2026-09-17), nightly
  `1.2.0.dev2026092905` (2026-09-29). Always re-check the releases page.
- Per-release changelogs live at `https://mojolang.org/releases/v<version>/`
  (e.g. v1.1.0); the index is `https://mojolang.org/releases/`. Fetch the
  changelog first when asked "what changed in version X?".
- GPU primitives moved: `std.gpu` is private (`std._gpu`) and `max.gpu` is the
  only public entry point (`/docs/std/gpu/...` redirects to the `max.gpu` API
  reference). Verify GPU APIs against `max.gpu`, not `std.gpu`.
- Default to latest stable unless the user explicitly wants nightly behavior.
- Quick version check: `python3 scripts/check_latest.py`.

## Topic map (append `.md` to any of these)

| Topic | Page |
|-------|------|
| Language basics | https://mojolang.org/docs/manual/basics/ |
| Values / ownership | https://mojolang.org/docs/manual/values/ |
| Lifetimes, origins, references | https://mojolang.org/docs/manual/values/lifetimes/ |
| Pointers | https://mojolang.org/docs/manual/pointers/ |
| Functions | https://mojolang.org/docs/manual/functions/ |
| Closures | https://mojolang.org/docs/manual/functions/closures/ |
| Lambda expressions | https://mojolang.org/docs/manual/functions/lambda/ |
| Value lifecycle | https://mojolang.org/docs/manual/lifecycle/ |
| Variables | https://mojolang.org/docs/manual/variables/ |
| Python interop | https://mojolang.org/docs/manual/python/ |
| Mojo from Python | https://mojolang.org/docs/manual/python/mojo-from-python/ |
| Python from Mojo | https://mojolang.org/docs/manual/python/python-from-mojo/ |
| Standard library | https://mojolang.org/docs/std/ |
| Testing | https://mojolang.org/docs/tools/testing/ |
| Compilation targets | https://mojolang.org/docs/tools/compilation/ |
| Stability guarantees | https://mojolang.org/docs/api-docs/stability/ |
| Roadmap | https://mojolang.org/docs/roadmap/ |

## Workflow

1. If the question is "is X current?": fetch the matching official page in raw
   Markdown form.
2. If it is "what changed recently?": fetch `https://mojolang.org/releases/`;
   a 404 or renamed form on the stable docs is itself a drift signal.
3. If it is a stdlib API: fetch `/docs/std/` or browse the GitHub stdlib source
   under `mojo/stdlib/std/` for the definitive implementation.
4. If it is a CLI or tooling question: fetch the CLI page (`mojo precompile`,
   `mojo run`, `mojo doc`, ...).
5. Trust official docs over bundled references and pretrained memory. When a
   bundled skill and the official docs disagree, follow the official docs and
   say so explicitly.
6. Cite the exact URL you fetched in the answer.

## GitHub repo layout (source of truth)

- `mojo/stdlib/` — stdlib; implementation under `mojo/stdlib/std/`
- `mojo/examples/` — official examples (gpu-intro, python-interop, life,
  layout_tensor, operators, ...)
- `mojo/proposals/` — proposals (historical context, not current truth)
- `mojo/docs/` — repo copy of docs
- `KGEN/` — Mojo compiler

See `references/official-url-map.md` for the complete page table and
`scripts/check_latest.py` for a version check against the releases page.
