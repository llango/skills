# Migrations and Outdated Patterns

Use this reference when updating older Mojo code or correcting stale advice.
Treat proposal docs as historical context only. The final answer should use
current syntax and conventions.

## Fast migration map

| Legacy form | Current form |
|---|---|
| `fn name(...)` in new code | `def name(...)` |
| `let x = ...` | `var x = ...` |
| `alias X = ...` | `comptime X = ...` |
| `@parameter if` / `@parameter for` | `comptime if` / `comptime for` |
| `borrowed` | `imm` (usually implicit) |
| `inout` | `mut` |
| `owned` convention | `var` convention |
| `inout self` in ctor | `out self` |
| `from collections import ...` | `from std.collections import ...` |
| `Stringable`/`__str__` | `Writable`/`write_to` |

## Migration workflow

### 1. Normalize syntax first

Replace removed forms and ensure all newly authored functions use `def`.

### 2. Re-check ownership behavior

Do not blindly preserve mutation logic. Decide whether the API should:

- borrow immutably (`imm`/default),
- mutate in place (`mut`), or
- consume/return ownership (`var`, `deinit`, `^`).

### 3. Re-check package/import behavior

Prefer package layout with `__init__.mojo` and package-based imports:

```text
temperature_tools/
├── __init__.mojo
└── convert.mojo
```

### 4. Re-check interop APIs

For Python-from-Mojo, use `std.python` patterns. For Mojo-from-Python, use
`PyInit_<module>` + `PythonModuleBuilder`, and mark the surface as early/beta.

## Example migration

```mojo
# Legacy shape
fn bump(xs: List[Int]) -> List[Int]:
    let ys = xs
    ys.append(1)
    return ys

# Modern rewrite
from std.collections import List

def bump(mut xs: List[Int]) raises:
    xs.append(1)
```

## Agent guidance

- Explain migration as semantic updates, not only token swaps.
- Prefer concise before/after snippets.
- If legacy intent is ambiguous, say so and pick the safest modern default.
