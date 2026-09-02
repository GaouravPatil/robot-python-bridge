import asyncio
import json
import time
from playwright.async_api import async_playwright

HOSTED_URL = "https://gaouravpatil.github.io/robot-python-bridge/"

# Global variable to hold the latest state
latest_state = {}
last_print_time = 0

async def main():
    global latest_state, last_print_time
    print(f"Connecting to hosted Web App: {HOSTED_URL}...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Callback for receiving live robot-state messages from browser tab
        async def receive_state(source, data):
            global latest_state, last_print_time
            latest_state = json.loads(data)
            now = time.time()
            
            # Print live state summary at most twice per second to prevent terminal flooding
            if now - last_print_time >= 0.5:
                last_print_time = now
                pos = f"x={latest_state.get('x')}, z={latest_state.get('z')}, rot={latest_state.get('rotationY')}"
                fps = latest_state.get('fps', 'N/A')
                near = "YES ⚠️" if latest_state.get('nearBox') else "NO"
                print(f"[LIVE STATE] Pos: ({pos}) | FPS: {fps} | Near Box: {near}")

        # Expose binding so browser script can call window.robotState(...)
        await page.expose_binding("robotState", receive_state)

        # Inject content script to capture window.postMessage("robot-state")
        await page.add_init_script("""
            window.addEventListener("message", (event) => {
                if (event.data?.type === "robot-state") {
                    window.robotState(JSON.stringify(event.data));
                }
            });
        """)

        await page.goto(HOSTED_URL)
        print("\n✅ Connected successfully to live hosted page!")
        print("-" * 60)
        print("Available Commands:")
        print("  w / s / a / d : Move Forward / Backward / Turn Left / Turn Right (pulse 0.5s)")
        print("  w-on / s-on   : Hold Move Forward / Backward")
        print("  a-on / d-on   : Hold Turn Left / Turn Right")
        print("  stop          : Stop all movement")
        print("  t [x] [z]     : Teleport (default: 0 0)")
        print("  c [hex]       : Change color (e.g., #ff0000, #00ff00, #ff00ff)")
        print("  status        : Show current robot state")
        print("  q             : Quit")
        print("-" * 60 + "\n")

        async def send_command(cmd_payload):
            await page.evaluate("""
                (cmd) => {
                    window.postMessage({
                        type: "robot-command",
                        ...cmd
                    }, "*");
                }
            """, cmd_payload)

        while True:
            cmd = await asyncio.to_thread(input, "> ")
            cmd = cmd.strip().lower()

            if not cmd:
                continue

            if cmd == "q":
                print("Exiting Playwright bridge...")
                break

            elif cmd == "w":
                await send_command({"forward": True})
                await asyncio.sleep(0.5)
                await send_command({"forward": False})

            elif cmd == "s":
                await send_command({"back": True})
                await asyncio.sleep(0.5)
                await send_command({"back": False})

            elif cmd == "a":
                await send_command({"left": True})
                await asyncio.sleep(0.5)
                await send_command({"left": False})

            elif cmd == "d":
                await send_command({"right": True})
                await asyncio.sleep(0.5)
                await send_command({"right": False})

            elif cmd == "w-on":
                await send_command({"forward": True})
            elif cmd == "s-on":
                await send_command({"back": True})
            elif cmd == "a-on":
                await send_command({"left": True})
            elif cmd == "d-on":
                await send_command({"right": True})

            elif cmd == "stop":
                await send_command({"stop": True})

            elif cmd.startswith("t"):
                parts = cmd.split()
                x = float(parts[1]) if len(parts) > 1 else 0.0
                z = float(parts[2]) if len(parts) > 2 else 0.0
                await send_command({"action": "teleport", "x": x, "z": z})
                print(f"Teleported robot to ({x}, {z})")

            elif cmd.startswith("c"):
                parts = cmd.split()
                color = parts[1] if len(parts) > 1 else "#ff0000"
                if not color.startswith("#"):
                    color = "#" + color
                await send_command({"action": "color", "color": color})
                print(f"Changed robot color to {color}")

            elif cmd == "status":
                print("\n--- CURRENT ROBOT STATE ---")
                print(json.dumps(latest_state, indent=2))
                print("---------------------------\n")

            else:
                print(f"Unknown command: '{cmd}'")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())