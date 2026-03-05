# commands/scan_all.py
# CLI command: scan ALL asset types (art, gumps, textures) from both clients.

import os
import yaml

CONFIG_PATH = "config.yaml"


def _load_config() -> dict:
    if os.path.isfile(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f) or {}
    return {}


def scan_all():
    print("[scan-all] Starting full scan...")

    from commands.scan_art import scan_art
    print("\n--- Scanning Art ---")
    scan_art()

    # Additional asset types can be added here as they are implemented
    # from commands.scan_gumps import scan_gumps
    # scan_gumps()

    print("\n[scan-all] All scans complete.")


if __name__ == "__main__":
    scan_all()
