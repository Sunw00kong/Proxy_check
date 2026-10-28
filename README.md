# Proxy_check

Check which proxies in a pool can reach a single, **authorized** in-scope
target, how fast they respond, and which are dead. CLI + a small local web UI.

> The target is hardcoded on purpose (see `TARGET` in `Sscrape.py`): it keeps
> the tool tied to a specific permitted scope and stops it being trivially
> repointed. Use only against a target you're authorized to test.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## CLI

```bash
python Sscrape.py                       # defaults: proxies.txt, 8s, 20 workers
python Sscrape.py -p list.txt -t 5 -w 50 -o run1
```

Outputs `run1.working.txt` (live proxies, fastest first) and `run1.json`
(full results + summary).

## Web UI

```bash
python web.py        # http://127.0.0.1:5001
```

Paste/edit the proxy list, set timeout/workers, hit **Check**. The target is
shown locked (no input box). A desktop launcher (`web_launch.sh` +
`proxycheck.svg`) is provided for one-click start.

> "Check" sends live requests to the locked target through each proxy.

## Notes

- Proxies should be `http://ip:port`. An `https://` prefix tells the client to
  reach the proxy over TLS, which most public HTTP proxies don't support, so
  they'll falsely show as dead.
