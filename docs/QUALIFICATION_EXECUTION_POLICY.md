# CY16 qualification execution policy

Verified 2026-10-14 against this repository's `.github/workflows/ci.yml`,
`Makefile`, and `pyproject.toml`.

## Allowed execution

- The CY16-bootstrap repository is **public**. Its existing
  `ubuntu-latest` workflow is configured for PRs targeting main,
  pushes to main, and manual dispatch.
- Public-repository hosted GitHub Actions are eligible for GitHub's
  public-repository runner allowance; this is **not** an authorization
  to consume private-repository hosted runner minutes.
- The inspected workflow builds the local C sources and Python
  package; no private checkout or private-repository dependency was
  found in these inspected build entry points.

## Disallowed / delegated

- Do not run GitHub-hosted Actions jobs in private repositories for
  this campaign, even if GitHub currently reports available minutes.
- Any private-repository workload must be delegated through Agent
  Dispatch to an approved runtime shape (disposable TrueNAS,
  local host, or another qualified executor), with bounded scope,
  observable logs, artifacts, and explicit provenance.
- Do not assume that triggering an Agent Dispatch job in a private
  repository is free: its **control-plane** workflow can itself use
  private-repository hosted runner minutes. Prefer an approved public
  control plane or a self-hosted dispatcher, subject to credential
  and data-boundary review.
- Never move proprietary CY16 PDFs, private evidence, credentials,
  or private test inputs into a public Actions workflow.

## Qualification gate

1. Confirm actual PR-triggered CI run on this public repo.
2. Verify tests/build steps and capture run URL and revision.
3. If private fixtures are needed, dispatch a separate private-data
   qualification through Agent Dispatch; do not silently fall back
   to private GitHub-hosted Actions.
4. Record runtime identity, billable-minute class, input revision,
   outputs, and result before treating any execution as qualified.

This policy does not itself prove that CI is green or that an
Agent Dispatch runtime is currently available.
