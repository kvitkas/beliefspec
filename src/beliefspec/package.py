"""Build a private local handoff archive; never upload or publish it."""

import zipfile
from datetime import UTC, datetime

from beliefspec.dataio import file_sha256, write_json
from beliefspec.experiment import ROOT


def main():
    archive = ROOT.parent / "beliefspec-pilot-2026-10-01.zip"
    if archive.exists():
        raise FileExistsError(f"Preserve existing archive: {archive}")
    paths = [ROOT / name for name in ("README.md", "pyproject.toml", "requirements.lock.txt", ".gitignore")]
    for directory in ("src", "tests", "configs", "docs", "data", "runs", "results", "artifacts"):
        paths.extend(p for p in (ROOT / directory).rglob("*") if p.is_file()
                     and "__pycache__" not in p.parts and p.name != ".DS_Store"
                     and p.name != "package_manifest.json")
    manifest = ROOT / "artifacts/package_manifest.json"
    write_json(manifest, {"utc": datetime.now(UTC).isoformat(),
                          "private_local_archive": archive.name,
                          "files": {str(p.relative_to(ROOT)): {"sha256": file_sha256(p),
                                                                 "bytes": p.stat().st_size}
                                    for p in sorted(paths)}})
    paths.append(manifest)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as stream:
        for path in sorted(paths):
            stream.write(path, arcname=str(path.relative_to(ROOT.parent)))
    with zipfile.ZipFile(archive) as stream:
        bad_member = stream.testzip()
    if bad_member:
        raise RuntimeError(f"Archive CRC check failed: {bad_member}")
    print(f"Created private local archive: {archive} ({archive.stat().st_size} bytes; {len(paths)} files)")


if __name__ == "__main__":
    main()
