# API call failures on chessortag.org

## What we observe
- Browser console shows `https://api.chessortag.org/api/study/analyze` and `/api/study/engine_top` returning 500/502 plus CORS blocks (“No 'Access-Control-Allow-Origin' header”).
- Front-end code that triggers these calls lives in `website/study/index.html` (fetchEngineMoves, fetchPredictionForFen) and assumes `API_BASE = https://api.chessortag.org`.
- TypeErrors “Failed to fetch” are follow-on symptoms when the browser blocks the response or the network layer fails.

## Possible root causes
- Upstream services down: predictor/engine processes (FastAPI, Stockfish service, etc.) not running or crashing, causing gateway 502 and backend 500.
- CORS misconfiguration: Access-Control-Allow-Origin not set for `https://chessortag.org`, especially on error paths (500/502) or on specific routes (`/api/study/analyze`, `/api/study/engine_top`).
- Reverse proxy routing issues: api.chessortag.org not forwarding to the correct upstream, TLS/hostname mismatch, or stale DNS/SSL leading to connection failures that surface as ERR_FAILED.
- Input/contract errors: invalid/missing FEN payloads or unauthenticated requests reaching strict endpoints may throw server exceptions instead of 4xx with CORS headers.
- Load spikes: fetchEngineMoves fires on every move without throttling; simultaneous analyze + engine_top requests can overload a small instance and trigger 502/timeouts.
- Hardcoded API base: if deployed behind a single host (same-origin) but still pointing to api.*, any outage or certificate issue on that subdomain will break the page even if the main site is up.

## How to avoid and stabilize
- Make CORS global: ensure middleware adds Access-Control-Allow-Origin (and -Headers/-Methods) for `https://chessortag.org` (or `*` if acceptable) on all responses, including errors and 5xx paths.
- Harden upstream services: add health checks, process supervisors, and auto-restart for predictor/engine containers; set resource limits and warm up models/engine to avoid first-request crashes.
- Improve routing resiliency: verify reverse-proxy upstreams for api.chessortag.org, shorten upstream timeouts, and add circuit breakers/fallbacks when predictor is down (serve cached/engine_top-only results).
- Throttle on the client side: debounce analyze/engine_top calls per move (e.g., cancel in-flight before new request) to reduce burst load and avoid piling requests that lead to 502.
- Validate inputs early: reject bad FEN or missing auth with 4xx and include CORS headers; log and surface clear error messages so the UI can degrade gracefully instead of failing fetch.
- Configurable API base: allow env-based API_BASE so same-origin deployments can avoid CORS entirely when served via the main domain or a reverse proxy.
- Monitoring and alerting: track error rate/latency for `/api/study/analyze` and `/api/study/engine_top`, alert when CORS failures or 5xx spikes occur, and keep logs to trace crashes quickly.
