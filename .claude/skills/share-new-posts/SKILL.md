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

## 2. Write the post package

Do this for each new post.

Read `posts/<slug>/source.json` in full. Also read `brand/voice-and-captions.md` and one or two packages in `examples/` so your output matches them.

**Pick the layout.** Run `.venv/bin/python scripts/log_post.py --recent` so you don't repeat the last layout used.

- `photo`: only if `header_image` is set. Prefer it when it is.
- `quote`: if there's a strong line of her own narration, under about 35 words.
- `print`: if there's a short line (15 words or fewer), especially about memory, photos, dates or places.
- `title`: when no single line stands alone, or the best lines are too sensitive to pull out.

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

- `label`: use "New essay" by default. Use "New episode" for a podcast post, or "Part II" and so on when the post is part of a series.
- `date_label`: only for `print`. Use it only when the post itself names the date or place. Never work one out yourself.

## 3. Validate

```
.venv/bin/python scripts/validate_post.py posts/<slug>/post.json
```

Fix every ERROR. Warnings are judgment calls.

## 4. Render and look

```
.venv/bin/python scripts/render_images.py posts/<slug>/post.json
```

Open both PNGs with the Read tool and check them:

- the text isn't cramped or tiny
- nothing is cut off
- there are no odd line breaks
- the layout looks like the `examples/` images

If an image looks wrong, fix it (a different quote or layout) and render again. Then run:

```
.venv/bin/python scripts/validate_post.py posts/<slug>/post.json --images
```

## 5. Publish the images (so Buffer can reach them)

```
git add posts/<slug>
git commit -m "Social drafts: <title>"
git push
```

`source.json` is gitignored on purpose, so it won't be committed.

## 6. Create the Buffer drafts

```
.venv/bin/python scripts/buffer.py draft posts/<slug>/post.json
```

It waits for the images to go live, then makes one draft per platform. If a platform fails, see "If the Buffer API rejects a field" in CLAUDE.md. Don't retry more than twice. Report the failure instead.

## 7. Log it

```
.venv/bin/python scripts/log_post.py posts/<slug>/post.json
git add data
git commit -m "Log: <slug>"
git push
```

## 8. Report to Sarah

Keep the report short and in plain language:

- which posts were drafted, and the layout and quote used for each
- that the drafts are waiting in Buffer for her approval
- any posts that were skipped, and why
- any errors

Show her the Instagram image for each post.
