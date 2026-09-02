# Robot Python Bridge 🤖

A real-time Python bridge for observing and controlling a live, static Three.js Web App hosted on GitHub Pages (`https://gaouravpatil.github.io/robot-python-bridge/`).

---

## 🚀 How to Run

### Prerequisites
- Python 3.8+
- Playwright for Python

### Quickstart

1. **Activate Environment & Install Dependencies:**
   ```bash
   source .venv/bin/activate
   pip install playwright
   playwright install chromium
   ```

2. **Run the Bridge Script:**
   ```bash
   python bridge.py
   ```

3. **Interact via Python CLI:**
   - `w`, `s`, `a`, `d` — Move forward / backward / turn left / turn right (pulse 0.5s)
   - `w-on`, `s-on`, `a-on`, `d-on` — Hold movement key
   - `stop` — Halt all movement
   - `t [x] [z]` — Teleport robot to coordinates (e.g. `t 10 -5`)
   - `c [hex]` — Change robot body color (e.g. `c #ff0000`)
   - `status` — Print detailed JSON state dump
   - `q` — Quit bridge

---

## 🛠️ Architecture & Mechanism Explanation

We chose **Playwright (Browser Automation via Chrome DevTools Protocol)** with **Injected Binding & `window.postMessage` Event Interception** to bridge local Python with the static hosted web page.

### Why this approach over alternatives?
- **No Backend / Server Required**: Keeps the hosted web application strictly static (compliant with assignment constraints).
- **Sub-Millisecond Latency**: Python receives state updates directly from the browser window event loop via Playwright's native JavaScript execution context (`expose_binding`).
- **No Browser Extensions or Complex Setup**: Unlike building a custom Chrome Extension or setting up a WebRTC signaling server / WebSocket relay, this mechanism works out-of-the-box with standard Python libraries against any public static URL without requiring browser extension installations or separate proxy infrastructure.

---

## ⚖️ Trade-offs & Analysis

| Aspect | Evaluation |
|---|---|
| **Latency** | **Near-instant (< 1ms)** — Data is passed in-process between Chromium's JS engine and Playwright's Python event loop. |
| **Security** | Requires running Python locally with permission to launch Chromium instances. Since communication occurs locally between Python and Chromium, no sensitive data is exposed over external relay networks. |
| **Hosting Requirements** | Pure static files (GitHub Pages / S3 / Vercel). Zero backend overhead or WebSockets server cost. |
| **Limitations** | Requires Playwright / Chromium to be running on the host machine driving the session (cannot observe a completely detached user browser without Playwright attachment or extension relay). |
