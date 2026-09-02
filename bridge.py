import asyncio
import json
from playwright.async_api import async_playwright

HOSTED_URL = "https://YOUR-HOSTED-URL.com"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Receive robot state from the page
        async def receive_state(source, data):
            state = json.loads(data)
            print("Robot state:", state)

        await page.expose_binding("robotState", receive_state)

        await page.add_init_script("""
            window.addEventListener("message", (event) => {
                if (event.data?.type === "robot-state") {
                    window.robotState(JSON.stringify(event.data));
                }
            });
        """)

        await page.goto(HOSTED_URL)

        print("Connected.")
        print("Commands: w, s, a, d, t, c, q")

        while True:
            command = await asyncio.to_thread(input, "> ")

            if command == "q":
                break

            commands = {
                "w": {"action": "move", "direction": "forward"},
                "s": {"action": "move", "direction": "backward"},
                "a": {"action": "rotate", "direction": "left"},
                "d": {"action": "rotate", "direction": "right"},
                "t": {"action": "teleport", "x": 0, "y": 0, "z": 0},
                "c": {"action": "color", "color": "#ff0000"}
            }

            if command in commands:
                await page.evaluate("""
                    (cmd) => {
                        window.postMessage({
                            type: "robot-command",
                            ...cmd
                        }, "*");
                    }
                """, commands[command])

        await browser.close()


asyncio.run(main())