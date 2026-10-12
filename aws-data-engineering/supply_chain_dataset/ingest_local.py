"""Copy local DataCo source CSVs into a private raw layer and record provenance."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_FILES = (
    "DataCoSupplyChainDataset.csv",
    "DescriptionDataCoSupplyChain.csv",
    "tokenized_access_logs.csv",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ingest(source_dir: Path, output_dir: Path) -> dict:
    source_dir = source_dir.resolve()
    output_dir = output_dir.resolve()
    manifest_path = output_dir / "manifest.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for name in DEFAULT_FILES:
        source = source_dir / name
        if not source.is_file():
            raise FileNotFoundError(f"Expected source file not found: {source}")
        target = output_dir / name
        shutil.copy2(source, target)
        files.append({
            "file_name": name,
            "source_path": str(source),
            "raw_path": str(target),
            "size_bytes": target.stat().st_size,
            "sha256": sha256(target),
        })
    manifest = {
        "ingested_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_directory": str(source_dir),
        "files": files,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=Path(__file__).parent)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "data" / "raw")
    args = parser.parse_args()
    manifest = ingest(args.source_dir, args.output_dir)
    print(f"Ingested {len(manifest['files'])} files into {args.output_dir.resolve()}")
    for item in manifest["files"]:
        print(f"  {item['file_name']}: {item['size_bytes']:,} bytes, sha256 {item['sha256']}")
    print(f"Manifest: {(args.output_dir.resolve() / 'manifest.json')}")


if __name__ == "__main__":
    main()
