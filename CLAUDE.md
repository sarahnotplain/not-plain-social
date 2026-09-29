# Not Plain: social sharing

This repo turns new posts from Sarah's Substack, **Not Plain** (sarahnotplain.substack.com), into draft social posts for Facebook, Instagram and Pinterest. Each draft includes a branded image. Sarah approves every draft in Buffer before anything goes live.

**About the writing:** Not Plain is narrative nonfiction. Sarah is writing a memoir in real time about her father's murder and her mother's conviction. Everything we post about it has to read as literary memoir, never as true-crime content or clickbait.

## The workflow

Run the `share-new-posts` skill (`/share-new-posts`). It walks through every step. In short:

check feed → write post.json, post-2.json, post-3.json (3 packages per article: layout, quote, captions) → validate → render images → look at them → git push → Buffer drafts → log → then one Substack Note (check_notes.py, at most 1 draft a day) → report

## Hard rules

1. **Drafts only.** Never publish, schedule for a time, or use `shareNow`. `scripts/buffer.py` always uses `saveToDraft: true`, so don't bypass it.
2. **Quotes are her exact words.** Copy them character for character from `source.json`. Never paraphrase, trim the middle out of a sentence, or "tidy up" a quote. `validate_post.py` enforces this.
3. **Only say what the post says.** Captions summarize and point to the post. Don't add facts, names, dates, feelings or details that aren't in the text.
4. **Handle the subject with care:**
   - No sensational framing. Avoid words like "shocking", "chilling", "twisted", "you won't believe", "the truth about".
   - Don't lead with violence. Don't pick quotes that describe the killing, weapons, bodies or courtroom details.
   - Don't name people who aren't already named in the post's title or subtitle.
   - Prefer lines from her own narration about memory, family, grief, place and time. Avoid lines of other people's dialogue.
5. **No emoji. At most 5 hashtags.** Don't use em dashes or AI filler phrasing (see `brand/voice-and-captions.md`).
6. **Paid posts:** if `looks_paywalled` is true, only quote from the free preview text and say "subscribe to read" rather than "read".
7. **If unsure, skip and say so.** For example, when a post is a podcast episode, an announcement, or too sensitive to excerpt, log it with `log_post.py --skip` and a reason. Don't guess.

## Where things live

| Path | What |
|---|---|
| `brand/style-guide.md` | Colors, fonts, the 4 layouts and when to use each |
| `brand/voice-and-captions.md` | Caption rules per platform + worked examples |
| `examples/` | Approved example packages (post.json + images). Match these. |
| `templates/*.html`, `templates/base.css` | The layouts (`note.html` is only for Substack Notes). Edit these when Sarah asks for design changes. |
| `scripts/` | check_feed, check_notes, validate_post, render_images, buffer, log_post |
| `posts/<slug>/` | One folder per shared post: `source.json` (local only), then per package `post.json` / `post-2.json` / `post-3.json` with matching `instagram(-N).png`, `pinterest(-N).png` |
| `data/posted.json` | Log of what's been drafted/skipped. Never re-draft a logged post unless asked. |
| `config.json` | Substack URL, GitHub repo, Buffer channel + board IDs |
| `.env` | `BUFFER_API_KEY` (never commit, never print) |

## Design changes

When Sarah asks for design changes ("make the quote bigger", "try a green accent"):

1. Edit `templates/`, not the scripts.
2. Re-render one of the `examples/` packages, look at the result, and show her before and after.
3. Once she approves, update `brand/style-guide.md` to match.

## If the Buffer API rejects a field

The Buffer API is GraphQL and still new, so field names may shift. Run `python scripts/buffer.py introspect <TypeName>` (for example `CreatePostInput`, `PostInputMetaData`, `PinterestPostMetadataInput`), fix `build_inputs()` in `scripts/buffer.py`, and note the change in the README changelog.
