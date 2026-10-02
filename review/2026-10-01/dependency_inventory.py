"""Record installed dependency metadata, without redistributing dependency binaries."""

import argparse
import json
from importlib.metadata import metadata
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    packages = []
    for line in (root / "requirements.lock.txt").read_text().splitlines():
        if not line.strip():
            continue
        name, pinned = line.split("==")
        info = metadata(name)
        packages.append({"name": name, "pinned_version": pinned, "installed_version": info["Version"],
                         "license_expression": info.get("License-Expression"),
                         "license_field_first_line": (info.get("License") or "").split("\n")[0],
                         "project_urls": info.get_all("Project-URL") or [],
                         "license_files": info.get_all("License-File") or []})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"source": "installed distribution metadata",
                                     "note": "Inventory, not a legal license determination; read upstream notices",
                                     "packages": packages}, indent=2) + "\n")
    print(f"Recorded metadata for {len(packages)} pinned distributions")


if __name__ == "__main__":
    main()
