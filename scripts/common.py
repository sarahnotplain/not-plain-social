"""Shared helpers: paths, config, and loading/saving post packages."""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
POSTS = ROOT / "posts"
DATA = ROOT / "data"
LOG = DATA / "posted.json"

SIZES = {                       # file name -> (width, height)
    "instagram": (1080, 1350),  # 4:5, also used for Facebook
    "pinterest": (1000, 1500),  # 2:3
}
LAYOUTS = ("quote", "title", "print", "photo")


def config():
    p = ROOT / "config.json"
    if not p.exists():
        sys.exit("config.json is missing. Copy config.example.json to config.json and fill it in (see README).")
    return json.loads(p.read_text())


def load_json(p, default=None):
    p = pathlib.Path(p)
    return json.loads(p.read_text()) if p.exists() else default


def save_json(p, obj):
    p = pathlib.Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def slug_from_url(url):
    m = re.search(r"/p/([^/?#]+)", url)
    return m.group(1) if m else re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-")


def post_dir(slug):
    return POSTS / slug


def variant_suffix(post_path):
    """post.json -> "", post-2.json -> "-2". Each variant's images carry the same suffix."""
    m = re.fullmatch(r"post(-\d+)?\.json", pathlib.Path(post_path).name)
    return (m.group(1) or "") if m else ""


def image_name(post_path, platform):
    return f"{platform}{variant_suffix(post_path)}.png"


def log():
    return load_json(LOG, {"posts": []})
