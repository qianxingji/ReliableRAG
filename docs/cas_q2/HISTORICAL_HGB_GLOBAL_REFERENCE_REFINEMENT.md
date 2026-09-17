# Resolve callable identities in the complete HGB state observer

Research Lead refinement before diagnostic v3, 2026-09-11.

Diagnostic v2 reaches a reduction item whose type-level __module__ attribute is
a member descriptor, causing the observer's string concatenation to fail. It
does not finish comparison. Keep its output and failure separate from v1 and
from the original seven-fit replay failure. No additional fit or score occurred.

The existing design requires global constructor/function identities to be
recorded without calling them. Extend that observation to a callable with
string-valued instance __module__/__qualname__: resolve those names using only
the already loaded module dictionary and nested attributes, and require the
resolved object is the very same callable. Record that verified global reference.
This covers extension-defined global callables that Python's FunctionType and
BuiltinFunctionType checks do not recognize. Do not accept a mere display name,
bound method with different identity or unresolved callable as equivalent state.

All complete state, exact comparison, zero-fit/score and byte-preservation
requirements remain unchanged. Use a new source file and output namespace.
Preserve both failed observers; no original model bytes or result are rewritten.
CAS Q2 STATUS: NOT READY. Total actual fits remain 185.
