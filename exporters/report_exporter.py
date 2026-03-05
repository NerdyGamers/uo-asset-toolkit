# exporters/report_exporter.py
# Generates a human-readable diff report from DiffResult lists.

import os
import json
from typing import List
from datetime import datetime


def write_json_report(results: list, output_path: str) -> str:
    """
    Write a JSON report of all diff results.
    Each result entry: {asset_id, asset_type, status, clean_hash, modded_hash}
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    report = {
        "generated": datetime.now().isoformat(),
        "total": len(results),
        "changed": sum(1 for r in results if r.status != "identical"),
        "results": [
            {
                "asset_id": hex(r.asset_id),
                "asset_type": r.asset_type,
                "status": r.status,
                "clean_hash": r.clean_hash,
                "modded_hash": r.modded_hash,
            }
            for r in results
        ],
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"[Report] Written {len(results)} results -> {output_path}")
    return output_path


def write_text_report(results: list, output_path: str) -> str:
    """
    Write a plain-text summary report.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    changed = [r for r in results if r.status != "identical"]
    lines = [
        f"UO Asset Toolkit - Diff Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total scanned: {len(results)}",
        f"Total changed: {len(changed)}",
        "",
        "Changed Assets:",
        "-" * 40,
    ]
    for r in changed:
        lines.append(f"  [{r.status.upper():8s}] {r.asset_type:10s} ID: {hex(r.asset_id)}")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[Report] Written text report -> {output_path}")
    return output_path
