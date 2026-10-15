# Trivy: what it scans and what it found

## Short answer (for the submission form)

Trivy scans each built image before it's pushed: the Debian/Alpine OS packages in the base image and every Python and npm package installed in it, compared against public vulnerability databases. The pipeline fails if it finds a HIGH or CRITICAL issue that already has a fix (`--ignore-unfixed`). The first scan of the backend image failed with four HIGH findings. They all came from copies of `urllib3`, `msgpack` and `setuptools` that **pip vendors inside itself**, not from the app's own dependencies. Since the running API never needs pip, removing it from the runtime image fixed all four, and both images now scan clean.

## The findings

Real output from `trivy image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1` (Trivy 0.76.0):

| Package | ID | Severity | Installed | Fixed | What it is |
|---|---|---|---|---|---|
| setuptools | CVE-2025-47273 | HIGH | 70.3.0 | 78.1.1 | Path traversal in `PackageIndex` |
| urllib3 | CVE-2026-97687 | HIGH | 2.7.0 | 2.8.0 | Traffic interception via HTTPS proxy TLS config override |
| urllib3 | CVE-2026-97689 | HIGH | 2.7.0 | 2.8.0 | DoS via unbounded memory allocation in the chunk parser |
| msgpack | GHSA-6v7p-g79w-8964 | HIGH | 1.1.2 | 1.2.1 | Out-of-bounds read when an `Unpacker` is reused |

Screenshots: [before](screenshots/m6-trivy-before-fix.png), with exit code 1, and [after](screenshots/m6-trivy-clean-local.png), with exit code 0 for both images.

### Explaining one: CVE-2025-47273 (setuptools)

`setuptools.package_index.PackageIndex` builds a local filename from a download URL without properly sanitising it. A crafted URL can contain `../` sequences that make it write files outside the intended download directory, possibly overwriting something that later gets executed. It's only reachable when something actually *downloads and installs packages* with that code path, i.e. during `pip`/`easy_install`-style installs.

In this image the only copy was the one vendored inside pip. Our app never imports it and never installs packages at runtime, so the practical risk was low. But "low risk, still present" is the wrong place to be for a public image, and the fix had no downside:

```dockerfile
# build stage: install deps into /opt/venv, then remove pip from that venv
RUN pip install -r requirements.txt && pip uninstall -y pip
# runtime stage: remove the base image's own pip and ensurepip wheels too
RUN python -m pip uninstall -y pip && rm -rf /usr/local/lib/python3.13/ensurepip
```

## Why these settings

- `--severity HIGH,CRITICAL`: LOW/MEDIUM findings are reported elsewhere (Dependabot, the full scan) but don't block a deploy.
- `--ignore-unfixed`: a finding with no released fix can't be acted on yet. Blocking on it would just freeze every deploy until upstream ships a patch.
- `exit-code: 1`: this is what makes it a *gate* rather than a report.

## What Trivy doesn't cover

Container scanning is one layer. Static analysis of our own code (SAST, e.g. CodeQL/Bandit), secret scanning (GitHub push protection), dependency alerts (Dependabot) and runtime controls (the restricted Pod Security Standard, read-only root filesystems) catch different problems.
