#!/usr/bin/env python3
"""Regenerate a CHARM oracle source manifest from an earlier reviewed file set."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite source manifest: {args.output}")
    template = json.loads(args.template.read_text(encoding="utf-8"))
    if template.get("schema_version") != "charm-verifier-source-manifest-v1":
        raise ValueError("unsupported oracle source-manifest template")
    rows = []
    for record in template.get("files", []):
        relative = record.get("path")
        if not isinstance(relative, str):
            raise ValueError("oracle source manifest path must be a string")
        source = (ROOT / relative).resolve()
        try:
            source.relative_to(ROOT)
        except ValueError as exc:
            raise ValueError(f"oracle source path escapes repository: {relative}") from exc
        if not source.is_file() or source.is_symlink():
            raise ValueError(f"oracle source file is missing or unsafe: {relative}")
        payload = source.read_bytes()
        rows.append({
            "path": relative,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "size_bytes": len(payload),
        })
    output = {
        "schema_version": "charm-verifier-source-manifest-v1",
        "role": template["role"],
        "entrypoint": template["entrypoint"],
        "source_file_count": len(rows),
        "files": rows,
        "oracle_matrix": template["oracle_matrix"],
        "regenerated_from_template_sha256": hashlib.sha256(
            args.template.read_bytes()
        ).hexdigest(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(hashlib.sha256(args.output.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
