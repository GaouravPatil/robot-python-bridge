# Robot Python Bridge

Live two-way bridge between local Python and a Three.js robot scene. Python runs a WebSocket server on `localhost:8765`. The browser page connects to it, streams robot state every frame, and receives movement / teleport / color commands back.

## How to Run

Prerequisites: Python 3.8+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python bridge.py
```

Then open `index.html` in your browser (or serve it locally). The page auto-connects to `ws://localhost:8765` and retries if the server isn't up yet.

Commands: `w / s / a / d` pulse-move 0.5 s, `w-on / s-on / a-on / d-on` hold, `stop` halt, `t [x] [z]` teleport (default `0 0`), `c [hex]` body color, `status` full JSON dump, `q` quit.

## How It Works

`bridge.py` starts a WebSocket server. The Three.js page (`index.html`) opens a WebSocket client to `localhost:8765`. Every animation frame the page sends the robot's position, rotation, FPS, and box proximity as JSON. Python reads these messages and prints a throttled summary. When you type a command in the terminal, Python sends a JSON message back through the same socket, and the page applies it (key simulation, teleport, color change).

No browser automation, no extensions, no Playwright — just a plain WebSocket.

## Trade-offs

| Aspect | Evaluation |
|---|---|
| Latency | Sub-millisecond over localhost WebSocket. Page streams ~60 msgs/sec; Python prints at most twice/sec and only on change. |
| Security | Server binds to `localhost` only — nothing exposed to the internet. |
| Dependencies | Just the `websockets` Python library. No Chromium, no Playwright. |
| Limitations | Page and Python must be on the same machine (or you'd need to change the bind address). Single client at a time. |
