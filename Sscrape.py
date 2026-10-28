import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
TIMEOUT = 8   # seconds to wait on one proxy before giving up
WORKERS = 20  # how many proxies we test at the same time (the "triage team")

# The one authorized, in-scope target we test proxies against.
# This is HARDCODED on purpose: it keeps the tool tied to a specific
# permitted scope (bug bounty / explicit authorization) and stops it from
# being trivially repointed at arbitrary sites. Do not turn this into a flag.
TARGET = "https://app.aurory.io"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_proxies(path="proxies.txt"):
    """Read the proxy pool: one proxy per line, blanks skipped."""
    with open(path, "r") as f:
        return [line.strip() for line in f if line.strip()]


def check_proxy(proxy):
    """Test ONE proxy against TARGET and time how long it takes.

    Returns a (proxy, ok, detail, elapsed) tuple instead of printing, so the
    thread pool can hand results back cleanly. If each worker printed on its
    own, the lines would interleave into mush.

    `elapsed` is the proxy's "pulse strength": a low number means a healthy,
    fast proxy; a number near TIMEOUT means it is barely responding.
    """
    proxy_dict = {"http": proxy, "https": proxy}
    start = time.perf_counter()  # stopwatch start
    try:
        res = requests.get(TARGET, proxies=proxy_dict, timeout=TIMEOUT)
        elapsed = time.perf_counter() - start
        return (proxy, True, res.status_code, elapsed)
    except requests.RequestException as e:
        # Still record how long we waited before the failure.
        elapsed = time.perf_counter() - start
        return (proxy, False, type(e).__name__, elapsed)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
def main():
    proxies = load_proxies()

    # Spin up a team of WORKERS medics; each tests a different proxy at once.
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        # Hand every proxy to the pool...
        futures = [pool.submit(check_proxy, p) for p in proxies]
        # ...and print each result as it finishes (not in list order).
        for fut in as_completed(futures):
            proxy, ok, detail, elapsed = fut.result()
            tag = "[OK]  " if ok else "[DEAD]"
            print(f"{tag} {proxy} -> {detail}  ({elapsed:.2f}s)")


if __name__ == "__main__":
    main()
