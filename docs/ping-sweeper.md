# Ping Sweeper

## 1. Feature Overview

The Ping Sweeper is the first tool in the Network Scanner module of the Cyber Security Toolkit.

**What it does:** Given a small range of IPv4 addresses, it checks which hosts respond to a ping and reports their status (reachable/unreachable) along with response time.

**Why it exists:** Host discovery is the first step in almost any network security assessment. Before scanning ports or checking services, you first need to know which devices are actually online. This tool teaches and demonstrates that first step in a safe, bounded, beginner-friendly way.

---

## 2. Cybersecurity Concepts

- **IPv4** — A numeric address (e.g. `192.168.1.5`) that identifies a device on a network.
- **ICMP / ping** — A lightweight network protocol used to test whether a device responds. `ping` sends an ICMP Echo Request and waits for an ICMP Echo Reply.
- **Host discovery** — The process of finding out which IP addresses in a range have a live device behind them.
- **Timeout** — The maximum time we wait for a reply before giving up and marking a host as unreachable.
- **Response time** — How long (in milliseconds) it took for a reply to come back. Lower usually means a closer/faster device.
- **Limitations of ping-based discovery** — A host may exist but still appear "unreachable" if it blocks ICMP via a firewall (this is common, including on Windows by default). Ping tells you "who responded," not "who exists."

---

## 3. Architecture

Actual request flow, as implemented and tested:

```
React (PingSweeper.jsx)
   ↓  fetch() POST
Express Gateway — POST /api/network/ping-sweep
   ↓  axios POST
Flask API — POST /ping-sweep
   ↓  function call
Python ping_sweep() logic (subprocess → ping.exe)
   ↓  returns structured results
Flask → Express → React (renders results table)
```

The browser never communicates with Flask directly — all requests go through the Express Gateway, as required by the project architecture.

---

## 4. Frontend

**File:** `frontend/src/components/PingSweeper.jsx`

**Input fields:**
- Start IP (text input)
- End IP (text input)
- Timeout in seconds (number input)

**Client-side validation:** Before any request is sent, the component checks that Start IP, End IP, and Timeout are all non-empty. If any is missing, a red error message appears immediately and **no network request is made** (confirmed via DevTools Network tab).

**Loading state:** While a scan is in progress, the Scan button is disabled and its label changes to "Scanning..." to prevent duplicate submissions.

**Error state:** If the Express Gateway returns a failure (bad input, or Flask unavailable), the real error message from the backend is displayed in a red box.

**Results table:** On success, displays a table with columns: IP Address, Status, Response Time.

**Authorization warning:** A visible banner reminds the user to only scan hosts they own or have explicit permission to test.

---

## 5. Express API

**Endpoint:** `POST /api/network/ping-sweep`
**File:** `gateway/index.js`

**Request format:**
```json
{
  "start_ip": "127.0.0.1",
  "end_ip": "127.0.0.5",
  "timeout": 1
}
```

**Response format (success):**
```json
{
  "success": true,
  "data": {
    "results": [
      { "ip": "127.0.0.1", "status": "reachable", "response_time": 1.0 }
    ]
  }
}
```

**Response format (error):**
```json
{
  "success": false,
  "error": { "code": "INVALID_INPUT", "message": "..." }
}
```

**Validation:** Checks that `start_ip`, `end_ip` exist and `timeout` is a number, before forwarding to Flask. This is a first line of defense in addition to Flask's own validation.

**Timeout/service-unavailable behavior:** The axios call to Flask has a 10-second cap. If Flask is unreachable (not running, or connection refused/aborted), Express returns HTTP `503` with error code `SERVICE_UNAVAILABLE`, instead of hanging indefinitely.

---

## 6. Flask API

**Endpoint:** `POST /ping-sweep`
**File:** `services/app.py`

**Request validation:**
- Confirms the request body is valid JSON
- Confirms `start_ip` and `end_ip` are present
- Confirms `timeout` is present and is a real number (not a boolean, not a string)

**Response structure:** Same `{ success, data }` / `{ success, error }` shape as Express, which Express relays as-is.

**Error handling:**
- Known validation errors (`PingSweepError` from the Python logic — bad IP, reversed range, oversized range, out-of-bounds timeout) → HTTP `400`, safe message.
- Any unexpected exception → logged privately via `app.logger.error(...)`, client only receives a generic HTTP `500` message. No stack traces are ever exposed to the client.

---

## 7. Python Logic

**File:** `services/network/ping_sweep.py`

- **IP validation:** Uses Python's `ipaddress.IPv4Address` to confirm both `start_ip` and `end_ip` are valid IPv4 addresses.
- **Range validation:** Confirms `start_ip <= end_ip`; rejects reversed ranges.
- **Maximum host limit:** `MAX_HOSTS = 20`. Requests exceeding this are rejected before any pinging starts.
- **Timeout bounds:** `MAX_TIMEOUT_SECONDS = 5`. Timeout must be greater than 0 and at most this value.
- **Concurrency:** Uses `ThreadPoolExecutor` with `MAX_CONCURRENT_PINGS = 10`, so no more than 10 pings run at once — chosen to keep the tool practical on an 8GB RAM laptop.
- **Ping execution:** Calls the operating system's own `ping.exe` via `subprocess.run()`, using Windows-specific flags (`-n 1 -w <timeout_ms>`). No admin privileges or third-party ICMP libraries are required.
- **Response parsing:** Confirms a real reply by checking for `"ttl="` in the output (not just the process exit code, which isn't fully reliable on all Windows versions), and extracts response time in milliseconds via regex.

---

## 8. Testing

The following tests were performed and passed:

**Python logic (pytest, 10/10 passed):**
- Valid range passes validation
- Invalid start IP raises error
- Invalid end IP raises error
- Reversed range raises error
- Range exceeding maximum raises error
- Timeout out of bounds raises error
- `ping_host()` reachable case (mocked)
- `ping_host()` unreachable case (mocked)
- `ping_host()` timeout handling (mocked)
- Real localhost sweep (`127.0.0.1`)

**Flask endpoint (manual PowerShell tests):**
- Valid localhost range → success response with correct data
- Invalid IP → HTTP 400, safe error message
- Missing field → HTTP 400, safe error message
- Invalid (non-numeric) timeout → HTTP 400, safe error message
- `/health` endpoint unaffected

**Express gateway (manual PowerShell tests):**
- `/api/health` still works (proxies to Flask)
- Valid sweep through Express → Flask → correct results
- Invalid IP → Express correctly relays Flask's 400
- Missing field → Express-level 400
- Flask stopped → Express returns HTTP 503, `SERVICE_UNAVAILABLE`

**React UI (manual browser tests):**
- Valid sweep → results table renders correctly
- Invalid IP → red error box, no crash
- Oversized range → red error box "Range too large"
- Flask unavailable → red error box, safe message
- Loading state → button disables and shows "Scanning..."
- Empty Start IP → red error box, no backend request sent (confirmed via DevTools)
- Empty End IP → red error box, no backend request sent
- Empty Timeout → red error box, no backend request sent

No additional test results are claimed beyond what is listed above.

---

## 9. Security

- **Authorization requirement:** The UI displays a clear warning that scanning is only permitted against hosts the user owns or has explicit permission to test.
- **Input validation:** Enforced at three independent layers — React (client-side), Express (gateway-level), and Flask/Python (server-side). This is defense-in-depth: even if one layer is bypassed, the others still protect the system.
- **Resource limits:** Maximum 20 hosts per sweep, maximum 5-second timeout, maximum 10 concurrent pings — chosen to keep the tool safe and usable on an 8GB RAM machine.
- **Safe error messages:** All error responses use a consistent `{ success, error: { code, message } }` structure with clear, non-technical messages.
- **No stack traces exposed:** Unexpected server errors are logged privately (Flask's own logger) and never sent to the client.

---

## 10. Limitations

- A ping response does **not** prove a host "exists" — many devices (including Windows machines by default) block ICMP via firewall while still being fully online and reachable via other protocols.
- Hosts that don't reply to ping will be marked "unreachable," even if they're actually up.
- Testing was performed against `127.0.0.x` loopback addresses — this validates the code path but does **not** represent scanning multiple distinct physical devices on a real network.
- Response time measurements on loopback addresses are extremely small (sub-millisecond) and are not representative of real network latency.
- This tool is an educational implementation and is **not** a replacement for professional-grade network discovery tools (e.g. Nmap) used in real security assessments.

---

## 11. Running the Feature

**Terminal 1 — Flask:**
```powershell
cd D:\Projects\cyber-security-toolkit\services
venv\Scripts\activate
python app.py
```

**Terminal 2 — Express:**
```powershell
cd D:\Projects\cyber-security-toolkit\gateway
node index.js
```

**Terminal 3 — React:**
```powershell
cd D:\Projects\cyber-security-toolkit\frontend
npm run dev
```

Then open `http://localhost:5173` in a browser.
