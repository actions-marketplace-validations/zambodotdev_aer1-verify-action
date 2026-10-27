#!/usr/bin/env python3
"""Verify Zambo receipts for the aer1-verify-action GitHub Action.

Scans the pull request body (and comments, when enabled) plus any files
named by the `paths` input for zambo receipt links, then checks every
receipt id against https://zambo.dev/api/v2/receipt/{id}/verify.
Exits 1 when any receipt does not verify, or when no receipts are found
and require-receipts is true. Standard library only.
"""
import glob
import json
import os
import re
import sys
import urllib.error
import urllib.request

UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
LINK_RE = re.compile(r"zambo\.dev/[^\s\"'<>\])]*?(" + UUID + ")", re.I)
VERIFY_URL = "https://zambo.dev/api/v2/receipt/{id}/verify"


def extract_ids(text):
    ids, seen = [], set()
    for m in LINK_RE.finditer(text or ""):
        i = m.group(1).lower()
        if i not in seen:
            seen.add(i)
            ids.append(i)
    return ids


def ids_from_json_text(text):
    """A receipt file may itself be JSON carrying the receipt id."""
    try:
        data = json.loads(text)
    except Exception:
        return []
    out = []
    if isinstance(data, dict):
        for key in ("id", "receipt_id"):
            v = data.get(key)
            if isinstance(v, str) and re.fullmatch(UUID, v, re.I):
                out.append(v.lower())
        meta = data.get("_meta") or data.get("meta") or {}
        if isinstance(meta, dict):
            r = meta.get("dev.zambo/receipt")
            if (
                isinstance(r, dict)
                and isinstance(r.get("id"), str)
                and re.fullmatch(UUID, r["id"], re.I)
            ):
                out.append(r["id"].lower())
    return out


def collect_from_files(patterns):
    texts = []
    for pat in patterns:
        for path in glob.glob(pat, recursive=True):
            if os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        texts.append(f.read())
                except OSError:
                    pass
    return texts


def gh_api(path, token):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "User-Agent": "aer1-verify-action",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def collect_from_pr(include_comments, token):
    texts = []
    event = {}
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    if event_path and os.path.isfile(event_path):
        try:
            with open(event_path, "r", encoding="utf-8") as f:
                event = json.load(f)
        except Exception:
            event = {}
    pr = event.get("pull_request") or {}
    if pr.get("title"):
        texts.append(pr["title"])
    if pr.get("body"):
        texts.append(pr["body"])
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if include_comments and token and pr.get("number") and repo:
        try:
            for c in gh_api(f"/repos/{repo}/issues/{pr['number']}/comments?per_page=100", token):
                if c.get("body"):
                    texts.append(c["body"])
            for c in gh_api(f"/repos/{repo}/pulls/{pr['number']}/comments?per_page=100", token):
                if c.get("body"):
                    texts.append(c["body"])
        except Exception as e:
            print(f"warning: could not read PR comments: {e}")
    return texts


def verify_id(receipt_id, opener=None):
    req = urllib.request.Request(
        VERIFY_URL.format(id=receipt_id), headers={"User-Agent": "aer1-verify-action"}
    )
    open_fn = opener or urllib.request.urlopen
    try:
        with open_fn(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("verification_status", "unknown")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return "not found"
        return f"error (http {e.code})"
    except Exception:
        return "unreachable"


def main():
    paths = [p.strip() for p in re.split(r"[,\n]", os.environ.get("INPUT_PATHS", "")) if p.strip()]
    require = os.environ.get("INPUT_REQUIRE_RECEIPTS", "false").lower() == "true"
    include_comments = os.environ.get("INPUT_INCLUDE_COMMENTS", "true").lower() != "false"
    token = os.environ.get("GH_TOKEN", "") or os.environ.get("GITHUB_TOKEN", "")

    texts = collect_from_pr(include_comments, token) + collect_from_files(paths)

    ids, seen = [], set()
    for t in texts:
        for i in extract_ids(t) + ids_from_json_text(t):
            if i not in seen:
                seen.add(i)
                ids.append(i)

    if not ids:
        print("no zambo receipts found")
        if require:
            print("require-receipts is true, failing the build")
            return 1
        return 0

    results = []
    bad = 0
    for i in ids:
        status = verify_id(i)
        ok = status == "verified"
        if not ok:
            bad += 1
        print(f"{status} {i} https://zambo.dev/verify/?id={i}")
        results.append((i, status))

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if summary_path:
        try:
            with open(summary_path, "a", encoding="utf-8") as f:
                f.write("| receipt | result |\n|---|---|\n")
                for i, s in results:
                    f.write(f"| [{i}](https://zambo.dev/verify/?id={i}) | {s} |\n")
        except OSError:
            pass

    print(f"{len(ids) - bad} of {len(ids)} receipts verified")
    print("want this on your own ai: https://zambo.dev/add/?ref=verify-action")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
