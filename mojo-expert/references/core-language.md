# Core Mojo Language

Use this reference for modern Mojo syntax when authoring or reviewing code.
Prefer local Modular docs/examples when available.

## Removed syntax and replacements

| Removed | Use instead |
|---|---|
| `fn` (new code) | `def` |
| `let x = ...` | `var x = ...` |
| `alias X = ...` | `comptime X = ...` |
| `@parameter if` / `@parameter for` | `comptime if` / `comptime for` |
| `borrowed` | `imm` (usually implicit) |
| `inout` | `mut` |
| `owned` arg convention | `var` argument convention |
| `inout self` in `__init__` | `out self` |
| `Stringable` / `__str__` | `Writable` / `write_to` |
| non-`std.` import paths | explicit `std.` import paths |

## Core defaults

- Use `def` in all newly generated code.
- Add `raises` explicitly when code can fail.
- Prefer explicit `std.` imports in examples.
- Use modern conventions: `imm`, `mut`, `out`, `deinit`, `ref`.

## Minimal modern example

```mojo
from std.collections import List

def mean(values: List[Float64]) -> Float64:
    var total: Float64 = 0.0
    for value in values:
        total += value
    return total / Float64(len(values))

def main() raises:
    var values: List[Float64] = [1.0, 2.0, 3.0]
    print(mean(values))
```

## Ownership and lifecycle signatures

```mojo
def __init__(out self, x: Int):
    self.x = x

def __init__(out self, *, copy: Self):
    self.x = copy.x

def __init__(out self, *, deinit move: Self):
    self.x = move.x^
```

## Struct parameter rule

Inside a struct body, use `Self.Param` for struct parameters:

```mojo
struct Container[T: Writable]:
    var data: Self.T

    def first(self) -> Self.T:
        return self.data
```

## Frequent mistakes to catch in reviews

- `fn` or `let` emitted in new code.
- `inout`/`borrowed`/`owned` conventions in fresh examples.
- missing `std.` imports for non-prelude modules.
- implicit copies of non-`ImplicitlyCopyable` values (needs `.copy()` or `^`).
