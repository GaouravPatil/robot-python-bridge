"""Robot Python Bridge — Proxie DevOps Assignment (Round 1).

Proves a fully static hosted web app can be observed and controlled
from ordinary local Python, with no backend added to the hosting.

Hosting: pure static files only (GitHub Pages). index.html is untouched.
Mechanism: Playwright (Chrome DevTools Protocol) automation from local Python.
  - Read (page -> Python): page broadcasts window.postMessage({type:"robot-state"...})
    every frame. We catch it with add_init_script and forward it via
    expose_binding("robotState") into Python. Event-driven, sub-second, no screenshots.
  - Write (Python -> page): page listens for window.postMessage({type:"robot-command"...}).
    We inject commands with page.evaluate(). Reuses the page's own key handling.
"""

import asyncio
import json
import os
import time
from playwright.async_api import async_playwright

HOSTED_URL = "https://gaouravpatil.github.io/robot-python-bridge/"

# Set HEADLESS=1 to run without opening a visible window (CI / servers without display).
HEADLESS = os.getenv("HEADLESS", "0") == "1"

latest_state = {}
last_print_time = 0


async def main():
    global latest_state, last_print_time

    print(f"Connecting to {HOSTED_URL}...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        page = await browser.new_page()

        last_shown = None

        async def receive_state(_, data):
            global latest_state, last_print_time
            nonlocal last_shown
            latest_state = json.loads(data)

            # Only print if robot actually moved / turned / near-box changed.
            # This stops terminal spam when idle, but page still sends 60 msgs/sec.
            key = (
                latest_state.get("x"),
                latest_state.get("z"),
                latest_state.get("rotationY"),
                latest_state.get("nearBox"),
            )
            if key == last_shown:
                return

            now = time.time()
            if now - last_print_time >= 0.5:
                last_print_time = now
                last_shown = key
                x, z, rot, near_box = key
                fps = latest_state.get("fps", "N/A")
                near = "YES" if near_box else "NO"
                print(f"[LIVE] x={x} z={z} rot={rot} | FPS: {fps} | Near box: {near}")

        await page.expose_binding("robotState", receive_state)

        await page.add_init_script("""
            window.addEventListener("message", (event) => {
                if (event.data?.type === "robot-state") {
                    window.robotState(JSON.stringify(event.data));
                }
            });
        """)

        await page.goto(HOSTED_URL)
        print("Connected! Commands: w/s/a/d, w-on/s-on/a-on/d-on, stop, t [x] [z], c [hex], status, q")

        async def send(cmd):
            await page.evaluate(
                "(cmd) => window.postMessage({ type: 'robot-command', ...cmd }, '*')",
                cmd,
            )

        moves = {"w": "forward", "s": "back", "a": "left", "d": "right"}

        while True:
            cmd = (await asyncio.to_thread(input, "> ")).strip().lower()

            if not cmd:
                continue
            if cmd == "q":
                print("Bye!")
                break

            if cmd in moves:
                key = moves[cmd]
                await send({key: True})
                await asyncio.sleep(0.5)
                await send({key: False})

            elif cmd in ("w-on", "s-on", "a-on", "d-on"):
                key = moves[cmd.split("-")[0]]
                await send({key: True})

            elif cmd == "stop":
                await send({"stop": True})

            elif cmd == "status":
                print(json.dumps(latest_state, indent=2))

            elif cmd == "t" or cmd.startswith("t "):
                parts = cmd.split()
                try:
                    x = float(parts[1]) if len(parts) > 1 else 0.0
                    z = float(parts[2]) if len(parts) > 2 else 0.0
                except ValueError:
                    print("Usage: t [x] [z]  (numbers only)")
                    continue
                await send({"action": "teleport", "x": x, "z": z})
                print(f"Teleported to ({x}, {z})")

            elif cmd == "c" or cmd.startswith("c "):
                parts = cmd.split()
                color = parts[1] if len(parts) > 1 else "#ff0000"
                if not color.startswith("#"):
                    color = "#" + color
                await send({"action": "color", "color": color})
                print(f"Color changed to {color}")

            else:
                print(f"Unknown command: '{cmd}'")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
