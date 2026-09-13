# P0-G aggregate candidate inventory-addition failure V1

Status: **PRESERVED_ENGINEERING_FAILURE_BEFORE_ARCHIVE_CREATION**.

After the first valid aggregate candidate had been built twice, the principal
third-party license inventory was added to the allowlist. The next test and
build attempt failed before writing either requested archive. The identity/path
scanner interpreted the `s:/` substring in every `https://` link as a Windows
drive path because its drive-letter alternative lacked a left boundary.

The failed destinations are preserved as empty directories:

- `E:/paper/ReliableRAG-cas-q3-aggregate-candidate-20260913-c`;
- `E:/paper/ReliableRAG-cas-q3-aggregate-candidate-20260913-d`.

The failed orchestration also wrote a local intermediate result object whose
hash and count fields were null. It never represented a passing receipt and is
replaced prospectively by the next complete build result. No archive, benchmark
payload, model operation, fit, Gold access or scientific output modification
occurred.

The correction keeps the same forbidden classes but requires that a candidate
drive letter is not immediately preceded by an ASCII letter or digit. This
continues to reject ordinary absolute Windows paths while allowing URL schemes.
The corrected implementation must pass all positive, determinism, tamper,
undeclared-member, traversal and symlink tests before a new candidate receives
a PASS result.
