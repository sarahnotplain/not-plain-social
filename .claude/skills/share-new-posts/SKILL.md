---
name: share-new-posts
description: Turn new Not Plain Substack posts into Buffer drafts (Facebook, Instagram, Pinterest) with branded images. Use when asked to share new posts, run the social workflow, or check Substack for new posts.
---

# Share new posts

Follow CLAUDE.md's hard rules throughout. Use `.venv/bin/python` for every script. If `.venv` doesn't exist, use `python3`.

## 0. Sync

Run `git pull` so the log is current.

## 1. Find new posts

```
.venv/bin/python scripts/check_feed.py
```

This prints a JSON list of new posts. For a specific post, use `--post <url>`. If the list is empty, reply "No new posts" and stop.

If more than 3 posts are new, only do the 3 most recent, and mention the rest in your report.

## 2. Write the post packages

Do this for each new post. Each article gets `drafts_per_article` packages (see `config.json`, normally 3), so Sarah has posts to spread out between articles:

| File | Label | Role |
|---|---|---|
| `post.json` | "New essay" | The announcement. Strongest hook. |
| `post-2.json` | "From the essay" | A second line from the post, in a different layout. |
| `post-3.json` | "From the essay" | A third line, or the title card if no third line stands alone. |

Rules for the set:
- Every package uses a **different quote** and, where possible, a **different layout**. Never repeat a quote within one article.
- Every quote still follows all of CLAUDE.md's care rules. If the post doesn't have enough suitable lines, make fewer packages and say so in the report. Don't lower the bar to reach 3.
- Paid posts: all quotes must come from the free preview. Often that means only 1 or 2 packages.
- Captions follow "What a caption is for" in `brand/voice-and-captions.md`: hook, a 2 to 4 sentence scene from the post, an open loop, then the call to action. Use different details from the essay in each package.
- Captions for packages 2 and 3 don't say "New". Use framing like "From *Title*, on Not Plain." and still point to the post (link in bio / the URL).
- Hashtags can vary between packages, still 5 at most.

Read `posts/<slug>/source.json` in full. Also read `brand/voice-and-captions.md` and one or two packages in `examples/` so your output matches them.

**Pick the layouts.** Sarah wants her feed to look dynamic, never cut and paste. Run `.venv/bin/python scripts/log_post.py --recent` and plan against it:

- The 3 packages of one article always use **3 different layouts**.
- Don't reuse a layout that appears in the most recent logged entry, unless there's no other fit.
- Mix light and dark: in the feed, avoid two cream cards (`quote`, `manuscript`, `artline`) back to back when a `print`, `photo`, `cover`, `poster` or `title` could go between them.

The layouts:

- `photo`: only if `header_image` is set. The art as a framed print with the title.
- `artline`: only if `header_image` is set. The art across the top with a line of hers below (30 words or fewer).
- `cover`: only if `header_image` is set. The art full-bleed fading to dark, with title, subtitle and "Not Plain" (like Substack's own share image).
- `poster`: only if `header_image` is set. The art dimmed full-bleed with the title large and centered in capitals. Best for strong, short titles. Skip it if the art is too busy for text.
- When a post has art, use two of the art layouts (`photo`, `artline`, `cover`, `poster`) across its 3 packages, and pick different ones from the last article that had art.
- `quote`: a strong line of her own narration, under about 35 words.
- `print`: a short line (15 words or fewer), especially about memory, photos, dates or places.
- `manuscript`: her line typed on a draft page with a lavender highlight (30 words or fewer). Good for lines about memory, noticing, or writing itself.
- `title`: when no single line stands alone, or the best lines are too sensitive to pull out.


Lavender is her signature color: `print` and `photo` always sit on lavender. The print's tilt varies automatically.

**Build the Instagram carousel.** Sarah considers carousels very important: Instagram needs to stop the scroll, and a single quote or title card doesn't. Facebook and Pinterest keep the single image from `layout`; Instagram gets the carousel instead.

- `post.json` always gets a carousel if the post has enough suitable lines (4 or more). `post-2.json` may get one too, in a different style. `post-3.json` stays a single image.
- Rotate the style so carousels don't feel templated. Check `log_post.py --recent` (it shows `layout+style`) and don't repeat the last style used:
  - `scene`: one moment told in steps. The hook sets up a question, each slide is a step, and the end is the turn. Example: "…there were only three places she could have gone" → the kitchen → the garage → the back door → "Their eyes met."
  - `details`: one vivid, concrete object or image from the essay per slide (the tree sprayed with fake snow, the honeysuckle trellis). Use `print` slides for some of them.
  - `panorama`: set `"panorama": true`. One painting pans across the middle slides. Only for wide art (landscapes).
  - `album`: for essays about photographs or memory. Mostly `print` slides, each one a picture or memory she describes.
- Slides: 4 to 7 is best (3 to 10 allowed). First is `hook`, last is `end`, and the middle ones are `line` or `print`. Vary the `bg` of `line` slides (`cream`, `lavender`, `black`) and give each a different `crop` of the art, so no two slides look the same.
- **Every slide's text is her exact words**, like any quote. If a line starts mid-sentence, begin it with "…" and keep her lowercase. If it stops mid-sentence, end it with "…". Never capitalize a fragment or add a period she didn't write.
- Labels, the hook's `list` and the `eyebrow` should be her wording too (the validator warns otherwise). Short: 1 to 4 words.
- The hook should make someone swipe. Use a question the essay sets up, a strong opening line, or a surprising detail. Don't just repeat the title.
- The end slide is the turn or an open loop, and never the resolution. It adds "Read the rest in *Title*. Link in bio." automatically ("Subscribe to read…" for paid posts).
- All care rules still apply to every slide: no names that aren't in the title/subtitle, and nothing about the violence, weapons or court.
- The Instagram caption for a carousel still follows the voice guide, but keep it shorter (the slides tell the scene). Open with a hook, and give 1 or 2 sentences of context, "Swipe through.", then the call to action and hashtags.

```json
"carousel": {
  "style": "scene",
  "slides": [
    {"kind": "hook", "eyebrow": "Five days before Christmas", "text": "…there were only three places she could have gone",
     "list": ["the kitchen", "the garage", "the back door"], "crop": "58% 30%"},
    {"kind": "line", "label": "The kitchen", "text": "…the kitchen was empty", "crop": "30% 22%", "bg": "cream"},
    {"kind": "line", "label": "The garage", "text": "…the garage door was closed like it always was", "crop": "50% 70%", "bg": "lavender"},
    {"kind": "print", "label": "The back door", "text": "She followed the stone path and when she reached the wooden trellis, dripping with honeysuckle, she heard it…"},
    {"kind": "end", "text": "Their eyes met.", "crop": "52% 32%"}
  ]
}
```

Slide options: `crop` ("x% y%", which part of the art to show) and `zoom` (bigger = closer). Set `"art": false` to leave the art off a slide. `number` (defaults to its position) and `alt` (defaults to the slide text) are also available. Without a `header_image`, the slides render text-only. Render and **look at every slide** before pushing: check the crops for awkward framing and make sure no text is cut off.

**Pick the quote.** Copy it exactly from `source.json`. Choose a line that makes someone want to read on without needing context, and that follows the care rules.

Write `posts/<slug>/post.json`:

```json
{
  "slug": "…", "url": "…", "title": "…", "subtitle": "…",
  "header_image": null,
  "layout": "quote",
  "quote": "exact words from the post",
  "label": "New essay",
  "date_label": "",
  "alt_text": "Describe the image for screen readers: layout, the quote or title text.",
  "captions": {
    "instagram": "…",
    "facebook": "… must include the post URL …",
    "pinterest": { "title": "…", "description": "…" }
  }
}
```

- `label`: use "New essay" for `post.json` and "From the essay" for the other packages. Use "New episode" for a podcast post, or "Part II" and so on when the post is part of a series.
- `date_label`: only for `print`. Use it only when the post itself names the date or place. Never work one out yourself.

## 3. Validate

Run this for each package (`post.json`, `post-2.json`, `post-3.json`):

```
.venv/bin/python scripts/validate_post.py posts/<slug>/post.json
```

Fix every ERROR. Warnings are judgment calls.

## 4. Render and look

For each package:

```
.venv/bin/python scripts/render_images.py posts/<slug>/post.json
```

Variants write `instagram-2.png`, `pinterest-2.png` and so on. Open both PNGs with the Read tool and check them:

- the text isn't cramped or tiny
- nothing is cut off
- there are no odd line breaks
- the layout looks like the `examples/` images

If an image looks wrong, fix it (a different quote or layout) and render again. Then run:

```
.venv/bin/python scripts/validate_post.py posts/<slug>/post.json --images
```

**Reel:** for the package with a carousel, also make the video version:

```
.venv/bin/python scripts/render_reel.py posts/<slug>/post.json
```

It writes `private/reels/<slug>(-N).mp4` (not committed). Save a Reel caption next to it as `private/reels/<slug>(-N).txt`: the Instagram caption without "Swipe through." Sarah posts Reels herself from her phone, because she adds a trending sound in the app. If `private/reels/motion/<slug>.mp4` exists (an animated version of the art, see `private/growth/higgsfield.md`), the Reel uses it automatically.

## 5. Publish the images (so Buffer can reach them)

```
git add posts/<slug>
git commit -m "Social drafts: <title>"
git push
```

`source.json` is gitignored on purpose, so it won't be committed.

## 6. Create the Buffer drafts

For each package:

```
.venv/bin/python scripts/buffer.py draft posts/<slug>/post.json
```

It waits for the images to go live, then makes one draft per platform. If a platform fails, see "If the Buffer API rejects a field" in CLAUDE.md. Don't retry more than twice. Report the failure instead.

## 7. Log it

```
.venv/bin/python scripts/log_post.py posts/<slug>/post.json posts/<slug>/post-2.json posts/<slug>/post-3.json
git add data
git commit -m "Log: <slug>"
git push
```

## 7b. Substack Notes (at most one draft per day)

After the articles, do the same for Notes:

```
.venv/bin/python scripts/check_notes.py
```

It lists her recent Notes that haven't been drafted or skipped. Pick **at most `notes.per_day` (1)** to draft today.

- **Draft:** notes that stand on their own as writing: lines about memory, grief, family, place, or what Not Plain is and why she writes it (framing notes that name the murder are allowed; she approves everything in Buffer).
- **Skip and log** (`log_post.py --skip note-<id> "reason"`): everyday chatter, Substack/platform talk, questions to readers, jokes, anything that needs other context to make sense, and anything the care rules in CLAUDE.md rule out.
- **Leave for another day:** good notes you didn't pick today. Don't log them; they stay in the pool for `notes.lookback_days`.
- **Exact words.** The quote is copied from the note like any other quote. If a note contains emoji, use only whole sentences without them. If a note has a typo, don't fix it: leave that note for another day and mention it in the report so Sarah can decide.

Write `posts/note-<id>/post.json`:

- `layout`: `"note"`, `label`: `"From my notes"`, `title`: `"Notes from Not Plain"`.
- `url`: if `source.json` has `shares_post`, that essay's URL. Otherwise the Substack home page (`substack_url` in config).
- Captions follow "Substack Notes" in `brand/voice-and-captions.md`.

Then validate, render, look, push, draft and log it exactly like an article package (step 3 onward), with just the one file.

## 8. Report to Sarah

Keep the report short and in plain language:

- which posts were drafted, and for each package the layout and quote used
- which note was drafted (if any), which were skipped and why, and any good ones left for another day
- that the drafts are waiting in Buffer for her approval
- any posts that were skipped, and why
- any errors

Show her the Instagram image for each package, and tell her which Reel is ready in `private/reels/`.
