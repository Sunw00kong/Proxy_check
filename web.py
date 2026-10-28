"""A tiny local web UI for Proxy_check (Flask).

One page: the target is LOCKED (shown read-only, no input box) to preserve
the scope/safety rule from Sscrape. You paste or edit the proxy list, hit
"Check", and see which proxies are alive, their status, and their latency.

Run it locally:
    python web.py        # serves on http://127.0.0.1:5001

Note: clicking "Check" sends live requests to the locked TARGET *through*
each proxy. Only use it against a target you're authorized to test.
"""

from pathlib import Path

from flask import Flask, render_template_string, request

import Sscrape  # the existing script, imported as a module (same folder)

app = Flask(__name__)

DEFAULT_PROXIES = Path(__file__).resolve().parent / "proxies.txt"


def _default_proxy_text() -> str:
    """Prefill the textarea with proxies.txt if it exists."""
    try:
        return DEFAULT_PROXIES.read_text()
    except OSError:
        return ""


PAGE = """
<!doctype html><meta charset="utf-8"><title>Proxy_check</title>
<style>
  body{font:14px system-ui;margin:2rem;max-width:820px;color:#1a1a1a}
  h1{margin:0 0 .25rem} .sub{color:#666;margin-bottom:1rem}
  .locked{background:#f4f4f4;border:1px solid #ddd;border-radius:6px;padding:.4rem .6rem;margin-bottom:1rem}
  textarea{width:100%;min-height:150px;padding:.5rem;border:1px solid #ccc;border-radius:6px;font-family:monospace}
  .row{display:flex;gap:.5rem;align-items:center;margin:.6rem 0}
  input[type=number]{width:70px;padding:.35rem;border:1px solid #ccc;border-radius:6px}
  button{padding:.5rem 1rem;border:0;border-radius:6px;background:#0b5;color:#fff;cursor:pointer}
  table{border-collapse:collapse;width:100%;margin-top:1rem}
  th,td{text-align:left;padding:.4rem .6rem;border-bottom:1px solid #eee}
  .ok{color:#0a0;font-weight:600} .dead{color:#b00}
  code{background:#f4f4f4;padding:.1rem .3rem;border-radius:4px}
</style>
<h1>Proxy_check</h1>
<div class="sub">Check which proxies can reach the in-scope target.</div>

<div class="locked">Target (locked): <code>{{ target }}</code></div>

<form method="post" action="/check">
  <textarea name="proxies" placeholder="one proxy per line, e.g. http://1.2.3.4:8080">{{ proxies_text }}</textarea>
  <div class="row">
    <label>Timeout (s) <input type="number" name="timeout" value="{{ timeout }}" min="1" max="60"></label>
    <label>Workers <input type="number" name="workers" value="{{ workers }}" min="1" max="200"></label>
    <button type="submit">Check</button>
  </div>
</form>

{% if results is not none %}
  <p><b>{{ working|length }}</b> working / <b>{{ results|length }}</b> checked
     &middot; sends live requests to the locked target</p>
  <table>
    <tr><th>#</th><th>Proxy</th><th>Result</th><th>Detail</th><th>Latency</th></tr>
    {% for r in ordered %}
    <tr>
      <td>{{ loop.index }}</td>
      <td><code>{{ r.proxy }}</code></td>
      <td class="{{ 'ok' if r.ok else 'dead' }}">{{ 'OK' if r.ok else 'DEAD' }}</td>
      <td>{{ r.detail }}</td>
      <td>{{ '%.2f'|format(r.elapsed) }}s</td>
    </tr>
    {% endfor %}
  </table>
{% endif %}
"""


def _render(results=None, proxies_text=None, timeout=8, workers=20):
    working = [r for r in (results or []) if r["ok"]]
    # working first (fastest), then the dead ones
    ordered = sorted(results or [], key=lambda r: (not r["ok"], r["elapsed"]))
    return render_template_string(
        PAGE, target=Sscrape.TARGET,
        proxies_text=proxies_text if proxies_text is not None else _default_proxy_text(),
        timeout=timeout, workers=workers,
        results=results, working=working, ordered=ordered,
    )


@app.get("/")
def index():
    return _render()


@app.post("/check")
def check():
    raw = request.form.get("proxies", "")
    proxies = [line.strip() for line in raw.splitlines() if line.strip()]
    timeout = int(request.form.get("timeout", 8))
    workers = int(request.form.get("workers", 20))
    # Sscrape.run tests every proxy in parallel and returns result dicts.
    results = Sscrape.run(proxies, timeout, workers)
    return _render(results=results, proxies_text=raw, timeout=timeout, workers=workers)


def main() -> None:
    # 127.0.0.1 + a different port than Ferrox so both can run at once.
    app.run(host="127.0.0.1", port=5001, debug=False)


if __name__ == "__main__":
    main()
