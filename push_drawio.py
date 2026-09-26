#!/usr/bin/env python3
"""Create coattails-droid/drawio-live and push a local dir as its full tree.

Steps: create public repo -> create blobs (threaded, batched) -> tree ->
commit -> create refs/heads/main -> enable Pages (main, /).
Auth via dynamic_credentials surrogate for custom.github.
"""
import base64
import concurrent.futures
import json
import os
import sys
import time
import urllib.request
import urllib.error

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request, read_response_body

CRED_NAME = "custom.github"
ALLOWED = ["api.github.com", "github.com"]
API = "https://api.github.com"
OWNER = "coattails-droid"
REPO = "drawio-live"
THREADS = 8
MAX_RETRIES = 6


def api_request(method, path, data=None, raw_bytes=False, retries=MAX_RETRIES):
    url = API + path
    body = data if raw_bytes else (json.dumps(data).encode() if data is not None else None)
    last_err = None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        req.add_header("User-Agent", "muse-github-skill/1.0")
        if body:
            req.add_header("Content-Type", "application/json")
        add_surrogate_to_request(req, CRED_NAME, allowed_hosts=ALLOWED)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = read_response_body(resp)
                return json.loads(raw.decode()) if raw else {}
        except urllib.error.HTTPError as e:
            eb = e.read().decode(errors="replace")
            last_err = f"HTTP {e.code} {method} {path}: {eb[:400]}"
            if e.code in (429,) or (e.code == 403 and "rate limit" in eb.lower()):
                wait = min(120, 2 ** attempt * 5)
                print(f"  rate-limited, sleeping {wait}s (attempt {attempt+1})", file=sys.stderr)
                time.sleep(wait)
                continue
            if e.code in (500, 502, 503) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(last_err)
        except Exception as e:
            last_err = f"{type(e).__name__} {method} {path}: {e}"
            time.sleep(2 ** attempt)
    raise RuntimeError(f"exhausted retries: {last_err}")


def create_repo():
    try:
        r = api_request("POST", "/user/repos", {
            "name": REPO,
            "private": False,
            "description": "Static GitHub Pages mirror of the draw.io diagram editor (jgraph/drawio webapp, no backend).",
            "auto_init": False,
            "has_issues": False,
            "has_wiki": False,
        })
        print(f"Created repo: {r.get('full_name')}")
    except RuntimeError as e:
        if "422" in str(e) and "already exists" in str(e).lower():
            print("Repo already exists, continuing.")
        else:
            raise


def create_blob(owner, repo, local_path):
    with open(local_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode()
    r = api_request("POST", f"/repos/{owner}/{repo}/git/blobs",
                    {"content": content_b64, "encoding": "base64"})
    return r["sha"]


def main():
    local_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    # Exclude the push script itself from the pushed tree
    self_name = os.path.basename(__file__)
    rel_files = []
    for root, dirs, files in os.walk(local_dir):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
        for fn in files:
            if fn.endswith(".pyc"):
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, local_dir)
            if rel == self_name:
                continue
            rel_files.append((rel.replace(os.sep, "/"), full))
    rel_files.sort()
    print(f"Pushing {len(rel_files)} files to {OWNER}/{REPO}")

    create_repo()

    # 1) blobs
    blob_shas = {}
    failures = []

    def do_blob(item):
        rel, full = item
        return rel, create_blob(OWNER, REPO, full)

    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as ex:
        futs = {ex.submit(do_blob, item): item for item in rel_files}
        done = 0
        for fut in concurrent.futures.as_completed(futs):
            rel = futs[fut][0]
            try:
                r, sha = fut.result()
                blob_shas[r] = sha
            except Exception as e:
                failures.append((rel, str(e)))
            done += 1
            if done % 250 == 0:
                print(f"  blobs: {done}/{len(rel_files)}")
    if failures:
        print(f"FAILED blobs ({len(failures)}):", file=sys.stderr)
        for rel, err in failures[:20]:
            print(f"  {rel}: {err}", file=sys.stderr)
        sys.exit(1)
    print(f"  all {len(blob_shas)} blobs created")

    # 2) tree
    tree = [{"path": rel, "mode": "100644", "type": "blob", "sha": blob_shas[rel]}
            for rel in sorted(blob_shas)]
    t = api_request("POST", f"/repos/{OWNER}/{REPO}/git/trees", {"tree": tree})
    tree_sha = t["sha"]
    print(f"tree {tree_sha[:7]}")

    # 3) commit (no parents: fresh repo)
    c = api_request("POST", f"/repos/{OWNER}/{REPO}/git/commits", {
        "message": "Deploy draw.io static webapp (upstream jgraph/drawio@82af4345, v31.5.2)",
        "tree": tree_sha,
        "parents": [],
    })
    commit_sha = c["sha"]
    print(f"commit {commit_sha[:7]}")

    # 4) create main ref
    api_request("POST", f"/repos/{OWNER}/{REPO}/git/refs",
                {"ref": "refs/heads/main", "sha": commit_sha})
    print("ref refs/heads/main created")

    # 5) enable Pages (legacy build from main root)
    try:
        p = api_request("POST", f"/repos/{OWNER}/{REPO}/pages",
                        {"source": {"branch": "main", "path": "/"}})
        print(f"Pages enabled: {p.get('html_url')}")
    except RuntimeError as e:
        print(f"Pages enable note: {e}", file=sys.stderr)

    print("DONE")


if __name__ == "__main__":
    main()
