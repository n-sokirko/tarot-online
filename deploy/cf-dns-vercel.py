"""
Repoint sokirdon.com from the (retired) Cloudflare Tunnel to Vercel.

Reads the zone-scoped Cloudflare API token that `cloudflared login` left in
~/.cloudflared/cert.pem — the same credential `cloudflared tunnel route dns`
uses — so no extra secret has to be stored anywhere.

Touches exactly three things and nothing else:
  * deletes the apex CNAME pointing at *.cfargotunnel.com
  * creates two A records for the apex, pointing at Vercel
  * creates a CNAME for www, pointing at Vercel

`api.sokirdon.com` is left alone: the frontend now calls Railway directly, and
that record is not in the way. Records are proxied=False on purpose — behind
Cloudflare's orange cloud Vercel sees Cloudflare's addresses instead of its own
and never issues a certificate.

    python deploy/cf-dns-vercel.py            # dry run, prints the plan
    python deploy/cf-dns-vercel.py --apply    # actually change the zone
    python deploy/cf-dns-vercel.py --list     # just show the current records
"""
import argparse
import base64
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request

CERT = pathlib.Path.home() / ".cloudflared" / "cert.pem"
APEX = "sokirdon.com"

# From Vercel's domain config API (GET /v6/domains/<domain>/config), rank 1.
WANTED = [
    {"type": "A", "name": APEX, "content": "216.198.79.1", "proxied": False, "ttl": 1},
    {"type": "A", "name": APEX, "content": "64.29.17.1", "proxied": False, "ttl": 1},
    {"type": "CNAME", "name": "www", "content": "5d8c0496c7026cc1.vercel-dns-017.com",
     "proxied": False, "ttl": 1},
]


def credentials() -> tuple[str, str]:
    if not CERT.exists():
        sys.exit(f"{CERT} not found — run `cloudflared login` first.")
    block = re.search(
        r"-----BEGIN ARGO TUNNEL TOKEN-----(.*?)-----END ARGO TUNNEL TOKEN-----",
        CERT.read_text(), re.S,
    )
    if not block:
        sys.exit(f"{CERT} has no ARGO TUNNEL TOKEN block.")
    tok = json.loads(base64.b64decode("".join(block.group(1).split())))
    return tok["apiToken"], tok["zoneID"]


def cf(api: str, path: str, method: str = "GET", body: dict | None = None) -> dict:
    req = urllib.request.Request(
        "https://api.cloudflare.com/client/v4" + path,
        method=method,
        data=json.dumps(body).encode() if body else None,
        headers={"Authorization": "Bearer " + api, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        return json.load(exc)


def records(api: str, zone: str) -> list[dict]:
    res = cf(api, f"/zones/{zone}/dns_records?per_page=100")
    if not res.get("success"):
        sys.exit(f"could not read the zone: {res.get('errors')}")
    return res["result"]


def show(recs: list[dict]) -> None:
    for r in recs:
        print(f"  {r['name']:<24} {r['type']:<6} {r['content'][:46]:<46} proxied={r['proxied']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write the changes")
    parser.add_argument("--list", action="store_true", help="only print current records")
    args = parser.parse_args()

    api, zone = credentials()
    name = cf(api, f"/zones/{zone}")["result"]["name"]
    print(f"zone: {name}\n\ncurrent records:")
    current = records(api, zone)
    show(current)

    if args.list:
        return

    stale = [r for r in current
             if r["name"] == APEX and r["type"] == "CNAME" and "cfargotunnel.com" in r["content"]]
    have = {(r["type"], r["name"], r["content"]) for r in current}
    todo = [w for w in WANTED
            if (w["type"], w["name"] if w["name"] != "www" else f"www.{APEX}", w["content"]) not in have]

    print("\nplan:")
    for r in stale:
        print(f"  DELETE {r['type']:<6} {r['name']} -> {r['content'][:40]}")
    for w in todo:
        print(f"  CREATE {w['type']:<6} {w['name']} -> {w['content']} (proxied={w['proxied']})")
    if not stale and not todo:
        print("  nothing to do — the zone already points at Vercel")
        return

    if not args.apply:
        print("\ndry run — re-run with --apply to write these changes")
        return

    print()
    for r in stale:
        res = cf(api, f"/zones/{zone}/dns_records/{r['id']}", "DELETE")
        print(f"deleted {r['name']} CNAME: ok={bool(res.get('result') or res.get('success'))}")
    for w in todo:
        res = cf(api, f"/zones/{zone}/dns_records", "POST", w)
        if res.get("success"):
            print(f"created {w['type']:<6} {w['name']} -> {w['content']}")
        else:
            print(f"FAILED  {w['type']:<6} {w['name']}: {res.get('errors')}")

    print("\nzone now:")
    show(records(api, zone))


if __name__ == "__main__":
    main()
