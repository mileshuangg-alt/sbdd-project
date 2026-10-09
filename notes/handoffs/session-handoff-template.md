# Session [N] Handoff - [one-line title]

**Date prepared:** [date]
**Purpose:** Start Session [N] without repeating Session [N-1] setup, qualification, artifact discovery, receptor preparation, or validation work.

## 0. Standing rule
The handoff is the audit. Start at the first execution step. Never propose inventory, verification, or requirements-mapping phases for anything this handoff marks frozen. Retrieve an artifact only when execution exposes a specific gap, and name the artifact plus the decision it unblocks.

## 1. Critical boundary
[What the previous session closed; what this session must not reopen.]
State the last result at its true size:
> [Exact bounded claim language, including what it does NOT establish.]

## 2. What Session [N-1] achieved
[Per achievement: what was done, exact artifacts, provenance (versions, commits, paths), frozen status. Include restore commands for any environment a fresh shell needs.]

## 3. Frozen archive
[Bundle locations, manifests, checksums. Read-only evidence, not a working directory.]

## 4. Documentation completed
[Session logs, decision entries, reports written.]

## 5. Git state
[Local branch/commit, each remote's last confirmed state, intentionally untracked artifacts.]

## 6. Environments
Local: [repo path, conda env, key versions]
Server: [host, paths, env restore commands]

## 7. Decisions now in force
[One block per decision: claim boundary (supports / does not support), frozen instruments and routes, parity rules.]

## 8. Claim authority
Authorized: [exact claim language allowed]
Prohibited: [exact claims banned]
Retention defects on record: [missing artifacts, documented; do not silently reconstruct]

## 9. Do NOT reopen
[Explicit list of closed branches, dead ends, frozen choices.]

## 10. Session [N] starting point
[The one operation to execute first, and what done looks like. State the first authorized question if useful.]

## 11. Process rules in force
- Validation-requirement rule: trace to frozen framework, label anything new as proposed, user approval before mandatory.
- Alternatives-pass rule: enumerate serious cited alternatives, assess cost/scope, document rejection reasons, label unrejected.
- Approval protocol: decisions and framework edits are drafted, shown, and approved by me before being written. Results reported as measured, no rounding up.

## 12. Preservation rule
[What must be preserved, including failed branches and diagnostics, until the stage is finalized and frozen.]
