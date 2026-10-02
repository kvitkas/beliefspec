"""Check the Git index for publication hazards and evidence-byte preservation.

This is a bounded heuristic scan, not proof that arbitrary secrets cannot exist.
It does not print matched values, contact a network service, or change Git state.
"""

import argparse
import importlib.util
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXCLUDED_DIR_PARTS = {
    ".pytest_cache",
    ".review-runs",
    ".tools",
    "__pycache__",
    "private",
    "vendor",
}
EXCLUDED_SUFFIXES = {".key", ".pem", ".zip"}
PATTERNS = {
    "github_token": re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})"),
    "provider_key": re.compile(rb"sk-[A-Za-z0-9_-]{24,}"),
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "personal_absolute_path": re.compile(rb"/" rb"Users" rb"/[^/\s]+/"),
    "personal_email": re.compile(rb"[A-Za-z0-9._%+-]+@(?:gmail|hotmail|outlook)\.com"),
}
BINARY_SUFFIXES = {".pdf", ".png", ".pt", ".npz"}


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def publication_report():
    helper = ROOT / "review/2026-10-02/verify_publication.py"
    spec = importlib.util.spec_from_file_location("verify_publication", helper)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.verify_publication(ROOT, source="index")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    paths = git("ls-files", "-z").decode().strip("\0").split("\0")
    findings = []
    blobs = {}
    for relative in paths:
        parts = Path(relative).parts
        if (
            any(p.startswith(".venv") for p in parts)
            or any(p in EXCLUDED_DIR_PARTS for p in parts)
            or Path(relative).suffix in EXCLUDED_SUFFIXES
        ):
            findings.append({"path": relative, "kind": "excluded_path_tracked"})
        blob = git("show", f":{relative}")
        blobs[relative] = blob
        suffix = Path(relative).suffix
        if suffix not in BINARY_SUFFIXES:
            for name, pattern in PATTERNS.items():
                if pattern.search(blob):
                    findings.append({"path": relative, "kind": name})
    provenance = publication_report()
    if not provenance["passed"]:
        findings.append(
            {
                "path": "review/2026-10-02/publication_copy.json",
                "kind": "publication_provenance_failed",
                "failures": provenance["failures"],
            }
        )
    for relative in ("results/final/episodes.csv", "results/final/interventions.csv"):
        if blobs.get(relative) != (ROOT / relative).read_bytes():
            findings.append({"path": relative, "kind": "original_result_bytes_changed_by_git"})
    report = {
        "scope": "current Git index; heuristic credential/path scan, provenance, and raw-CSV checks",
        "tracked_files": len(paths),
        "frozen_files": provenance["file_count"],
        "publication_provenance": provenance,
        "findings": findings,
        "passed": not findings,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if findings:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
