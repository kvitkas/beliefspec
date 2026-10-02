"""Verify publication-copy provenance without rewriting the frozen evidence.

The public repository keeps one cleaned publication copy of ``docs/protocol.md``.
All other frozen files must still match ``artifacts/freeze.json`` in the live tree
or in the Git index, depending on the requested source. The original protocol
bytes are verified from a fixed historical Git revision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Literal

ALLOWED_PUBLICATION_COPY = "docs/protocol.md"
FREEZE_PATH = "artifacts/freeze.json"
FREEZE_SHA256 = "32f29ded1b7cd547509addd000fbf6375d9d86f660e3a74c56e9a48076a7b98b"
FROZEN_MANIFEST_FILE_COUNT = 50
FROZEN_PROTOCOL_REVISION = "0b0298ee75accc2306caeca205c5225ce5a2ceae"
FROZEN_PROTOCOL_SHA256 = "8e41a14956bbfd7a4789e3da88db5da7b2b1ba2e2bc557de3fb11758e1bf4bb6"
PUBLICATION_PROTOCOL_SHA256 = "a674b33339fcf8bd85fd99ce3f3a3259a552bf29882f1cc65cd63e9f35e2c2d6"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_bytes(root: Path, spec: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), "show", spec], stderr=subprocess.PIPE)


def source_bytes(root: Path, relative: str, source: Literal["worktree", "index"]) -> bytes:
    if source == "index":
        return git_bytes(root, f":{relative}")
    return (root / relative).read_bytes()


def source_json(root: Path, relative: str, source: Literal["worktree", "index"]) -> Any:
    return json.loads(source_bytes(root, relative, source).decode())


def _empty_report(source: str) -> dict[str, Any]:
    return {
        "root": ".",
        "source": source,
        "file_count": 0,
        "mismatch_count": 0,
        "mismatches": [],
        "live_frozen_verified_count": 0,
        "historical_frozen_verified_count": 0,
        "publication_copy_verified_count": 0,
        "passed": False,
        "failures": [],
    }


def verify_publication(
    root: Path,
    *,
    source: Literal["worktree", "index"] = "worktree",
) -> dict[str, Any]:
    """Return a structured provenance report for the public package."""

    root = root.resolve()
    metadata_path = root / "review/2026-10-02/publication_copy.json"
    metadata_relative = str(metadata_path.resolve().relative_to(root))
    metadata = source_json(root, metadata_relative, source)
    report = _empty_report(source)
    mismatches = report["mismatches"]
    failures = report["failures"]

    if metadata.get("freeze_path") != FREEZE_PATH:
        failures.append("freeze_path_metadata_mismatch")
    if metadata.get("freeze_sha256") != FREEZE_SHA256:
        failures.append("freeze_sha256_metadata_mismatch")

    freeze_actual = sha256_bytes(source_bytes(root, FREEZE_PATH, source))
    if freeze_actual != FREEZE_SHA256:
        mismatches.append(
            {
                "path": FREEZE_PATH,
                "kind": "freeze_manifest_hash_mismatch",
                "expected": FREEZE_SHA256,
                "actual": freeze_actual,
            }
        )
        failures.append("freeze_manifest_hash_mismatch")

    freeze = source_json(root, FREEZE_PATH, source)
    frozen_files = freeze.get("files", {})
    report["file_count"] = len(frozen_files)
    report["model_outcomes_on_test_inspected"] = freeze.get("model_outcomes_on_test_inspected")
    report["primary"] = freeze.get("primary")
    report["episodes"] = freeze.get("episodes")

    publication_copies = metadata.get("publication_copies")
    if not isinstance(publication_copies, list) or len(publication_copies) != 1:
        failures.append("publication_copy_mapping_count")
        publication_copies = []
    copy = publication_copies[0] if publication_copies else {}
    exception_path = copy.get("path")
    if exception_path != ALLOWED_PUBLICATION_COPY:
        failures.append("publication_copy_path")
    if copy.get("frozen_sha256") != FROZEN_PROTOCOL_SHA256:
        failures.append("publication_copy_frozen_hash_metadata_mismatch")
    if copy.get("frozen_sha256") != frozen_files.get(ALLOWED_PUBLICATION_COPY):
        failures.append("publication_copy_frozen_hash")
    if copy.get("historical_revision") != FROZEN_PROTOCOL_REVISION:
        failures.append("historical_revision_metadata_mismatch")
    if copy.get("publication_sha256") != PUBLICATION_PROTOCOL_SHA256:
        failures.append("publication_sha256_metadata_mismatch")
    if metadata.get("frozen_manifest_file_count") != FROZEN_MANIFEST_FILE_COUNT:
        failures.append("frozen_manifest_count_metadata_mismatch")
    if metadata.get("frozen_manifest_file_count") != len(frozen_files):
        failures.append("frozen_manifest_file_count")

    source_verified_count = 0
    for relative, expected in sorted(frozen_files.items()):
        if relative == exception_path == ALLOWED_PUBLICATION_COPY:
            continue
        try:
            actual = sha256_bytes(source_bytes(root, relative, source))
        except (FileNotFoundError, subprocess.CalledProcessError):
            actual = None
        if actual != expected:
            mismatches.append(
                {
                    "path": relative,
                    "kind": f"{source}_frozen_hash_mismatch",
                    "expected": expected,
                    "actual": actual,
                }
            )
        else:
            source_verified_count += 1
    report["live_frozen_verified_count"] = source_verified_count

    if copy:
        try:
            historical_actual = sha256_bytes(
                git_bytes(root, f"{FROZEN_PROTOCOL_REVISION}:{ALLOWED_PUBLICATION_COPY}")
            )
        except subprocess.CalledProcessError as error:
            historical_actual = None
            failures.append("historical_protocol_unavailable")
            report["historical_protocol_error"] = error.stderr.decode(errors="replace").strip()
            report["historical_protocol_action"] = (
                f"Use a full Git clone containing revision {FROZEN_PROTOCOL_REVISION}."
            )
        if historical_actual != FROZEN_PROTOCOL_SHA256:
            mismatches.append(
                {
                    "path": ALLOWED_PUBLICATION_COPY,
                    "kind": "historical_protocol_hash_mismatch",
                    "revision": FROZEN_PROTOCOL_REVISION,
                    "expected": FROZEN_PROTOCOL_SHA256,
                    "actual": historical_actual,
                }
            )
        else:
            report["historical_frozen_verified_count"] = 1

        try:
            publication_actual = sha256_bytes(source_bytes(root, ALLOWED_PUBLICATION_COPY, source))
        except (FileNotFoundError, subprocess.CalledProcessError):
            publication_actual = None
        if publication_actual != PUBLICATION_PROTOCOL_SHA256:
            mismatches.append(
                {
                    "path": ALLOWED_PUBLICATION_COPY,
                    "kind": f"{source}_publication_copy_hash_mismatch",
                    "expected": PUBLICATION_PROTOCOL_SHA256,
                    "actual": publication_actual,
                }
            )
        else:
            report["publication_copy_verified_count"] = 1

    if any(row["path"] != ALLOWED_PUBLICATION_COPY for row in mismatches):
        failures.append("frozen_file_hash_mismatch")
    if any(row["path"] == ALLOWED_PUBLICATION_COPY for row in mismatches):
        failures.append("protocol_publication_or_history_mismatch")

    report["mismatch_count"] = len(mismatches)
    report["failures"] = sorted(set(failures))
    report["passed"] = not report["failures"] and not report["mismatches"]
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--source", choices=["worktree", "index"], default="worktree")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = verify_publication(
        Path(args.root),
        source=args.source,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report, indent=2, allow_nan=False))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
