---
name: mojo-correct
description: "Use when writing, porting, reviewing, or optimizing Mojo (.mojo files): idiomatic syntax, CPU/memory perf (ownership, SIMD, vectorize/parallelize), GPU kernels (DeviceContext, TileTensor/LayoutTensor), and Mojo/Python extension modules. Targets v1.1.0, blocks stale pre-1.0 syntax (fn, alias, read/borrowed/inout/owned, @value, NDBuffer). Not for pure Python, Rust, or MAX serving/deployment."
allowed-tools: Read, Edit, Write, Grep, Glob, Bash(mojo:*), Bash(pixi:*)
---

# Mojo

Write idiomatic, correct, current Mojo. Target version: Mojo v1.1.0 (2026-09-17). Canonical docs: `mojolang.org/docs/`, changelog: `mojolang.org/releases/v1.1.0/`.

Mojo is young and fast-moving. The dominant failure mode is emitting 2023-2024-era syntax that now warns or fails to compile. The version table below is the single most important asset - apply it on every Mojo task. The second failure mode (this skill's other focus): correct-looking high-performance code that compiles but silently copies, mis-types GPU intrinsics, or breaks the extension-module ABI - see "SOTA blind spots".

## CRITICAL VERSION CONTEXT - apply first

When you see the LEFT column in code, examples, or your own memory, it is STALE - use the RIGHT column.

| Stale (avoid) | Current (use) | Notes |
|---|---|---|
| `fn` keyword | `def` | `fn` was REMOVED in 1.1.0 - it is now a hard parse error. Every function, method, and nested function is `def`. |
| `owned arg` | `var arg` | `var` means the function takes ownership. |
| `borrowed arg` | `imm arg` (or omit - it is the default) | Immutable reference convention. |
| `read arg` | `imm arg` | `read` was removed in 1.1.0 - a hard error. Use `imm`. |
| `inout arg` | `mut arg` | Mutable reference convention. |
| `__copyinit__` | `__init__(out self, *, copy: Self)` | Keyword-only `copy`. Auto-synthesized for `Copyable` types. |
| `__moveinit__` | `__init__(out self, *, deinit move: Self)` | Keyword-only `deinit move`. Auto-synthesized for `Movable` types. |
| `@value` | `@fieldwise_init` (+ derive `Copyable`, `Movable`) | `@value` superseded. |
| `@register_passable` / `@register_passable("trivial")` | `RegisterPassable` / `TrivialRegisterPassable` trait | Decorators removed; conform to the trait instead. |
| `alias X = ...` | `comptime X = ...` | `comptime` is the modern compile-time value keyword. |
| `@parameter if` / `@parameter for` | `comptime if` / `comptime for` | Both forms were REMOVED in 1.1.0. `@parameter` on a closure is now `@__parameter` and declares a *legacy* closure - don't write it; pass unified closures as runtime args. |
| `from sys import ...`, `from memory import ...` (stdlib) | `from std.sys import ...`, `from std.memory import ...` | Stdlib lives under the `std` package (`std.sys`, `std.memory`, `std.algorithm`, `std.python`, ...). `layout` is its own package, NOT `std.layout`. |
| `from std.gpu import ...` | `from max.gpu import ...` | `std.gpu` is private (`std._gpu`); `max.gpu` is the only public source of GPU primitives. |
| `from std.builtin.simd import ...` | `from std.simd import ...` | The `simd` module moved to the top level of `std`. |
| `constrained(cond, msg)` | `comptime assert cond, msg` | Must sit inside a function body, not at module/struct scope. |
| `NDBuffer` | `TileTensor` / `LayoutTensor` | `NDBuffer` removed entirely. |
| `DynamicVector` / `InlinedFixedVector` / stdlib `Tensor` | `List` / `Array[T, N]` / (no stdlib Tensor - use SIMD/List/Pointer) | Removed collection types. The `InlineArray` alias was removed in 1.1.0 - write `Array`. |
| `mojo test` CLI | `TestSuite` struct + `mojo run test_file.mojo` | `mojo test` removed 2025-10-31. |
| `from pkg import x` binds `pkg` | binds only `x` | Import semantics tightened. |
| `gpu.block.sum(...)` | `gpu.primitives.block.sum(...)` | Collective ops moved under `gpu.primitives`. |
| `thread_idx` as `UInt` | `thread_idx` as `Int` | ID accessors migrated `UInt -> Int`. |
| `lst[-1]` negative index | not supported on stdlib collections | Index from front; CPU bounds-checking is on by default. |
| `docs.modular.com/mojo/` | `mojolang.org/docs/` | Docs domain moved (301 redirects active). |
| `Variant.take()` / `.unsafe_take()` | `.unwrap()` / `.unsafe_unwrap()` | Renamed in 1.1.0. |
| `List.steal_data()` / `OwnedPointer.take()` | `.unsafe_take_allocation()` / `.into_inner()` | Renamed in 1.1.0. |
| `__del__(deinit self)` | `__deinit__(deinit self)` | Renamed; `ImplicitlyDeletable` is now `Deinitable`. |
| `MutExternalOrigin` / `StaticConstantOrigin` / `Immut*` origins | `MutUntrackedOrigin` / `ImmStaticOrigin` / `Imm*` | Origin aliases removed in 1.1.0. |
| `UnsafePointer` / `MutUnsafePointer` / `OptionalUnsafePointer` | `Pointer` / `MutPointer` / `OptionalPointer` | `UnsafePointer` is a deprecated alias; the rest were removed. |
| `alloc[T](n)` + `ptr.free()` | `alloc(Layout[T](count=n))` + `dealloc(alloc^)` | `alloc` returns a linear `Allocation[T]` the compiler forces you to dispose of. |
| `p.load()` / `p.store(v)` / `p.init_pointee_move(v)` | `p.unsafe_load()` / `p.unsafe_store(v)` / `p.unsafe_write(v)` | Only the `unsafe_`-prefixed spellings survive. |
| `memcpy()` / `memset()` / `destroy_n()` | `unsafe_memcpy()` / `unsafe_memset()` / `unsafe_destroy_n()` | Un-prefixed raw-memory forms removed in 1.1.0. |
| `@always_inline` / `@no_inline` | `@inline(.always)` / `@inline(.never)` | One `InlineLevel` value selects the policy; two disagreeing decorators are an error. |
| `DType.float32` where the type is known | `.float32` | Contextual member refs (1.1.0): `SIMD[.float32, 4]`, `.cast[.bfloat16]()`, `address_space=.SHARED`. |
| `is_trivially_copyable[T]()` | `IsTriviallyCopyable[T]` | comptime predicates in `std.traits` - drop the call parens. |
| `Atomic[DType.float32]` | `Atomic[Float32]` | `Atomic` is parameterized on a value type, not a `DType`. |
| `unsafe_ptr()` on StringLiteral/CStringSpan/Arc/Owned | `ptr()` | The old name is deprecated; these always hold a live value. |
| `as_immutable()` / `get_immutable()` / `String.as_string_slice()` | `as_imm()` / `StringSpan(s)` | Removed in 1.1.0. |
| `mojo package` / `.mojopkg` | `mojo precompile` / `.mojoc` | `.mojopkg` support removed in 1.1.0. |
| `Coroutine` / `Task` / `std.runtime.asyncrt` | (nothing - now private) | Async task API removed; `initialize_runtime()` / `parallelism_level()` moved up to `std.runtime`. |
| `Hasher.update(obj)` | `obj.__hash__(hasher)` | `update()` now takes an `ImmSpan[Byte, _]`. |

When asserting anything that may be unstable, qualify with the version (e.g., "as of v1.1.0"). Stdlib outside stabilized-API markers can still change - re-verify against the installed toolchain.

Version sensitivity: the toolchain in use may lag this target. Anything pre-1.0 (0.26.x, 1.0.0b1/b2) still accepts `fn`, `alias`, `read`, `InlineArray`, and `alloc[T](n)`, so code written for those versions looks fine there while failing on 1.1.0. Always check `mojo --version` and prefer what the installed compiler accepts over this table when they disagree.

## When to use

Trigger on: writing/porting/reviewing/optimizing `.mojo` code; Mojo structs, traits, generics, ownership, lifecycle, `comptime`/`@parameter`; Mojo error handling, testing, Python interop; Mojo performance (SIMD, `vectorize`, `parallelize`, `benchmark`); Mojo GPU kernels.

Skip unless: the task names Mojo / Modular / MAX kernels, or touches a `.mojo` file. Do NOT activate for pure Python, Rust, C++, or MAX serving/deployment config.

## Core rules (apply on every task)

Language and syntax
- Use `def`. Functions are non-raising by default; add `raises` (prefer typed: `raises MyError`) to propagate errors - omitting it is a compile error.
- Every new binding needs `var` (`var x = 1`); bare `x = 1` for a name that doesn't exist yet is an error in 1.1.0, and a walrus (`x := 1`) only updates an existing variable. Branch-only assignment needs a predeclared `var x: T`.
- Argument conventions: `imm` (default, immutable ref - `read` is gone), `mut` (mutable ref), `var` (takes ownership; pair with `^` at the call site), `ref` (parametric, advanced). Plus `out` (constructors/named results), `deinit` (destructors). `var`/`ref` are hard keywords; `imm`/`mut`/`out`/`deinit` are invalid as argument names - never use them as identifiers.
- `struct` is the workhorse: static, no inheritance, fields declared with `var` + explicit type, initialized in `__init__`. Share behavior via traits (`Copyable`, `Movable`, `Writable`, ...), not inheritance. Use `@fieldwise_init` for the field-wise constructor. Inside a struct body, qualify own parameters as `Self.T` (bare `T` errors).
- Custom iterables signal end by RAISING, not by returning `Optional`: `def __next__(mut self) raises StopIteration -> Self.Element`. The collection conforms to `Iterable` and exposes a `comptime IteratorType[...]: Iterator`. Iterate with `for item in col:` (borrow) or `for ref item in col:` (mutate). `Dict` items iterate directly - `for e in d.items(): e.key, e.value` (no `[]` deref).
- Compile-time `[parameters]` vs run-time `(arguments)` drives metaprogramming. `comptime` for constants/values, branch selection (`comptime if`), and loop unrolling (`comptime for`). `@parameter if`/`@parameter for` are removed; `@__parameter` only declares legacy closures - pass unified closures (`def f(x: Int) {mut acc}: ...`) as runtime arguments instead.
- Imports: stdlib modules are under the `std` package - `from std.sys import ...`, `import std.math`. GPU primitives come from `max.gpu` (`std.gpu` is private). The `layout` package (`LayoutTensor`, `TileTensor`) is separate, not under `std`.

## SOTA blind spots (what strong models get wrong)

These compile-fail, silently kill performance, or post-date model knowledge cutoffs. High value for an LLM inference/training engine optimized on CPU memory and GPU.

Memory and copies - the #1 silent perf killer
- Copies are NOT free and NOT implicit for most types. `List`, `Dict`, and user structs that conform only to `Copyable`/`Movable` (not `ImplicitlyCopyable`) require explicit `.copy()` or ownership transfer `^`. `var b = big_weights` or `return my_struct` errors until you write `^` or `.copy()` - this is the guardrail that stops accidental weight/KV-cache duplication. Move with `^` on last use; borrow with `imm`/`ref`; never deep-copy a tensor on a hot path.
- `Pointer` (formerly `UnsafePointer`) is non-null by design - `Bool(p)` is unavailable. For nullable storage use `OptionalPointer[T, origin]` (same layout, `None` is the null niche). As a struct field it needs an explicit origin - use `MutUntrackedOrigin` for owned heap data: `var _ptr: Pointer[Self.T, MutUntrackedOrigin]`. Allocate with `alloc(Layout[T](count=n))`, which returns an `Allocation[T]` you must dispose of (hold the `Allocation` as the field, and `dealloc(self._alloc^)` in `__deinit__`; `unsafe_leak()` only if you truly want a bare pointer). Old spellings `alloc[T](n)`, `p.free()`, `p.load()`, `p[i]` are gone or renamed `unsafe_*`.
- Pick the right pointer: `Pointer[T, mut, origin]` (safe, non-null view), `OwnedPointer[T]` (unique, Rust `Box`), `ArcPointer[T]` (refcounted shared), `Span(list)` (non-owning contiguous view - use for slices into weights/activations instead of copying).

CPU performance
- `min`/`max` are FREE FUNCTIONS in `std.math`, not SIMD methods: `from std.math import min, max; min(a, b)`. SIMD has methods `.clamp(lo, hi)`, `.select(t, f)` (per-lane via bool mask), `.reduce_add()/.reduce_max()/.reduce_min()`, `.cast[DType.x]()`.
- No implicit conversions between numeric *variables* - `Float32(my_int)`, `Int(my_uint)` explicitly. Literals ARE polymorphic and adapt to context (`var a: Float32 = 0.5`), so no wrapping needed for constants.
- Vectorize with `SIMD[.float32, size]` - write `.dtype` wherever the type is already known (contextual member refs, 1.1.0) - with `size` a power of two from `sys.simd_width_of[...]()`; raw vector loads via `ptr.load[width=N](idx)`. Use `std.algorithm` `vectorize`/`parallelize`/`elementwise` for data-parallel work, `@inline(.always)` on tiny hot functions, and parameterize over `DType`/sizes so the compiler monomorphizes. `prefetch` lives in `std.sys.intrinsics`.
- Strings are UTF-8: `len(s)` is byte length (deprecated on `String` - use `s.byte_length()` vs `s.count_codepoints()`). No slice syntax; byte access is `s[byte=i]` (returns `StringSlice`). Matters for tokenizer/vocab paths. `StaticString` is zero-allocation for compile-time constants.

GPU kernels

Skip unless: code targets an accelerator (DeviceContext, enqueue_*, kernels, TileTensor on device).
- `comptime assert tensor.flat_rank == N` is MANDATORY in any function that subscripts a `TileTensor` (kernel, host helper, CPU reference). Without it `tensor[r, c]` fails with `"invalid call to '__getitem__': lacking evidence to prove correctness"`. Derived tensors (`.tile()`, `.vectorize()`, `.distribute()`) get a NEW layout - re-assert `flat_rank` on the derived value before indexing.
- `enqueue_function` with a parameterized kernel: bind comptime params first, else a wall of "no matching method"/"DevicePassable" errors. `comptime k = vector_add[type_of(layout)]; ctx.enqueue_function[k](...)`. Monomorphic kernels (signature uses `type_of(layout)` directly) pass by name.
- Accumulating products from tensors with DIFFERENT layouts fails with `"cannot convert ElementType to Float32"` - `tensor[i]` returns `SIMD[dtype, layout_expr]` and the layout_exprs don't unify. Fix: `rebind[Scalar[dtype]](tensor[i])` per operand (builtin, no import). Not needed when all operands share one layout.
- Warp shuffle `offset`/`mask` args are `UInt32`, not `Int` - plain `Int` is a type-mismatch error. `warp.sum/max/min/broadcast/reduce` broadcast the result to every lane; `warp.shuffle_down/shuffle_xor` do not.
- `WARP_SIZE` is hardware-dependent (NVIDIA/AMD-RDNA = 32, AMD-CDNA = 64). Use `gpu.WARP_SIZE`, never hardcode 32. `global_idx.x`/`thread_idx.x` return `Int` - compare directly in bounds checks. Always `if tid < n:` (grid is rounded up). `barrier()` is block-wide only - never inside a divergent branch (deadlock).
- Architecture dispatch: `is_*` (`is_nvidia_gpu`, `is_amd_gpu`, ...) checks the COMPILATION TARGET - use inside kernels/GPU code. `has_*` (`has_accelerator`, `has_nvidia_gpu_accelerator`) checks the HOST - use from host code to decide whether to launch.
- Shared memory: `stack_allocation[dtype, address_space=.SHARED](row_major[M,N]())` from the `layout` package returns a `TileTensor`; the `std.memory` `stack_allocation` returns a raw pointer. `AddressSpace` is in `max.gpu.memory` (import from `max.gpu`, not `std.gpu`). Async staging: `fragment.copy_from_async(src)` then `async_copy_wait_all()`. `Atomic` is now `Atomic[Float32]`, not `Atomic[DType.float32]`.
- Profiling intuition: coalesce global-memory accesses; distrust high cache-hit rates (often means uncoalesced); target sufficient occupancy (25-50%), not maximum. Tensor cores are SM70+ (WMMA).

Mojo to/from Python (extension modules / serving glue)

Skip unless: code crosses the Python boundary (`PythonObject`, `PythonModuleBuilder`, `@export def PyInit_`, or a `.mojo` imported from Python).
- PythonObject -> Mojo scalar requires the `py=` KEYWORD: `Int(py=obj)`, `Float64(py=obj)`, `String(py=obj)`. Positional `Int(obj)` fails (only `Bool` accepts positional). Works on numpy scalars too.
- `Python.dict(...)` is generic over a single value type for all kwargs - mixed types fail to infer; wrap: `Python.dict(flag=PythonObject(b), count=PythonObject(42))`. Use `getenv` from `std.os` for env vars, not Python's `os`. No lambda - build callables via `Python.evaluate("lambda x: ...")`.
- Building an extension `.so`: `@export def PyInit_<name>() -> PythonObject` (name MUST match the `.mojo` filename), register with `PythonModuleBuilder` (`def_function` - no positional-arg limit since 1.1.0; `add_type[T]().def_py_init[...]().def_method[...]()`), compile `mojo build --emit shared-lib`. The shared-lib file must NOT contain a `main()` (`"error: shared library should not contain a 'main' function"`) - keep CLI code separate.
- Bound methods take either `py_self: PythonObject` (manual `py_self.downcast_value_ptr[Self]()`) or `self_ptr: Pointer[Self, MutAnyOrigin]` (auto-downcast, direct field access). Return a Mojo value to Python with `PythonObject(alloc=value^)`; recover later via `downcast_value_ptr[T]()`. `import mojo.importer` auto-compiles `.mojo` on import (caches in `__mojocache__/`).
- NumPy interop is no longer 1-D only: `copy_to_numpy_tensor(values, Coord(Idx[2], Idx[3]))` builds an N-D array and `from_numpy_tensor[DType.float64, 2](arr)` borrows a C-contiguous array as a `NumPyView` indexed `view[i, j]` (both in `std.python.numpy`); the 1-D `*_numpy_array` forms are unchanged.
- Keep hot loops in Mojo - every `PythonObject` op crosses the FFI and allocates.

Ecosystem and versioning
- `magic` is dead - `pixi` fully replaced it for Mojo/MAX environments (or `uv`/`pip`/`conda` against `conda.modular.com`/`whl.modular.com`). Mojo needs a C linker (`gcc`/`clang`) to compile; Windows requires WSL2.
- MAX and Mojo versions must match major.minor when building custom MAX kernels - mismatch = kernel compilation failure. Keep both on the same channel (stable or nightly). Mojo is now 1.x: stable `mojo==1.1.0` (2026-09-17), nightly `1.2.0.dev*`; MAX numbers its releases separately (`26.x`). Don't pin a version - let the channel resolve it.
- 1.1.0 completed the 1.0 deprecation cleanup: `fn`, `alias`, `__comptime_assert`, `@parameter if`/`for`, the rename aliases (`InlineArray`, `Immut*`, `StaticConstantOrigin`, `MutExternalOrigin`, `MutUnsafePointer`, ...), the redundant `Int` overloads, and the un-`unsafe_`-prefixed memory APIs are all GONE, not deprecated. `.mojopkg` files are gone too (use `.mojoc`).

## New in 1.1.0 (post-cutoff - models don't know these)

- **Contextual member refs**: write `.member` where the expected type is known - `SIMD[.float32, 4]`, `.cast[.bfloat16]()`, `address_space=.SHARED`, `List[Color] = [.red]`. With no contextual type (unannotated binding, overloaded callee, bare tuple literal), spell it out: `DType.float32`.
- **`@inline(level)`** replaces `@always_inline` / `@no_inline`: `@inline(.always)`, `@inline(.nodebug)`, `@inline(.never)`, and the level may be a parameter. Two inline decorators that disagree are now an error.
- **Thin function types can carry a `where` clause**: `comptime Kernel = def[w: Int](Int) thin -> None where (w > 0, "width must be positive")`. Binding a constrained function to an unconstrained function type is now an error, not a silent drop.
- **Collections**: `Array` gained `Comparable` (lexicographic), `Defaultable`, `concat()`, `repeat()`, and a `fill_with=` constructor that replaces the `Array(uninitialized=True)` + fill-loop idiom. `List` gained a `fill_with=` constructor, its element bound is `AnyType` (not `Movable`), and `extend()`/`resize()` now grow geometrically - `capacity()` may exceed what you asked (`reserve()` still allocates exactly).
- **Stabilized APIs** (safe to depend on, part of the deliberately small stable set): `String.__init__()`, `String(*, capacity_bytes=)`, `String.reserve_bytes()`, `SIMD.__init__()`, `SIMD.__eq__()`, `SIMD.__len__()`, `List.append()`.
- **Memory**: `UnsafeMaybeUninit` → `MaybeUninit` (conforms to lifecycle traits only when the payload is trivial); new free function `deinit(value)` to end a lifetime at a chosen point; `Pointer.unsafe_write(def() -> T)` constructs in place without requiring `Movable`; `write()` is the safe counterpart for trivially-deinit types; `unsafe_ptr()` → `ptr()`; `CStringSlice` → `CStringSpan`.
- **Unified closures keep spreading**: `sort()`, `debug_assert()`, `Span.apply()`, `std.algorithm` tile/unswitch helpers, and the whole benchmarking API (`bench_function`, `bench_with_input`, `iter_custom`, `iter_preproc`) take closures as runtime arguments now; the comptime-parameter forms are gone.
- **Tooling**: `mojo build|run --mlir-timing` / `--llvm-timing` (plus `--timing-json`, `--timing-file`) report where a compile spends time; `@__doc_inline` on an import documents re-exported symbols. Uncaught exceptions now print to **stderr**. `b64decode()` always validates (`validate=` removed) and ignores ASCII whitespace.

## Do NOT
- Do not emit any LEFT-column construct from the version table.
- Do not teach the old "`fn` is strict, `def` is dynamic" dichotomy - modern `def` carries the static, checked behavior.
- Do not use class inheritance, monkey-patching, or dynamic attributes on structs.
- Do not assume copies are free, that `Pointer` can be null, or that `mojo test` exists.
- Do not hardcode warp size 32, skip the `flat_rank` assert, pass `Int` to warp shuffle, or call `enqueue_function` on an unbound parameterized kernel.

## Workflow
1. Confirm the target is Mojo and note the toolchain version (`mojo --version`, `pixi.lock`); reconcile against the version table's sensitivity note.
2. Apply the version table and core rules on every task. For possibly-unstable APIs (GPU tensor types, `vectorize`/`parallelize` signatures, `LayoutTensor` vs `TileTensor`, extension-module ABI), verify against current docs (see References) before committing to syntax.
3. For new code, prefer typed errors, explicit ownership (`^`/`.copy()`), and parameterization over `DType`/sizes. For ports, translate stale constructs via the version table first, then idiomatize, then optimize copies/SIMD/layout.
4. Verify: build/run with `mojo run` (or `mojo build`); write tests as `test_*` functions discovered by `TestSuite`.

## References
Verify any unstable or non-obvious API against current upstream docs (Mojo is young; stdlib outside stabilized-API markers still changes):

- Manual: https://mojolang.org/docs/manual/
- Stdlib reference: https://mojolang.org/docs/std/
- Releases / changelog (breaking changes by version): https://mojolang.org/releases/ (v1.1.0: https://mojolang.org/releases/v1.1.0/)
- GPU: https://mojolang.org/docs/manual/gpu/fundamentals/ and the intro tutorial under the same path
- Ground-truth source (stdlib + MAX kernels): https://github.com/modular/modular