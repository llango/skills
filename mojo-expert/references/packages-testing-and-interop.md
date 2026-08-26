# Packages, Testing, and Python Interop

Use this reference for package layout, `__init__.mojo`, test structure, and
Python interoperability. These examples are intended to stand on their own even
without a local Modular checkout.

## Packages and imports

A module is a single `.mojo` file. A package is a directory containing
`__init__.mojo`.

### Minimal package layout

```text
temperature_tools/
├── __init__.mojo
└── convert.mojo
main.mojo
```

```mojo
# temperature_tools/__init__.mojo
from .convert import c_to_f
```

```mojo
# temperature_tools/convert.mojo
def c_to_f(celsius: Float64) -> Float64:
    return celsius * 9.0 / 5.0 + 32.0
```

```mojo
# main.mojo
from temperature_tools import c_to_f

def main() raises:
    print(c_to_f(21.0))
```

## Packaging

Use `mojo precompile` when the user wants a packaged artifact (the old `mojo
package` command and `.mojopkg` files were removed in v1.0.0):

```bash
mojo precompile temperature_tools -o temperature_tools.mojoc
```

Only recommend this when the user actually needs distribution or packaged reuse.

## Testing patterns

Small project-style layout:

```text
src/
  my_math/
    __init__.mojo
    ops.mojo
test/
  my_math/
    test_ops.mojo
```

Example test shape:

```mojo
from std.testing import assert_equal
from my_math.ops import inc, dec

def test_inc():
    assert_equal(inc(1), 2)

def test_dec():
    assert_equal(dec(1), 0)
```

Useful run-command patterns to mention when relevant:

- `pixi run mojo run test/my_math/test_ops.mojo` (the `mojo test` CLI command was removed; run files that drive `TestSuite` with `mojo run`)
- `pixi run tests ./stdlib/test/bit`
- `./bazelw test //mojo/stdlib/test/...`

Say explicitly when those commands are repo-specific examples rather than
portable requirements.

## Calling Python from Mojo

```mojo
from std.python import Python, PythonObject

def main() raises:
    var np = Python.import_module("numpy")
    var array = np.array(Python.list(1, 2, 3))
    print(array)

    var py_n: PythonObject = np.int64(7)
    var n = Int(py=py_n)  # keyword form for conversion from PythonObject
    print(n)
```

Important caveats:

- Mojo uses the active environment's CPython runtime.
- Python packages such as NumPy must be installed in that environment.
- `import_module()` returns a Python object wrapper; access Python members
  through that wrapper.

## Exposing Mojo to Python

High-level pattern with current bindings:

- define exported initializer: `@export def PyInit_<module>() abi("C") -> PythonObject`
- register functions/types with `PythonModuleBuilder`
- build shared library with `mojo build --emit shared-lib`
- on Python side, use `import mojo.importer` then `import <module>`

```mojo
from std.os import abort
from std.python import PythonObject
from std.python.bindings import PythonModuleBuilder

def add(a: PythonObject, b: PythonObject) raises -> PythonObject:
    return a + b

@export
def PyInit_fastmath() abi("C") -> PythonObject:
    try:
        var m = PythonModuleBuilder("fastmath")
        m.def_function[add]("add")
        return m.finalize()
    except e:
        abort(String("failed to create module: ", e))
```

Important caveats:

- This workflow is stable as of Mojo v1.0.0, but exported-type support may
  tighten over time; keep `abi("C")` explicit on `PyInit_*`.
- The Python-side import hook builds cached artifacts under `__mojocache__`.
- Type-export support may require traits such as `Writable`, and sometimes
  `Movable` or `Defaultable`.

## Agent guidance

- Prefer package examples with `__init__.mojo`, not loose same-directory files.
- For Mojo-from-Python, keep the answer high-level unless the user asks for the
  full binding surface.
- For repo-specific commands, label them as examples instead of mandatory setup.
- For new examples, avoid legacy `fn`/`let` syntax.
