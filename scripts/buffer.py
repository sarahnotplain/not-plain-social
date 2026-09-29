"""Talk to Buffer's API (https://developers.buffer.com).

Usage:
    python scripts/buffer.py setup                        # list channel IDs (+ Pinterest boards) for config.json
    python scripts/buffer.py introspect CreatePostInput   # show a GraphQL type's fields (for fixing field names)
    python scripts/buffer.py draft posts/<slug>/post.json [--dry-run]

`draft` creates one DRAFT per platform (Facebook, Instagram, Pinterest). Nothing is
published: Sarah approves drafts in Buffer. Images must already be pushed to GitHub
so their raw URLs are public (Buffer has no upload endpoint).

Needs BUFFER_API_KEY in the environment or in a .env file at the repo root
(Buffer -> Settings -> API: https://publish.buffer.com/settings/api).
"""
import json, os, pathlib, sys, time, urllib.request
from common import ROOT, config, load_json, save_json

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

def raw_url(cfg, slug, filename):
    g = cfg["github"]
    return f"https://raw.githubusercontent.com/{g['owner']}/{g['repo']}/{g.get('branch', 'main')}/posts/{slug}/{filename}"


def wait_until_public(url, tries=12):
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
            if urllib.request.urlopen(req, timeout=20).status == 200:
                return
        except urllib.error.HTTPError:
            pass
        time.sleep(5)
    sys.exit(f"Image isn't publicly reachable yet: {url}\nDid you git push? Is the repo public?")


CREATE = """mutation($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess { post { id dueAt } }
    ... on MutationError { message }
  }
}"""


def build_inputs(post, cfg):
    ch = cfg["buffer"]["channels"]
    caps = post["captions"]
    square = raw_url(cfg, post["slug"], "instagram.png")
    tall = raw_url(cfg, post["slug"], "pinterest.png")
    def img(url):
        a = {"url": url}
        if post.get("alt_text"):
            a["metadata"] = {"altText": post["alt_text"]}
        return [{"image": a}]
    common = {"schedulingType": "automatic", "mode": "addToQueue", "saveToDraft": True, "needsApproval": False}
    return {
        "facebook": {**common, "channelId": ch["facebook"], "text": caps["facebook"],
                     "assets": img(square),
                     "metadata": {"facebook": {"type": "post"}}},
        "instagram": {**common, "channelId": ch["instagram"], "text": caps["instagram"],
                      "assets": img(square),
                      "metadata": {"instagram": {"type": "post", "shouldShareToFeed": True}}},
        "pinterest": {**common, "channelId": ch["pinterest"], "text": caps["pinterest"]["description"],
                      "assets": img(tall),
                      "metadata": {"pinterest": {"boardServiceId": cfg["buffer"]["pinterest_board_id"],
                                                 "title": caps["pinterest"]["title"], "url": post["url"]}}},
    }


def draft(path, dry_run=False):
    path = pathlib.Path(path)
    post, cfg = load_json(path), config()
    inputs = build_inputs(post, cfg)
    if dry_run:
        print(json.dumps(inputs, indent=2, ensure_ascii=False)); return

    for url in {raw_url(cfg, post["slug"], f) for f in ("instagram.png", "pinterest.png")}:
        wait_until_public(url)

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


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["setup"]: setup()
    elif a[:1] == ["introspect"] and len(a) == 2: introspect(a[1])
    elif a[:1] == ["draft"] and len(a) >= 2: draft(a[1], "--dry-run" in a)
    else: sys.exit(__doc__)
