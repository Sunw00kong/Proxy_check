import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import requests

# ---------------------------------------------------------------------------
# Target
# ---------------------------------------------------------------------------
# The one authorized, in-scope target we test proxies against.
# HARDCODED on purpose: it keeps the tool tied to a specific permitted scope
# (bug bounty / explicit authorization) and stops it from being trivially
# repointed at arbitrary sites. There is deliberately NO --url flag below.
TARGET = "https://app.aurory.io"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_proxies(path):
    """Read the proxy pool: one proxy per line, blanks skipped."""
    with open(path, "r") as f:
        return [line.strip() for line in f if line.strip()]


def check_proxy(proxy, timeout):
    """Test ONE proxy against TARGET and time how long it takes.

    Returns a result dict (not a print) so the thread pool can collect them
    cleanly and we can both display and save them afterwards.

    'elapsed' is the proxy's "pulse strength": low = healthy/fast, near the
    timeout = barely responding.
    """
    proxy_dict = {"http": proxy, "https": proxy}
    start = time.perf_counter()  # stopwatch start
    try:
        res = requests.get(TARGET, proxies=proxy_dict, timeout=timeout)
        elapsed = time.perf_counter() - start
        return {"proxy": proxy, "ok": True, "detail": res.status_code,
                "elapsed": round(elapsed, 3)}
    except requests.RequestException as e:
        # Still record how long we waited before the failure.
        elapsed = time.perf_counter() - start
        return {"proxy": proxy, "ok": False, "detail": type(e).__name__,
                "elapsed": round(elapsed, 3)}


def run(proxies, timeout, workers):
    """Test every proxy in parallel, printing each result as it finishes."""
    results = []
    # Spin up a team of `workers` medics; each tests a different proxy at once.
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(check_proxy, p, timeout) for p in proxies]
        for fut in as_completed(futures):          # results arrive as they finish
            r = fut.result()
            tag = "[OK]  " if r["ok"] else "[DEAD]"
            print(f"{tag} {r['proxy']} -> {r['detail']}  ({r['elapsed']:.2f}s)")
            results.append(r)
    return results


def save_results(results, out_prefix):
    """Write the end-of-run report: a working-proxy list + a full JSON file.

    Returns the list of working proxies (fastest first).
    """
    # Live proxies only, sorted fastest-first (lowest latency = strongest pulse).
    working = sorted((r for r in results if r["ok"]), key=lambda r: r["elapsed"])

    # working.txt -- just the usable proxies, one per line, ready to reuse.
    with open(f"{out_prefix}.working.txt", "w") as f:
        for r in working:
            f.write(r["proxy"] + "\n")

    # JSON report -- full detail for records/automation.
    report = {
        "target": TARGET,
        "generated": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": len(results),
            "working": len(working),
            "dead": len(results) - len(working),
        },
        # working first (by speed), then the dead ones.
        "results": sorted(results, key=lambda r: (not r["ok"], r["elapsed"])),
    }
    with open(f"{out_prefix}.json", "w") as f:
        json.dump(report, f, indent=2)

    return working


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Check a pool of proxies against the in-scope TARGET."
    )
    parser.add_argument("-p", "--proxies", default="proxies.txt",
                        help="proxy list file, one per line (default: proxies.txt)")
    parser.add_argument("-t", "--timeout", type=int, default=8,
                        help="per-proxy timeout in seconds (default: 8)")
    parser.add_argument("-w", "--workers", type=int, default=20,
                        help="number of proxies tested at once (default: 20)")
    parser.add_argument("-o", "--out", default="proxy-results",
                        help="output file prefix (default: proxy-results)")
    # NOTE: intentionally no --url/--target option; TARGET is fixed for scope/safety.
    args = parser.parse_args()

    proxies = load_proxies(args.proxies)
    results = run(proxies, args.timeout, args.workers)
    working = save_results(results, args.out)

    # End-of-shift summary.
    print()
    print(f"Done. {len(working)}/{len(results)} proxies working.")
    print(f"  working list -> {args.out}.working.txt")
    print(f"  full report  -> {args.out}.json")


if __name__ == "__main__":
    main()
