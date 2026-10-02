from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "review/2026-10-02/verify_publication.py"


spec = importlib.util.spec_from_file_location("verify_publication", HELPER_PATH)
verify_publication = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(verify_publication)


def run(*args: str, cwd: Path) -> None:
    subprocess.check_call(args, cwd=cwd, stdout=subprocess.DEVNULL)


def sha(data: bytes) -> str:
    return verify_publication.sha256_bytes(data)


def write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def make_fixture(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    run("git", "init", "-q", cwd=root)
    run("git", "config", "user.email", "test@example.com", cwd=root)
    run("git", "config", "user.name", "Test User", cwd=root)

    original_protocol = b"original protocol with private completion logistics\n"
    publication_protocol = b"clean publication protocol\n"
    code = b"frozen code\n"
    write(root / "docs/protocol.md", original_protocol)
    write(root / "src/module.py", code)
    freeze = {
        "files": {
            "docs/protocol.md": sha(original_protocol),
            "src/module.py": sha(code),
        },
        "model_outcomes_on_test_inspected": False,
        "primary": "test primary metric",
        "episodes": 2,
    }
    write(root / "artifacts/freeze.json", json.dumps(freeze).encode() + b"\n")
    run("git", "add", ".", cwd=root)
    run("git", "commit", "-q", "-m", "frozen evidence", cwd=root)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip()

    write(root / "docs/protocol.md", publication_protocol)
    metadata = {
        "schema_version": 1,
        "freeze_path": "artifacts/freeze.json",
        "freeze_sha256": sha((root / "artifacts/freeze.json").read_bytes()),
        "frozen_manifest_file_count": 2,
        "publication_copies": [
            {
                "path": "docs/protocol.md",
                "frozen_sha256": sha(original_protocol),
                "historical_revision": revision,
                "publication_sha256": sha(publication_protocol),
                "rationale": "test publication copy",
            }
        ],
    }
    write(root / "review/2026-10-02/publication_copy.json", json.dumps(metadata).encode() + b"\n")
    run("git", "add", ".", cwd=root)
    monkeypatch.setattr(verify_publication, "FREEZE_SHA256", metadata["freeze_sha256"])
    monkeypatch.setattr(verify_publication, "FROZEN_MANIFEST_FILE_COUNT", 2)
    monkeypatch.setattr(verify_publication, "FROZEN_PROTOCOL_REVISION", revision)
    monkeypatch.setattr(verify_publication, "FROZEN_PROTOCOL_SHA256", sha(original_protocol))
    monkeypatch.setattr(verify_publication, "PUBLICATION_PROTOCOL_SHA256", sha(publication_protocol))
    return root


def check(root: Path, **kwargs):
    return verify_publication.verify_publication(root, **kwargs)


def test_valid_fixture_verifies_live_frozen_history_and_publication_copy(
    tmp_path: Path, monkeypatch
) -> None:
    report = check(make_fixture(tmp_path, monkeypatch))
    assert report["passed"]
    assert report["live_frozen_verified_count"] == 1
    assert report["historical_frozen_verified_count"] == 1
    assert report["publication_copy_verified_count"] == 1
    assert report["file_count"] == 2
    assert report["mismatch_count"] == 0


def test_current_protocol_tamper_fails_publication_copy_check(tmp_path: Path, monkeypatch) -> None:
    root = make_fixture(tmp_path, monkeypatch)
    write(root / "docs/protocol.md", b"tampered publication protocol\n")
    report = check(root)
    assert not report["passed"]
    assert "protocol_publication_or_history_mismatch" in report["failures"]


def test_non_protocol_tamper_fails_frozen_file_check(tmp_path: Path, monkeypatch) -> None:
    root = make_fixture(tmp_path, monkeypatch)
    write(root / "src/module.py", b"tampered code\n")
    report = check(root)
    assert not report["passed"]
    assert "frozen_file_hash_mismatch" in report["failures"]


def test_freeze_tamper_fails_manifest_hash_check(tmp_path: Path, monkeypatch) -> None:
    root = make_fixture(tmp_path, monkeypatch)
    freeze = json.loads((root / "artifacts/freeze.json").read_text())
    freeze["episodes"] = 99
    write(root / "artifacts/freeze.json", json.dumps(freeze).encode() + b"\n")
    report = check(root)
    assert not report["passed"]
    assert "freeze_manifest_hash_mismatch" in report["failures"]


def test_wrong_historical_hash_fails(tmp_path: Path, monkeypatch) -> None:
    root = make_fixture(tmp_path, monkeypatch)
    run("git", "commit", "-q", "-m", "publication copy", cwd=root)
    monkeypatch.setattr(verify_publication, "FROZEN_PROTOCOL_REVISION", "HEAD")
    report = check(root)
    assert not report["passed"]
    assert "protocol_publication_or_history_mismatch" in report["failures"]


def test_missing_history_reports_actionable_failure(tmp_path: Path, monkeypatch) -> None:
    root = make_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(verify_publication, "FROZEN_PROTOCOL_REVISION", "missingrevision")
    report = check(root)
    assert not report["passed"]
    assert "historical_protocol_unavailable" in report["failures"]
    assert "full Git clone" in report["historical_protocol_action"]


def test_index_source_uses_staged_bytes_not_worktree_bytes(tmp_path: Path, monkeypatch) -> None:
    root = make_fixture(tmp_path, monkeypatch)
    run("git", "commit", "-q", "-m", "publication copy", cwd=root)
    write(root / "src/module.py", b"worktree only tamper\n")
    live_report = check(root, source="worktree")
    index_report = check(root, source="index")
    assert not live_report["passed"]
    assert index_report["passed"]


def test_additional_publication_exception_fails(tmp_path: Path, monkeypatch) -> None:
    root = make_fixture(tmp_path, monkeypatch)
    metadata_path = root / "review/2026-10-02/publication_copy.json"
    metadata = json.loads(metadata_path.read_text())
    metadata["publication_copies"].append(
        {
            "path": "src/module.py",
            "frozen_sha256": metadata["publication_copies"][0]["frozen_sha256"],
            "historical_revision": metadata["publication_copies"][0]["historical_revision"],
            "publication_sha256": metadata["publication_copies"][0]["publication_sha256"],
        }
    )
    write(metadata_path, json.dumps(metadata).encode() + b"\n")
    report = check(root)
    assert not report["passed"]
    assert "publication_copy_mapping_count" in report["failures"]
