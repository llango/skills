# Mojo Official Sources — URL Map

Verified against the official docs index (mojolang.org/llms.txt, Mojo 1.1.0,
2026-09-29). Append `.md` to any mojolang.org docs page URL to get raw
Markdown (e.g. `https://mojolang.org/docs/manual/basics.md`).

Per-release changelogs: `https://mojolang.org/releases/v<version>/` — the
URL is `/releases/v1.1.0/` (with a trailing slash), not `/releases/1.1.0`.

## Core

| Name | URL |
|------|-----|
| Homepage | https://mojolang.org/ |
| Install | https://mojolang.org/install/ |
| Docs root | https://mojolang.org/docs/ |
| Releases | https://mojolang.org/releases/ |
| LLM index (all pages) | https://mojolang.org/llms.txt |
| Manual index | https://mojolang.org/llms-manual.txt |
| Stdlib index | https://mojolang.org/llms-stdlib.txt |
| Reference index | https://mojolang.org/llms-reference.txt |
| CLI index | https://mojolang.org/llms-cli.txt |
| MAX docs | https://docs.modular.com/ |
| Modular homepage | https://www.modular.com/ |
| GitHub repo | https://github.com/modular/modular |

## Manual (https://mojolang.org/docs/manual/)

Full page list (append `.md` for raw Markdown):

- basics/ — language basics
- get-started/ — getting started
- quickstart/
- variables/ — variables
- types/ — types (built-in and collection types)
- control-flow/ — control flow
- functions/ — functions
- functions/closures/ — closures
- functions/lambda/ — lambda expressions
- structs/ — structs
- structs/operator-support/ — operator support
- structs/reference/ — references in structs
- traits/ — traits
- generics/ — generics and parameterization
- parameters/ — parameters
- values/ — values and ownership
- values/lifetimes/ — lifetimes, origins, references
- values/ownership/ — ownership and transfer semantics
- values/value-semantics/ — value semantics
- lifecycle/ — value lifecycle
- lifecycle/death/, lifecycle/initialization/, lifecycle/life/ — lifecycle details
- pointers/ — pointers and memory
- pointers/using-pointers/ — pointer usage details
- metaprogramming/ — compile-time metaprogramming
- metaprogramming/comptime-evaluation/, constraints/, materialization/, reflection/
- operators/ — operator overloading
- errors/ — errors, error handling, context managers
- packages/ — packages and imports
- python/ — Python interop
- python/mojo-from-python/ — calling Mojo from Python
- python/python-from-mojo/ — calling Python from Mojo
- python/types/ — Python types in Mojo
- python-to-mojo/ — converting Python code to Mojo
- c-ffi/ — C FFI

## Language reference (https://mojolang.org/docs/reference/)

Full grammar and semantics. Key pages:

- cheat-sheets/ — quick reference
- keywords/ — keywords
- operators/ — operators and precedence
- literals/ — literals
- types/ — built-in types
- numeric-types/ — numeric types
- expressions/ — expressions
- simple-statements/, compound-statements/ — statements
- function-declarations/, struct-declarations/, trait-declarations/ — declarations
- lambda-expressions/ — lambda syntax
- closure-declarations/ — closure syntax
- decorators/ — decorators (export, parameter, explicit-destroy, fieldwise-init, ...)
- docstrings/ — docstring format
- inline-mlir/ — inline MLIR

## Standard library (https://mojolang.org/docs/std/)

Modules (37): algorithm, atomic, base64, benchmark, bit, builtin, collections,
compile, complex, documentation, ffi, format, gpu, hashlib, io, iter,
itertools, logger, math, memory, origin, os, pathlib, prelude, pwd, python,
random, reflection, runtime, stat, subprocess, sys, tempfile, testing, time,
traits, utils.

## Tools and API docs

- tools/compilation/ — build targets, CPU/GPU selection, cross-compilation
- tools/testing/ — testing (TestSuite, assertions)
- tools/packaging/ — packaging and distribution
- tools/debugging/ — debugging
- tools/feature-toggles/, tools/notebooks/, tools/skills/
- api-docs/ — API docs home
- api-docs/stability/ — stability guarantees (SemVer, @stable markers)

## CLI (https://mojolang.org/docs/cli/)

mojo run, build, precompile, repl, format, doc, demangle, debug (each has a
page: /docs/cli/<command>/).

## GitHub repo (https://github.com/modular/modular, default branch: main)

| Path | Content |
|------|---------|
| mojo/stdlib/std/ | Stdlib implementation source (source of truth) |
| mojo/examples/ | Official examples (gpu-intro, python-interop, life, layout_tensor, operators, ...) |
| mojo/proposals/ | Proposals (historical context only) |
| mojo/docs/ | Repo copy of docs |
| KGEN/ | Mojo compiler |
| max/ | MAX platform |
| AGENTS.md, CLAUDE.md | Agent-oriented repo guidance |

Raw file pattern: https://raw.githubusercontent.com/modular/modular/main/<path>
