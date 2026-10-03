"""
Smoke helpers for Game → Client COMMAND_TYPE 3–9.

Does not require a live EEG device. Requires:
  - BrainLink Client running with Shared Memory enabled
  - For types 3–8: game config path (--game-config or %APPDATA%\\BrainLink\\game_config_path.txt)
  - Type 9 needs no game config (writes export JSON)

Usage:
  python test_game_commands.py 9
  python test_game_commands.py 4
"""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from examples.shared_memory_client import BrainLinkSharedMemoryClient


COMMANDS = {
    3: ("save_model", "send_save_model_command"),
    4: ("set_prediction_mode", "send_set_prediction_mode_command"),
    5: ("apply_base_fault", "send_apply_base_fault_command"),
    6: ("load_model", "send_load_model_command"),
    7: ("reset_model", "send_reset_model_command"),
    8: ("load_history", "send_load_history_command"),
    9: ("export_settings_for_game", "send_export_settings_command"),
}


def main():
    cmd = int(sys.argv[1]) if len(sys.argv) > 1 else 9
    if cmd not in COMMANDS:
        print(f"Unknown type {cmd}. Use one of: {sorted(COMMANDS)}")
        return 1

    name, method = COMMANDS[cmd]
    client = BrainLinkSharedMemoryClient()
    if not client.connect():
        print("Start BrainLink Client and enable Shared Memory first.")
        return 1

    export_path = Path(os.environ.get("APPDATA", Path.home())) / "BrainLink" / "brainlink_export_for_game.json"
    before = export_path.stat().st_mtime if export_path.exists() else 0.0

    print(f"Sending COMMAND_TYPE={cmd} ({name})...")
    ok = getattr(client, method)()
    time.sleep(0.5)
    print("Done." if ok else "Failed to write command.")

    if cmd == 9 and ok:
        if export_path.exists() and export_path.stat().st_mtime >= before:
            print(f"Export OK: {export_path}")
            print(export_path.read_text(encoding="utf-8")[:500])
        else:
            print(f"Export file missing or not updated: {export_path}")
            ok = False
    else:
        print("Check client tray/log for result.")

    client.disconnect()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
