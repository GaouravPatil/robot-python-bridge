# Robot Python Bridge

Live two-way bridge between ordinary local Python and a static Three.js app hosted on GitHub Pages (`https://gaouravpatil.github.io/robot-python-bridge/`). Python reads live robot state (position, rotation, FPS, near-box) streamed every frame and writes commands (move, teleport, color) into the live hosted page.

Constraint compliance: hosting stays pure static files — `index.html` is untouched, no server added to it. The bridge runs entirely from local Python. See `demo_transcript.txt` for a live exchange proof.

## How to Run

Prerequisites: Python 3.8+, Chromium (installed via Playwright).

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

python bridge.py
# Set HEADLESS=1 to run without a visible window (servers / CI):
# HEADLESS=1 python bridge.py
```

Commands: `w / s / a / d` pulse-move 0.5s, `w-on / s-on / a-on / d-on` hold, `stop` halt, `t [x] [z]` teleport (default `0 0`), `c [hex]` body color, `status` full JSON dump, `q` quit.

## Why This Mechanism

We picked Playwright (Chrome DevTools Protocol automation) with `expose_binding` + `window.postMessage` interception because it needs no backend, no extension, and no changes to the static host, while staying event-driven and sub-second in both directions. A WebSocket relay or WebRTC channel would require hosting and maintaining a separate server, and an extension would add install friction, so Playwright is the simplest fit for local control of a public static URL.

How it works: page → Python via `postMessage({type: "robot-state"})` caught by `add_init_script` and forwarded through `expose_binding("robotState")`; Python → page via `page.evaluate(postMessage({type: "robot-command"}))`, which reuses the page's own key/action handling. No screenshots, no polling.

## Trade-offs

| Aspect | Evaluation |
|---|---|
| Latency | Sub-second, near-instant locally — in-process JS-to-Python binding for reads, single `evaluate` for writes. Page streams ~60 msgs/sec; Python prints at most twice/sec and only on change. |
| Security | Nothing exposed to the internet. Risk is local only: script launches Chromium on your machine. No secrets leave the host. |
| Browser permissions | Requires local permission to launch Chromium via Playwright. No extension install, no remote debugging flags, no extra browser permissions. |
| Hosting | Pure static (GitHub Pages / S3 / Vercel). Zero backend cost. |
| Limitations | Chromium + Python must run on the same machine driving the session. Cannot observe a detached stranger's tab, cannot scale to remote multi-user control — that would need a WebSocket relay instead. Fails without display unless `HEADLESS=1` is set. |

## Demo

Full terminal transcript: [`demo_transcript.txt`](demo_transcript.txt). Record a GIF/screen recording of `python bridge.py` alongside the hosted tab for visual proof — robot visibly moves, teleports, and recolors as commands are typed.
