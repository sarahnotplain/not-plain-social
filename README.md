# Not Plain: social sharing

When a new post goes up on [Not Plain](https://sarahnotplain.substack.com), Claude:

1. reads it
2. picks a line
3. makes branded images for Instagram, Facebook and Pinterest
4. writes a caption for each
5. saves them as **drafts in Buffer**

Sarah opens Buffer, checks the drafts, and approves them. Nothing posts without her.

```
Substack post ──► Claude Code ──► images + captions ──► GitHub (hosts the images)
                                                    └─► Buffer drafts ──► Sarah approves ──► FB / IG / Pinterest
```

**Tools:** Claude Code (desktop app), Buffer, and GitHub. Everything else is in this folder.

---

## One-time setup (about 30 minutes)

### 1. Buffer

- Connect three channels: the **Facebook Page**, the **Instagram account**, and **Pinterest**. Instagram must be a Business or Creator account, which Buffer walks you through. Buffer's free plan should cover three channels.
- Create a Pinterest board for the posts (for example "Not Plain").
- Go to **Settings → API** ([publish.buffer.com/settings/api](https://publish.buffer.com/settings/api)), create a key, and keep it handy.

### 2. Instagram bio

Put the Substack link in the Instagram bio. Captions say "link in bio" because Instagram doesn't allow links in posts.

### 3. GitHub

Create a **public** repository called `not-plain-social` and put this folder in it. The easiest way is GitHub Desktop, or ask Claude to do it.

The repository has to be public because Buffer can only pick up images from a public link.

**What stays off GitHub:** the full text of each post (`source.json`) and the API key (`.env`). Both stay on this computer only, so paid posts never leak.

### 4. Claude Code

Open this folder in the Claude desktop app (Code tab) and say:

> Set up this project: create the Python environment, install requirements and Chromium for Playwright, copy config.example.json to config.json with my GitHub username, and create .env from .env.example.

Claude runs these commands:

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium
```

Then open `.env` and paste the Buffer key after `BUFFER_API_KEY=`. Do this yourself rather than pasting the key into the chat.

### 5. Connect Buffer

Tell Claude:

> Run `scripts/buffer.py setup` and fill in the channel IDs and my Pinterest board ID in config.json.

### 6. First test

Tell Claude:

> /share-new-posts

The first run picks up posts published since `start_date` in `config.json`, which is set to Sep 26, 2026. That covers her three recent essays, which makes a good test. Check the drafts in Buffer, then delete or approve them.

### 7. Put it on a schedule

In the Claude desktop app, create a **scheduled task** for this folder:

- **Frequency:** daily, early morning
- **Prompt:** "Run /share-new-posts. If there are no new posts, stop."

The computer needs to be on (or wake up) for the task to run. If it's asleep, the task runs the next time the computer is awake.

---

## Day to day

- **Sarah:** write, publish on Substack, and later approve the drafts in Buffer.
- **To share a post right away:** open Claude and say "/share-new-posts".
- **To redo a post's images:** say "Redo the images for *\<title\>* using the title layout."
- **To skip a post:** say "Don't share *\<title\>*." Claude logs it as skipped.
- **Design changes:** describe what you'd like ("warmer accent color", "bigger quotes"). Claude edits the templates and shows you before and after using the examples.

## What's in here

| | |
|---|---|
| `CLAUDE.md` | The rules Claude follows (read this first) |
| `.claude/skills/share-new-posts/` | The step-by-step workflow |
| `brand/` | Visual style guide and caption voice guide, with examples |
| `examples/` | Approved sample posts: images and captions |
| `templates/` | The four image layouts (quote, title, print, photo) |
| `scripts/` | Feed checker, validator, image renderer, Buffer connection, log |
| `posts/` | One folder per shared post |
| `data/posted.json` | Record of what's been drafted or skipped |

## Safety checks built in

- Buffer only ever receives **drafts**.
- Quotes are checked **word for word** against the post before any image is made.
- Captions are checked against platform limits, hashtag count (5 max), no emoji, and whether the Facebook caption includes the link.
- Claude looks at every image before it goes to Buffer.
- Posts about sensitive material follow the care rules in `CLAUDE.md`.

## Known rough edges

- **Buffer's API is new.** The draft call is built from Buffer's docs but hasn't run against a live account yet. If a field name is off, Claude can look up the correct one (`buffer.py introspect`) and fix it. Expect one round of this on the first run.
- **Substack's feed sometimes rate-limits.** The checker retries automatically.
- **Paid posts:** the feed only includes the free preview, so quotes come from that part.

## Changelog

- 2026-09-28: first version. Four layouts, Buffer drafts, examples from three posts.
