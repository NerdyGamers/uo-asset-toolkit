import sys
import os

# ---------------------------------------------------------------------------
# UO Asset Toolkit — launcher.py
# Entry point for both CLI and GUI modes.
# Usage:
#   python launcher.py              -> launches PyQt6 GUI
#   python launcher.py scan-all    -> CLI scan
#   python launcher.py scan-art    -> CLI art-only scan
#   python launcher.py build-modpack -> CLI mod pack builder
#   python launcher.py analyze     -> CLI client analysis
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()

        if cmd == "scan-all":
            from commands.scan_all import scan_all
            scan_all()

        elif cmd == "scan-art":
            from commands.scan_art import scan_art
            scan_art()

        elif cmd == "build-modpack":
            from commands.build_modpack import build_modpack
            build_modpack()

        elif cmd == "analyze":
            from commands.analyze_client import analyze_client
            analyze_client()

        else:
            print(f"Unknown command: {cmd}")
            print("Available commands: scan-all, scan-art, build-modpack, analyze")
            sys.exit(1)

        return

    # No arguments — launch GUI
    try:
        from PyQt6.QtWidgets import QApplication
        from gui.main_window import MainWindow
    except ImportError:
        print("PyQt6 is required for GUI mode. Install it with: pip install PyQt6")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName("UO Asset Toolkit")
    app.setApplicationVersion("5.0.0")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
