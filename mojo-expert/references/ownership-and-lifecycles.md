# Ownership and Lifecycles

Use this reference for `imm` vs `mut`, ownership transfer, and lifecycle-aware
Mojo APIs. It is safe to use standalone for common reviews and rewrites.

## Default model

- Every value has one owner at a time.
- Borrowing and mutation must be intentional.
- When in doubt, prefer a simple owned-value API or a clear `mut` parameter over
  clever reference tricks.

## Concrete examples

### `imm` for read-only access

```mojo
from std.collections import List

def total(values: List[Int]) -> Int:
    var acc = 0
    for value in values:
        acc += value
    return acc
```

### `mut` for caller-visible mutation

```mojo
from std.collections import List

def append_zero(mut values: List[Int]) raises:
    values.append(0)
```

### Owned argument when returning a new value

```mojo
from std.collections import List

def appended_one(mut values: List[Int]) raises -> List[Int]:
    values.append(1)
    return values
```

### Constructor pattern with `out`

```mojo
struct Counter:
    var value: Int

    def __init__(out self, start: Int):
        self.value = start
```

## Review checklist

When reviewing Mojo code, look for:

- mutation happening through a parameter that should be `mut`
- ownership-taking APIs being used like borrowed ones
- stale lifecycle hooks copied from older examples
- returned references whose owner may not outlive the caller

## Agent guidance

- For ordinary APIs, prefer `imm` or `mut` over advanced `ref` usage.
- Use lifecycle-heavy patterns only when the codebase already needs them.
- If you are unsure whether an API should mutate or return a new value, explain
  both choices and pick the simpler one.
