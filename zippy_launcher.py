#!/usr/bin/env python3
"""
Cross-platform GUI launcher for Zippy.
Opens a terminal window displaying zippy --help.
"""

import os
import subprocess
import sys


def main():
    """Launch zippy --help in a terminal window."""
    if sys.platform == "win32":
        # Windows: run in cmd and wait for user input
        subprocess.run([sys.executable, "-m", "zippy.cli", "--help"], shell=True)
        input("\nPress Enter to close this window...")
    elif sys.platform == "darwin":
        # macOS: use AppleScript to open Terminal.app
        script = f"""
        tell application "Terminal"
            do script "{sys.executable} -m zippy.cli --help; read -p 'Press Enter to close...'"
            activate
        end tell
        """
        subprocess.run(["osascript", "-e", script])
    else:
        # Linux: use x-terminal-emulator or fallback
        terminal = os.environ.get("TERMINAL", "x-terminal-emulator")
        try:
            subprocess.run(
                [
                    terminal,
                    "-e",
                    f"{sys.executable} -m zippy.cli --help; read -p 'Press Enter to close...'",
                ]
            )
        except FileNotFoundError:
            # Fallback: try common terminals
            for term in ["gnome-terminal", "konsole", "xterm"]:
                try:
                    subprocess.run(
                        [
                            term,
                            "-e",
                            f"{sys.executable} -m zippy.cli --help; read -p 'Press Enter to close...'",
                        ]
                    )
                    break
                except FileNotFoundError:
                    continue


if __name__ == "__main__":
    main()
