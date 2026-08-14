# Workspace Rules for intelliview-orchestrator

## Branch Synchronization & Upstream Workflow
- **Upstream Target**: `upstream/Stabilized-version` (`https://github.com/rajat-wyrm/intelliview-orchestrator.git`).
- **Fork Remote**: `origin` (`https://github.com/thisissaditya/intelliview-orchestrator.git`).
- **Strict Verification Gate**:
  - Before pushing any merged PR or commit to `upstream/Stabilized-version`, ensure all 4 CI test jobs (**Python Tests**, **End-to-End Smoke Test**, **Frontend Lint & Build**, **Docker Build**) pass or are gracefully skipped.
  - **IF ANY TEST FAILS**: Abort push immediately. Do NOT push failing code to `upstream/Stabilized-version`.
  - GitHub automatically triggers email notifications to your GitHub account upon any workflow failure.
