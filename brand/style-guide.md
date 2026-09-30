# Not Plain: visual style

**Mood:** a quiet literary memoir, like a book cover or a photo pulled from a family album. It shouldn't look like a true-crime podcast graphic. Use lots of empty space, one idea per image, and no stock photos or clip art.

## Brand source

Everything matches her Substack: the torn-kraft "Not Plain" logo on black (`assets/logo.png`, the same image Substack uses), the cream page background, and the lavender of her Subscribe buttons. Every image carries the logo.

## Colors (defined in `templates/base.css`)

| Name | Hex | Use |
|---|---|---|
| cream | `#F5F0E8` | Main background of quote and note cards (her Substack background) |
| lavender | `#8882A1` | Background behind the "print" and photo layouts (her Substack buttons) |
| accent | `#6B6687` | Deeper lavender for small labels and rules on cream |
| black | `#000000` | Title card background (matches the logo's black) |
| kraft | `#B59C74` | The cardboard in her logo; labels on black |
| ink | `#1F1B17` | Text on cream |
| muted | `#6E6A66` | Secondary text on cream |

No other accent colors (the old rust is gone).

## Type

- **EB Garamond:** everything that's meant to be read, meaning quotes, titles and subtitles. Italic for quotes and subtitles.
- **IBM Plex Mono**, uppercase and letter-spaced: small labels only ("NEW ESSAY", the site address, dates). It reads like a typewriter or a case file. Keep it small.

## Sizes

| File | Size | Used for |
|---|---|---|
| `instagram.png` | 1080 × 1350 (4:5) | Instagram and Facebook |
| `pinterest.png` | 1000 × 1500 (2:3) | Pinterest |

## Layouts

| Layout | Looks like | Use when |
|---|---|---|
| `quote` | Cream, big italic quote, "from *Title*", logo bottom left | There's a strong line of her own narration (35 words or fewer) |
| `title` | Black, logo top left, big title + italic subtitle | The title and subtitle are the hook, or no line should be pulled out |
| `print` | A tilted cream 5x7 print on lavender, logo + title below | A short line (15 words or fewer), especially about memory, photos, dates or places |
| `photo` | The post's photo as a bordered print on lavender, title below | The post has a header image |
| `artline` | The post's art across the top, a lavender rule, her line in italic on cream below | The post has a header image and a line of 30 words or fewer |
| `cover` | The post's art full-bleed, fading to near-black at the bottom; serif title, subtitle, italic "Not Plain", logo bottom right | The post has a header image (inspired by Substack's share image) |
| `poster` | The post's art dimmed and softly blurred, title large and centered in serif capitals, a short kraft rule | The post has a header image and a short, strong title |
| `manuscript` | Her line typed in mono on a ruled draft page, marked with lavender highlighter | Lines about memory, noticing or writing, 30 words or fewer |
| `note` | Cream, upright serif text beside a thin lavender rule, logo bottom left | Substack Notes only |

Sarah wants the feed to look dynamic, not cut and paste. Rotate the layouts so the same look never appears twice in a row, and mix light cards with dark or colored ones.

## Lavender stays

`print` and `photo` always sit on lavender, her signature color. (Black and kraft stages were tried and dropped on 2026-09-29.) The print's tilt varies per post (4 angles, chosen automatically), so no two prints sit the same way.

A 3x3 mock of the full mix is in `private/variety-preview/feed-mock.jpg` (approved 2026-09-29).

## Instagram carousels

Instagram gets a carousel (`templates/carousel/`); Facebook and Pinterest get the single image. Slide kinds:

| Kind | Looks like |
|---|---|
| `hook` | Black, big serif hook on the left, a tall close crop of the art on the right, an optional numbered list in mono, "Swipe →" in kraft |
| `line` | Art strip on top (a different crop each slide, or panning across one painting), big number, mono label, her line in italic; cream, lavender or black |
| `print` | Her line on a tilted cream print on lavender, like flipping through an album |
| `end` | The art fading into black, her last line big in italic, "Read the rest in *Title*. Link in bio." and the logo |

Styles rotate: `scene`, `details`, `panorama`, `album` (see the share-new-posts skill). Approved direction 2026-09-29; test renders are in `private/carousel-test/`.

## Examples

See `examples/`. These are the approved look.

## Open questions for Sarah (update this file as she answers)

- Does she want her face, a logo or a signature mark on the images?
- Should any hashtags lean toward true crime (such as #truecrime and #truecrimecommunity), or stay literary only?
- Should podcast episodes get their own label or color?
