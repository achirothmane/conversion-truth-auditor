# Intentionally broken tracking example

This fixture demonstrates the evidence model used by Conversion Truth Auditor.

Expected classifications:

- 2 MATCH
- 1 DUPLICATE
- 2 MISSING
- 1 PHANTOM
- 1 MISMATCH
- 1 UNKNOWN

Expected trust decision: `BLOCK_TRUST` under the default 5% materiality policy.

Run the quickstart command from the repository root to generate `report.json` and `report.html` from the included fixture.
