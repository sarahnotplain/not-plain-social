# Not Plain: visual style

**Mood:** a quiet literary memoir, like a book cover or a photo pulled from a family album. It shouldn't look like a true-crime podcast graphic. Use lots of empty space, one idea per image, and no stock photos or clip art.

## Colors (defined in `templates/base.css`)

| Name | Hex | Use |
|---|---|---|
| cream | `#F5F0E8` | Main background (matches her Substack) |
| paper | `#E9E2D6` | Background behind the "print" and photo layouts |
| ink | `#1F1B17` | Text on cream; background of the title card |
| rust | `#8A4B33` | Small labels and accent rules only |
| muted | `#6B6259` | Secondary text |
| sand | `#C9A88F` | Labels on the dark title card |

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
| `quote` | Cream, big italic quote, "from *Title*" | There's a strong line of her own narration (35 words or fewer) |
| `title` | Dark, big title + italic subtitle, thin frame | The title and subtitle are the hook, or no line should be pulled out |
| `print` | A tilted 5x7 print holding one short line | A short line (15 words or fewer), especially about memory, photos, dates or places |
| `photo` | The post's header image as a bordered print, title below | The post has a header image |
| `note` | Cream, upright serif text beside a thin rust rule, like a notebook page | Substack Notes only |

Rotate the layouts so her feed doesn't repeat the same look twice in a row.

## Examples

See `examples/`. These are the approved look.

## Open questions for Sarah (update this file as she answers)

- Does she want her face, a logo or a signature mark on the images?
- Should any hashtags lean toward true crime (such as #truecrime and #truecrimecommunity), or stay literary only?
- Should podcast episodes get their own label or color?
