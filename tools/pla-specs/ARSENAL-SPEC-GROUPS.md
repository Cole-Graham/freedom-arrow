# Arsenal specialization grouping

Shared PLA units retain all database memberships. The native Arsenal groups by the first membership, while its filter accepts any membership. This hook moves existing cards under an eligible selected heading after native filtering. All restores primary grouping. Both icon and photo modes use native group initialization and callbacks; prior group arrays are restored on failure.

Run the pure policy checks with `dotnet run --project tools/pla-specs/spec-group-tests/SpecGroupTests.csproj -c Release -- tools/pla-specs/spec-group-tests/build15-memberships.json`. Native UI validation remains separate. Log markers identify applied selections and failures.

Build17 is a runtime-only overlay over the exact complete Build16 archive. `package_ui.py` preserves all constant tables, FAModels, models and music, including Build16 weapon-family HUD resources. See the root build contract for the base SHA256 and `releases/0.6/verify.py` for full package checks. Country-selector order remains unchanged pending user clarification.

## Document change log

- 2026-11-11 11:03:18 PST (America/Los_Angeles) — Added the shared-card grouping guide and verification boundary.
