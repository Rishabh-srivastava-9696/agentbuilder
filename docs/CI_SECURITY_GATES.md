# CI security gates

The CI workflow is deliberately fail-closed for dependency vulnerabilities and
static analysis. The checks use public, credential-free OSS tooling; they do
not upload findings to a scanning service or use a scanner token.

## Enforced checks

| Check | Tool and scope | Failure condition |
| --- | --- | --- |
| Dependency vulnerabilities | Trivy filesystem vulnerability scanner, pinned through `aquasecurity/trivy-action@0.28.0`. It scans `apps/api/requirements.txt`, the six root `packages/*/pyproject.toml` manifests installed by the API image, and each deployed JavaScript application's lockfile: `apps/admin/package-lock.json`, `apps/widget/package-lock.json`, and `apps/shopify-mcp/package-lock.json`. | Any library vulnerability with severity `HIGH` or `CRITICAL`, or a scanner execution failure. Unfixed findings are included. |
| SAST | The digest-pinned `semgrep/semgrep:1.91.0` container runs the public `p/default` ruleset only against canonical deployable code: `apps/api/app`, root `packages`, and each deployed JavaScript application's `src` directory. It also scans the four deployment Dockerfiles and `docker-compose.yml`. Test and spec files are excluded because they are not shipped runtime code. | Any SAST finding or scanner/rule-loading failure. `--disable-nosem` prevents inline `nosemgrep` comments from suppressing a finding. |

Neither job uses `continue-on-error`, `--ignore-unfixed`, a baseline, nor an
ignore list. The dependency gate uses Trivy's `vuln` scanner only, so it does
not conflate vulnerability enforcement with optional secret or configuration
checks.

## Exception policy

There is no CI bypass or suppression path for these gates. A red security job
blocks the change until the finding is remediated, a dependency is upgraded or
replaced, or a SAST rule is corrected upstream. Do not add `nosemgrep` markers,
baselines, ignore files, `continue-on-error`, or `--ignore-unfixed` to make a
job pass.

If an operational release deadline cannot wait for remediation, record a
time-bounded risk-acceptance issue that identifies the scanner, finding ID,
affected component, compensating controls, owner, and expiry date; obtain
approval from the security owner and service owner. This records deployment
risk only—it does not waive or alter the CI result. The follow-up must restore
a green gate through an actual remediation before the expiry date.

## Dependency coverage and follow-up

Dependabot checks npm and pip manifests weekly and now covers every deployed
Dockerfile directory: `/apps/api`, `/apps/admin`, `/apps/widget`, and
`/apps/shopify-mcp`.

The API's `apps/api/requirements.txt` contains lower-bound Python requirements,
and the root package manifests also use unpinned lower bounds. There is no
fully resolved, hash-checked Python lockfile. Trivy scans these manifests, but
the result cannot be a deterministic audit of the deployed Python transitive
graph. Create and commit a fully resolved Python lockfile (with hashes), install
from it in CI and the API image, then point the vulnerability gate at that
lockfile while retaining Dependabot coverage for the API's supported Python
dependency manifest. This remains a required follow-up.

## Operational limitation

Both gates retrieve public artifacts at runtime: Trivy downloads its binary and
vulnerability database, while GitHub Actions pulls the Semgrep image and the
scanner retrieves the public ruleset. The Semgrep executable image is pinned by
digest; there is no in-repository mirror yet. Network or registry failures
therefore make the relevant job fail rather than silently skipping the security
check; add a controlled internal mirror if availability becomes a release
concern.
