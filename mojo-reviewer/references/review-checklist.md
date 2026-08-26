# Mojo Review Checklist

Use this checklist for findings-first reviews.

## Syntax and migration

- New code uses `def` rather than `fn`.
- No `let` bindings in fresh rewrites.
- No removed conventions (`inout`, `borrowed`, `owned`, proposal-only forms).
- `comptime` forms used instead of removed `alias` / `@parameter if/for`.

## Ownership and mutability

- Mutation paths are explicit via `mut`.
- Constructors use `out self`.
- Ownership transfer is explicit (`^`) when needed.
- Non-`ImplicitlyCopyable` values are copied/transferred intentionally.

## Imports and package layout

- Non-prelude modules imported explicitly from `std.` paths.
- Package examples include `__init__.mojo`.
- Import paths reflect package structure, not ad-hoc same-directory assumptions.

## Interop checks

- Python-from-Mojo uses `from std.python import ...`.
- Conversion from `PythonObject` uses current constructor forms (for example `Int(py=...)`).
- Mojo-from-Python pattern includes `PyInit_<module>` and `PythonModuleBuilder`.
- Early/beta caveats called out for extension behavior changes.

## Review output checks

- Findings listed before summary.
- Severity labels are consistent and justified.
- File/line references included when available.
- No false claims about execution or test coverage.
