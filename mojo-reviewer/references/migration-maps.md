# Mojo Migration Maps

Use these mappings when rewriting legacy snippets.

| Legacy | Current |
|---|---|
| `fn` in new code | `def` |
| `let` | `var` |
| `alias X = ...` | `comptime X = ...` |
| `@parameter if` / `@parameter for` | `comptime if` / `comptime for` |
| `borrowed` | `imm` (usually implicit) |
| `inout` | `mut` |
| `owned` arg convention | `var` arg convention |
| `inout self` ctor | `out self` |
| `Stringable` / `__str__` | `Writable` / `write_to` |
| `from collections import ...` | `from std.collections import ...` |
| `from memory import ...` | `from std.memory import ...` |

## Rewrite discipline

1. Preserve behavior before style.
2. Apply syntax replacements first.
3. Re-evaluate mutability/ownership semantics second.
4. Normalize imports/package structure third.
5. Keep rewrites minimal and testable.

## Common unsafe rewrites to avoid

- Changing mutation semantics without explanation.
- Removing `raises` from potentially failing paths.
- Migrating syntax while keeping broken import paths.
- Claiming compatibility with no compile/test signal.
