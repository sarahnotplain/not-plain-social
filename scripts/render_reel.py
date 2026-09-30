"""Turn a rendered carousel into a 9:16 Reel (MP4) for Instagram, TikTok or Facebook.

    python scripts/render_reel.py posts/<slug>/post-4.json

Each slide (rendered again without "Swipe" or slide counters) sits full width
over a blurred, darkened copy of the post's art, zooms in slowly, and crossfades
into the next. It stays up long enough to read (longer for longer
lines). The audio track is silent on purpose: add a trending sound in the app.

Motion background (optional): put a short clip that animates the post's art
(for example from Higgsfield's image-to-video) at private/reels/motion/<slug>.mp4
and it plays behind the slides, looped, in place of the blurred still. Only
animate the art itself (light, leaves, a slow camera move); never generate people
or scenes from the story.
Render the carousel first (render_images.py). Output goes to private/reels/,
which isn't committed, so the public repo doesn't fill up with video.
"""
import pathlib
import subprocess
import sys

import imageio_ffmpeg

from common import load_json
from render_images import reel_slides

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "private" / "reels"
W, H, SLIDE_H, FPS, FADE = 1080, 1920, 1350, 30, 0.6


def seconds(slide):
    """Reading time: about 3.5 words a second, plus a beat to look at the art."""
    words = len(slide.get("text", "").split())
    base = 3.0 if slide["kind"] == "end" else 1.8
    return round(min(max(base + words / 3.5, 3.0), 8.0), 2)


def render(path):
    path = pathlib.Path(path)
    post = load_json(path)
    car = post.get("carousel")
    if not car:
        sys.exit(f"{path} has no carousel to turn into a Reel")
    name = f"{post['slug']}{path.stem.replace('post', '')}"
    slides = reel_slides(path, OUT_DIR / ".frames" / name)
    art = path.parent / "header.jpg"
    motion = OUT_DIR / "motion" / f"{post['slug']}.mp4"
    background = art if art.exists() else slides[0]

    durs = [seconds(s) for s in car["slides"]]
    total = sum(durs) - FADE * (len(durs) - 1)
    n = len(durs)
    args = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error"]
    for img, d in zip(slides, durs):
        args += ["-loop", "1", "-framerate", str(FPS), "-t", str(d), "-i", str(img)]
    if motion.exists():
        args += ["-stream_loop", "-1", "-t", str(total), "-i", str(motion)]
        blur = "gblur=sigma=6,eq=brightness=-0.28:saturation=0.85"   # light blur so the motion shows
    else:
        args += ["-loop", "1", "-framerate", str(FPS), "-t", str(total), "-i", str(background)]
        blur = "gblur=sigma=40,eq=brightness=-0.22:saturation=0.8"
    args += ["-f", "lavfi", "-t", str(total), "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]

    parts = []
    for i, d in enumerate(durs):
        frames = int(d * FPS)
        parts.append(
            # Upscale before zoompan so the slow zoom doesn't judder.
            f"[{i}:v]scale={W * 2}:{SLIDE_H * 2},"
            f"zoompan=z='1+0.035*on/{frames}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2'"
            f":d=1:s={W}x{SLIDE_H}:fps={FPS},setsar=1,format=yuv420p[v{i}]")
    last, offset = "v0", 0.0
    for i in range(1, len(durs)):
        offset += durs[i - 1] - FADE
        parts.append(f"[{last}][v{i}]xfade=transition=fade:duration={FADE}:offset={offset:.2f}[x{i}]")
        last = f"x{i}"

    parts.append(f"[{n}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                 f"fps={FPS},{blur},format=yuv420p[bg];"
                 f"[bg][{last}]overlay=0:{(H - SLIDE_H) // 2}:shortest=1[out]")

    out = OUT_DIR / f"{name}.mp4"
    args += ["-filter_complex", ";".join(parts), "-map", "[out]", "-map", f"{n + 1}:a",
             "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(out)]
    subprocess.run(args, check=True)
    print(f"wrote {out.relative_to(ROOT)} ({total:.0f}s{', motion background' if motion.exists() else ''})")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for p in sys.argv[1:]:
        render(p)
