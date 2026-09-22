import asyncio
import json
import time
import websockets

WS_HOST = "localhost"
WS_PORT = 8765

latest_state = {}
client = None  # current browser connection


def print_state(state):
    """Print one throttled live line: x, z, rotation, FPS, proximity."""
    x = state.get("x")
    z = state.get("z")
    rot = state.get("rotationY")
    fps = state.get("fps", "N/A")
    near = "YES" if state.get("nearBox") else "NO"
    dist = state.get("nearestBoxDist", "N/A")
    print(f"[LIVE] x={x} z={z} rot={rot} | FPS: {fps} | Near box: {near} (dist={dist})")


async def handle_client(websocket):
    """Receive robot-state messages from the browser."""
    global latest_state, client
    client = websocket
    print("Browser connected ✓")
    last_shown = None
    last_print = 0
    try:
        async for raw in websocket:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if msg.get("type") != "robot-state":
                continue
            latest_state = msg
            key = (msg.get("x"), msg.get("z"), msg.get("rotationY"), msg.get("nearBox"))
            if key == last_shown:
                continue
            if time.time() - last_print >= 0.5:
                last_print = time.time()
                last_shown = key
                print_state(msg)
    finally:
        if client is websocket:
            client = None
        print("Browser disconnected — waiting for reconnect...")


async def send(cmd: dict):
    if client is None:
        print("No browser connected yet — open index.html first.")
        return
    await client.send(json.dumps(cmd))


async def input_loop():
    moves = {"w": "forward", "s": "back", "a": "left", "d": "right"}
    print("Commands: w/s/a/d, w-on/s-on/a-on/d-on, stop, t [x] [z], c [hex], status, q")
    while True:
        cmd = (await asyncio.to_thread(input, "> ")).strip().lower()
        if not cmd:
            continue
        if cmd == "q":
            print("Bye!")
            break
        elif cmd in moves:
            key = moves[cmd]
            await send({key: True})
            await asyncio.sleep(0.5)
            await send({key: False})
        elif cmd in ("w-on", "s-on", "a-on", "d-on"):
            await send({moves[cmd.split("-")[0]]: True})
        elif cmd == "stop":
            await send({"stop": True})
        elif cmd == "status":
            print(json.dumps(latest_state, indent=2) if latest_state else "(no data yet)")
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


async def main():
    async with websockets.serve(handle_client, WS_HOST, WS_PORT):
        print(f"Serving on ws://{WS_HOST}:{WS_PORT} — open index.html in a browser.")
        await input_loop()


if __name__ == "__main__":
    asyncio.run(main())
