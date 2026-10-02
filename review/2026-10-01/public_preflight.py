"""Check the Git index for publication hazards and evidence-byte preservation.

This is a bounded heuristic scan, not proof that arbitrary secrets cannot exist.
It does not print matched values, contact a network service, or change Git state.
"""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = {
    "docs/outreach_email.md", "docs/application_procedure.md", "docs/agentspec_smoke.md",
    "artifacts/agentspec/setup.log", "artifacts/agentspec/minigrid_quickstart_unset_keys_status.log",
    "artifacts/package_manifest.json",
}
PATTERNS = {
    "github_token": re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})"),
    "provider_key": re.compile(rb"sk-[A-Za-z0-9_-]{24,}"),
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "personal_absolute_path": re.compile(rb"/" rb"Users" rb"/[^/\s]+/"),
    "personal_email": re.compile(rb"[A-Za-z0-9._%+-]+@(?:gmail|hotmail|outlook)\.com"),
}


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    paths = git("ls-files", "-z").decode().strip("\0").split("\0")
    findings = []
    blobs = {}
    for relative in paths:
        parts = Path(relative).parts
        if relative in PRIVATE or any(p.startswith(".venv") for p in parts) or any(
            p in {".tools", ".review-runs", "__pycache__", ".pytest_cache", "vendor"} for p in parts
        ) or Path(relative).suffix in {".zip", ".pem", ".key"}:
            findings.append({"path": relative, "kind": "excluded_path_tracked"})
        blob = git("show", f":{relative}")
        blobs[relative] = blob
        if Path(relative).suffix not in {".pt", ".npz", ".png"}:
            for name, pattern in PATTERNS.items():
                if pattern.search(blob):
                    findings.append({"path": relative, "kind": name})
    freeze = json.loads((ROOT / "artifacts/freeze.json").read_text())
    for relative, expected in freeze["files"].items():
        actual = hashlib.sha256(blobs.get(relative, b"")).hexdigest()
        if actual != expected:
            findings.append({"path": relative, "kind": "frozen_git_blob_mismatch"})
    for relative in ("results/final/episodes.csv", "results/final/interventions.csv"):
        if blobs.get(relative) != (ROOT / relative).read_bytes():
            findings.append({"path": relative, "kind": "original_result_bytes_changed_by_git"})
    report = {"scope": "current Git index; heuristic privacy scan, frozen-byte and raw-CSV checks",
              "tracked_files": len(paths), "frozen_files": len(freeze["files"]),
              "findings": findings, "passed": not findings}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if findings:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
