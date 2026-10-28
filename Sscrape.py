import requests

TIMEOUT = 8  # seconds to wait on one proxy before we "call it" and move on

# The one authorized, in-scope target. Hardcoded on purpose (safety / scope).
TARGET = "https://app.aurory.io"

# Read the proxy list: one entry per line, blanks skipped
with open("proxies.txt", "r") as f:
    proxies = [line.strip() for line in f if line.strip()]

# Go proxy-by-proxy (the patients), checking each one's "pulse" against TARGET
for proxy in proxies:
    proxy_dict = {"http": proxy, "https": proxy}
    try:
        res = requests.get(TARGET, proxies=proxy_dict, timeout=TIMEOUT)
        print(f"[OK]   {proxy} -> {res.status_code}")
    except requests.RequestException as e:
        print(f"[DEAD] {proxy} -> {type(e).__name__}")  # name the failure, no wall of text
