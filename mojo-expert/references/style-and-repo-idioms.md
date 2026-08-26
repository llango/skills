# Style and Repo Idioms

Use this reference when the user wants Mojo code that looks current and
Modular-style, not just code that is roughly plausible.

## Formatting and layout

- Follow `mojo format` unless the surrounding project clearly uses something else.
- Keep files focused and group related package code together.
- Put runnable examples in `main()` instead of scattering top-level executable code.

Useful commands to mention when relevant:

```bash
mojo format example.mojo
mojo doc --diagnose-missing-doc-strings -Werror -o /dev/null stdlib/src/
```

## Naming

- `snake_case` for functions and variables
- `PascalCase` for structs, traits, and enums
- `SCREAMING_SNAKE_CASE` for constants

## Small concrete example

```mojo
from std.collections import List

struct Stats:
    var values: List[Int]

    def __init__(out self, values: List[Int]):
        self.values = values

    def count(self) -> Int:
        return len(self.values)
```

## Test and package idioms

- Use package names and imports consistently with the directory layout.
- Keep tests small, direct, and close to the behavior they exercise.
- Include ownership or mutation cases when the API can modify caller-owned data.

## Agent guidance

- Prefer patterns already visible in stdlib-style examples over generic style rules.
- If the user asks for a quick snippet, keep it light but still explicit about imports and types.
