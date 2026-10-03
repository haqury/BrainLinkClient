"""Capture raw BrainLink BLE packets for ~12 seconds and summarize markers."""
import asyncio
from collections import Counter
from pathlib import Path

from bleak import BleakClient

ADDRESS = "CC:36:16:32:7E:F2"
OUT = Path(__file__).resolve().parents[1] / "logs" / "ble_raw_dump.txt"
DURATION = 12


async def main():
    OUT.write_text("", encoding="utf-8")
    counts = Counter()
    samples = []

    def on_notify(_sender, data: bytearray):
        b = bytes(data)
        markers = []
        if b.find(bytes([0xAA, 0xAA, 0xBB, 0x0C, 0x02])) >= 0:
            markers.append("OLD_EXT")
        if b.find(bytes([0xAA, 0xBB, 0x0C])) >= 0:
            markers.append("AA_BB_0C")
        if b.find(bytes([0xAA, 0xAA, 0x0C])) >= 0:
            markers.append("AA_AA_0C")
        if 0x06 in b and 0x55 in b:
            markers.append("06_55")
        if b.find(bytes([0xAA, 0xAA, 0x20])) >= 0:
            markers.append("EEG")
        if b.find(bytes([0xAA, 0xAA, 0x07])) >= 0:
            markers.append("GYRO")
        for m in markers or ["OTHER"]:
            counts[m] += 1
        line = f"{markers} | {b.hex(' ')}\n"
        samples.append(line)
        with OUT.open("a", encoding="utf-8") as f:
            f.write(line)

    print(f"Connecting to {ADDRESS}...")
    async with BleakClient(ADDRESS) as client:
        print("Connected, listening...")
        for service in client.services:
            for char in service.characteristics:
                if "notify" in char.properties:
                    print(f"notify on {char.uuid}")
                    await client.start_notify(char.uuid, on_notify)
        await asyncio.sleep(DURATION)

    print("Counts:", dict(counts))
    print(f"Wrote {len(samples)} packets to {OUT}")
    # Show a few interesting lines
    interesting = [s for s in samples if "OLD_EXT" in s or "06_55" in s or "AA_BB" in s or "AA_AA_0C" in s]
    print(f"Interesting packets: {len(interesting)}")
    for s in interesting[:15]:
        print(s.rstrip())


if __name__ == "__main__":
    asyncio.run(main())
