"""A Reel built on moving art: an animated version of the essay's image fills the
screen, and a few of Sarah's lines fade in and out over it, then an end card.

    python scripts/render_motion_reel.py posts/<slug>/post-4.json

Needs "reel" in the post file:

    "reel": {"motion": "private/reels/motion/<name>.mp4",
             "lines": ["exact words", "exact words", ...]}

The motion clip comes from Higgsfield (image to video) and is looped forward
then backward so it never jumps. Every line must be her exact words from
source.json (same check as the validator). Output: private/reels/<slug>-motion.mp4
and a caption .txt next to it. The audio is silent: add a sound in the app.
"""
import html
import pathlib
import subprocess
import sys
import tempfile

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

from common import load_json
from render_images import data_uri, font_css
from validate_post import norm

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "private" / "reels"
W, H, FPS, FADE = 1080, 1920, 30, 0.7
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

# Text sits in the lower middle: clear of the top bar, and of Instagram's caption
# and buttons at the bottom and right.
LINE_HTML = """<div style="position:absolute; left:90px; right:150px; top:1170px; height:420px;
  display:flex; align-items:flex-start;">
  <div style="font-family:Garamond; font-style:italic; font-weight:500; font-size:{size}px;
    line-height:1.18; color:#F4EFE8; text-shadow:0 2px 24px rgba(0,0,0,.65), 0 1px 3px rgba(0,0,0,.5);">{text}</div>
</div>"""

END_HTML = """<div style="position:absolute; left:90px; right:150px; top:1100px;">
  <div style="font-family:'Plex Mono'; font-size:26px; letter-spacing:.16em; text-transform:uppercase;
    color:#D9CFE6; text-shadow:0 1px 12px rgba(0,0,0,.6);">From Not Plain</div>
  <div style="margin-top:26px; font-family:Garamond; font-weight:500; font-size:78px; line-height:1.08;
    color:#F4EFE8; text-shadow:0 2px 24px rgba(0,0,0,.65);">{title}</div>
  <div style="margin-top:34px; font-family:Garamond; font-size:40px; color:#F4EFE8;
    text-shadow:0 1px 14px rgba(0,0,0,.6);">{cta}</div>
  <img src="{logo}" style="margin-top:44px; height:74px; border-radius:10px;">
</div>"""

SHADE_HTML = """<div style="position:absolute; inset:0;
  background:linear-gradient(to bottom, rgba(0,0,0,0) 38%, rgba(0,0,0,.50) 62%, rgba(0,0,0,.62) 100%);"></div>"""


def seconds(text):
    """Reading time: about 3.2 words a second plus a beat, 3 to 7 seconds."""
    return round(min(max(1.6 + len(text.split()) / 3.2, 3.0), 7.0), 2)


def check_lines(lines, source_text):
    bad = [l for l in lines if norm(l.strip("…").strip(".").strip()) not in norm(source_text)]
    if bad:
        sys.exit("These lines aren't her exact words from source.json:\n  " + "\n  ".join(bad))


def overlays(post, lines, tmp):
    """Transparent 1080x1920 PNGs: the shade, one per line, and the end card."""
    logo = data_uri(ROOT / "assets" / "logo.png")
    title = post["title"]
    cta = ("Subscribe to read it on Not Plain." if post.get("looks_paywalled")
           else "Read the rest on Not Plain.") + " Link in bio."
    pages = [("shade", SHADE_HTML)]
    for i, line in enumerate(lines):
        size = 76 if len(line) < 70 else 66 if len(line) < 120 else 58
        pages.append((f"line{i}", LINE_HTML.format(size=size, text=html.escape(line))))
    pages.append(("end", END_HTML.format(title=html.escape(title), cta=html.escape(cta), logo=logo)))
    paths = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for name, body in pages:
            p = b.new_page(viewport={"width": W, "height": H})
            p.set_content(f"<!doctype html><html><head><meta charset='utf-8'><style>{font_css()}"
                          f"html,body{{margin:0;background:transparent}}</style></head><body>{body}</body></html>")
            p.evaluate("document.fonts.ready")
            paths[name] = tmp / f"{name}.png"
            p.screenshot(path=str(paths[name]), omit_background=True)
            p.close()
        b.close()
    return paths


def pingpong(motion, tmp, bounce=True):
    """Cropped to 9:16. bounce=True plays forward then backward so the loop never jumps;
    use "bounce": false for clips made with the same start and end frame (they loop already)."""
    out = tmp / "pingpong.mp4"
    tail = "split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1[v]" if bounce else "null[v]"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(motion), "-filter_complex",
                    f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},"
                    f"setsar=1,{tail}",
                    "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(out)],
                   check=True)
    return out


def render(path):
    path = pathlib.Path(path)
    post = load_json(path)
    reel = post.get("reel") or sys.exit(f"{path} has no 'reel' section")
    motion = ROOT / reel["motion"]
    if not motion.exists():
        sys.exit(f"Motion clip not found: {motion}")
    lines = reel["lines"]
    check_lines(lines, load_json(path.parent / "source.json", {}).get("text", ""))

    # Timeline: each line fades in, holds, fades out; then the end card holds.
    starts, t = [], 0.4
    for line in lines:
        starts.append((t, t + seconds(line)))
        t += seconds(line) + 0.2
    end_start, total = t, t + 4.0

    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d)
        png = overlays(post, lines, tmp)
        bg = pingpong(motion, tmp, reel.get("bounce", True))
        args = [FFMPEG, "-y", "-loglevel", "error", "-stream_loop", "-1", "-t", f"{total:.2f}", "-i", str(bg)]
        names = ["shade"] + [f"line{i}" for i in range(len(lines))] + ["end"]
        for n in names:
            args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{total:.2f}", "-i", str(png[n])]
        args += ["-f", "lavfi", "-t", f"{total:.2f}", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]

        f = [f"[0:v]fps={FPS},format=yuv420p[bg0]"]
        timing = [None] + starts + [(end_start, None)]
        last = "bg0"
        for k, (n, tm) in enumerate(zip(names, timing), start=1):
            chain = f"[{k}:v]format=rgba"
            if tm:
                a, b = tm
                chain += f",fade=t=in:st={a:.2f}:d={FADE}:alpha=1"
                if b:
                    chain += f",fade=t=out:st={b - FADE:.2f}:d={FADE}:alpha=1"
            f.append(f"{chain}[o{k}]")
            f.append(f"[{last}][o{k}]overlay=0:0:format=auto[bg{k}]")
            last = f"bg{k}"
        f.append(f"[{last}]format=yuv420p[out]")

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out = OUT_DIR / f"{post['slug']}-motion.mp4"
        args += ["-filter_complex", ";".join(f), "-map", "[out]", "-map", f"{len(names) + 1}:a",
                 "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                 "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(out)]
        subprocess.run(args, check=True)

    caption = post["captions"]["instagram"].replace("Swipe through, then start reading at the link in bio.",
                                                     "Start reading at the link in bio.")
    caption = caption.replace("Swipe through.\n\n", "").replace("Swipe through. ", "")
    out.with_suffix(".txt").write_text(caption)
    print(f"wrote {out.relative_to(ROOT)} ({total:.0f}s) and its caption")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for p in sys.argv[1:]:
        render(p)
