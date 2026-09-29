"""Talk to Buffer's API (https://developers.buffer.com).

Usage:
    python scripts/buffer.py setup                        # list channel IDs (+ Pinterest boards) for config.json
    python scripts/buffer.py introspect CreatePostInput   # show a GraphQL type's fields (for fixing field names)
    python scripts/buffer.py draft posts/<slug>/post.json [--dry-run] [--only facebook,instagram]
    python scripts/buffer.py update posts/<slug>/post.json   # push edited captions to existing drafts

`draft` creates one DRAFT per platform (Facebook, Instagram, Pinterest). Nothing is
published: Sarah approves drafts in Buffer. Images must already be pushed to GitHub
so their raw URLs are public (Buffer has no upload endpoint).

Needs BUFFER_API_KEY in the environment or in a .env file at the repo root
(Buffer -> Settings -> API: https://publish.buffer.com/settings/api).
"""
import hashlib, json, os, pathlib, sys, time, urllib.parse, urllib.request
from common import ROOT, config, image_name, load_json, save_json

ENDPOINT = "https://api.buffer.com"


def api_key():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    key = os.environ.get("BUFFER_API_KEY")
    if not key:
        sys.exit("BUFFER_API_KEY not set. Add it to .env (see .env.example).")
    return key


def gql(query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, method="POST", headers={
        "Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"})
    try:
        res = json.loads(urllib.request.urlopen(req, timeout=60).read())
    except urllib.error.HTTPError as e:
        sys.exit(f"Buffer API HTTP {e.code}: {e.read().decode()[:500]}")
    if res.get("errors"):
        sys.exit("Buffer API error:\n" + json.dumps(res["errors"], indent=2)
                 + "\nTip: run `python scripts/buffer.py introspect <TypeName>` to check field names.")
    return res["data"]


# ---------- setup ----------

def setup():
    orgs = gql("query { account { organizations { id name } } }")["account"]["organizations"]
    for org in orgs:
        print(f"\nOrganization: {org['name']}  (id {org['id']})")
        chans = gql("query($o: OrganizationId!) { channels(input: {organizationId: $o}) { id name service"
                    " metadata { ... on PinterestMetadata { boards { id serviceId name } } } } }",
                    {"o": org["id"]})["channels"]
        for c in chans:
            print(f"  {c['service']:<12} {c['name']:<30} channel id: {c['id']}")
            if c["service"] == "pinterest":
                boards = (c.get("metadata") or {}).get("boards") or []
                for b in boards:
                    print(f"      board: {b['name']:<30} id: {b['id']}  serviceId: {b['serviceId']}")
                if not boards:
                    print("      (no boards yet: create one on Pinterest, then reconnect or refresh the channel in Buffer)")
    print("\nCopy the facebook / instagram / pinterest channel ids into config.json -> buffer.channels,")
    print("and the board id into buffer.pinterest_board_id.")


def introspect(type_name):
    q = """query($n: String!) { __type(name: $n) { name kind
             fields { name type { name kind ofType { name kind ofType { name } } } }
             inputFields { name type { name kind ofType { name kind ofType { name } } } }
             enumValues { name } possibleTypes { name } } }"""
    print(json.dumps(gql(q, {"n": type_name})["__type"], indent=2))


# ---------- drafts ----------

def file_hash(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def raw_url(cfg, slug, filename):
    """Public GitHub link to an image. The ?v= tag changes whenever the image does,
    so Buffer never reuses a cached copy of an older version."""
    g = cfg["github"]
    local = ROOT / "posts" / slug / filename
    version = f"?v={file_hash(local)[:10]}" if local.exists() else ""
    return f"https://raw.githubusercontent.com/{g['owner']}/{g['repo']}/{g.get('branch', 'main')}/posts/{slug}/{filename}{version}"


def wait_until_public(url, local, tries=30):
    """Wait until GitHub serves exactly the local file (its CDN can lag a few minutes after a push)."""
    want = file_hash(local)
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            if hashlib.sha256(urllib.request.urlopen(req, timeout=20).read()).hexdigest() == want:
                return
        except urllib.error.HTTPError:
            pass
        time.sleep(10)
    sys.exit(f"GitHub isn't serving the current image yet: {url}\nDid you git push? Is the repo public?")


CREATE = """mutation($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess { post { id dueAt } }
    ... on MutationError { message }
  }
}"""


def tracked(url, platform, post, path):
    """Add UTM tags so Substack's stats show which platform (and which post) sent each reader."""
    tags = {"utm_source": platform, "utm_medium": "social", "utm_campaign": post["slug"],
            "utm_content": pathlib.Path(path).stem}          # post, post-2, post-3
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}{urllib.parse.urlencode(tags)}"


def build_inputs(post, cfg, path):
    ch = cfg["buffer"]["channels"]
    caps = post["captions"]
    square = raw_url(cfg, post["slug"], image_name(path, "instagram"))
    tall = raw_url(cfg, post["slug"], image_name(path, "pinterest"))
    def img(url):
        a = {"url": url}
        if post.get("alt_text"):
            a["metadata"] = {"altText": post["alt_text"]}
        return [{"image": a}]
    common = {"schedulingType": "automatic", "mode": "addToQueue", "saveToDraft": True, "needsApproval": False}
    return {
        "facebook": {**common, "channelId": ch["facebook"],
                     "text": caps["facebook"].replace(post["url"], tracked(post["url"], "facebook", post, path)),
                     "assets": img(square),
                     "metadata": {"facebook": {"type": "post"}}},
        "instagram": {**common, "channelId": ch["instagram"], "text": caps["instagram"],
                      "assets": img(square),
                      "metadata": {"instagram": {"type": "post", "shouldShareToFeed": True}}},
        "pinterest": {**common, "channelId": ch["pinterest"], "text": caps["pinterest"]["description"],
                      "assets": img(tall),
                      "metadata": {"pinterest": {"boardServiceId": cfg["buffer"]["pinterest_board_id"],
                                                 "title": caps["pinterest"]["title"],
                                                 "url": tracked(post["url"], "pinterest", post, path)}}},
    }


def wait_for_images(post, cfg, path):
    for p in ("instagram", "pinterest"):
        name = image_name(path, p)
        wait_until_public(raw_url(cfg, post["slug"], name), path.parent / name)


def draft(path, dry_run=False, only=None):
    path = pathlib.Path(path)
    post, cfg = load_json(path), config()
    inputs = build_inputs(post, cfg, path)
    if only:
        inputs = {k: v for k, v in inputs.items() if k in only}
    if dry_run:
        print(json.dumps(inputs, indent=2, ensure_ascii=False)); return

    wait_for_images(post, cfg, path)

    results = post.get("buffer", {})
    for platform, inp in inputs.items():
        if results.get(platform, {}).get("id"):
            print(f"{platform}: draft already exists ({results[platform]['id']}), skipping"); continue
        if not inp["channelId"]:
            print(f"{platform}: no channel id in config.json, skipping"); continue
        out = gql(CREATE, {"input": inp})["createPost"]
        if "post" in out:
            results[platform] = {"id": out["post"]["id"], "status": "draft"}
            print(f"{platform}: draft created ({out['post']['id']})")
        else:
            results[platform] = {"error": out.get("message")}
            print(f"{platform}: FAILED - {out.get('message')}")
    post["buffer"] = results
    save_json(path, post)
    if any("error" in r for r in results.values()):
        sys.exit(1)


EDIT = """mutation($input: EditPostInput!) {
  editPost(input: $input) {
    ... on PostActionSuccess { post { id } }
    ... on MutationError { message }
  }
}"""


def update(path):
    """Replace the caption text on drafts that already exist; still drafts afterward."""
    path = pathlib.Path(path)
    post, cfg = load_json(path), config()
    inputs = build_inputs(post, cfg, path)
    wait_for_images(post, cfg, path)
    failed = False
    for platform, existing in post.get("buffer", {}).items():
        if not existing.get("id"):
            continue
        # Buffer validates the whole post on edit, so resend type/metadata and the image with the text.
        inp = {"id": existing["id"], "saveToDraft": True,
               **{k: inputs[platform][k] for k in ("text", "metadata", "assets")}}
        out = gql(EDIT, {"input": inp})["editPost"]
        if "post" in out:
            print(f"{platform}: caption updated ({existing['id']})")
        else:
            failed = True
            print(f"{platform}: FAILED - {out.get('message')}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["setup"]: setup()
    elif a[:1] == ["introspect"] and len(a) == 2: introspect(a[1])
    elif a[:1] == ["draft"] and len(a) >= 2:
        only = a[a.index("--only") + 1].split(",") if "--only" in a else None
        draft(a[1], "--dry-run" in a, only)
    elif a[:1] == ["update"] and len(a) == 2: update(a[1])
    else: sys.exit(__doc__)
