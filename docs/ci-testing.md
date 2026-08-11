\# CI Testing



\## Verification



1\. Create a Pull Request targeting the `Stabilized-version` branch.

2\. GitHub Actions automatically starts the CI workflow.

3\. Backend tests are executed using `pytest`.

4\. Frontend linting is executed using ESLint.

5\. The Pull Request should only be merged after all required CI checks pass.



\## Local Testing



\### Backend



Run:



```bash

pytest

