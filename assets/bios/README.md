# Group member bio files

Each person on **The Group** page (`thegroup.html`) comes from one `.txt` file in this folder.
Edit the files, then run the builder from the website folder:

```
python build_team.py
```

It prints what it did. If a file has a mistake it tells you exactly what and where, and **changes nothing** until it's fixed.

---

## Add a new member

1. Put their photo in `assets/headshots/` — any size, JPG or PNG. A web-sized copy is made automatically.
2. Copy `template/_TEMPLATE.txt` into this folder, rename it (e.g. `abc_bio.txt` — the filename itself doesn't matter), and fill it in.
3. Run `python build_team.py`.

## Update someone

Edit their file, run `python build_team.py`.

## Remove someone

Delete their file, run `python build_team.py`. (Their photos can stay; unused photos don't appear.)

---

## Fields

One field per line, as `Field: value`. Order and spacing don't matter. Leave a value blank if it doesn't apply.

| Field | Needed? | What to write | Where it shows |
|---|---|---|---|
| `Name` | **yes** | `Jake Sirlin` | card, panel |
| `Role` | **yes** | one of the roles below — spelled exactly | which section they appear in |
| `Title` | PI only | `Assistant Professor of Chemistry` | PI card (members: replaces the role in their panel) |
| `Joined` | recommended | `August 31, 2026` or `March 2026` | not displayed — sets the order within a section |
| `Headshot` | **yes** | filename in `assets/headshots/`, e.g. `2026_JTS_Postdoc_Headshot.JPG` | card, panel |
| `Headshot Focus` | optional | `60% 50%` — re-aims the 4:5 crop when the subject is off-centre | card, panel |
| `Card Shift` | optional | `5%` — slides the card's photo up so the face sits higher above the caption (1–15%) | card |
| `Email` | optional | `jsirlin [at] uvm.edu` | panel (PI: under title) |
| `Fellowship` | optional | `NSF Graduate Research Fellow` | card, panel |
| `Education` | optional, **repeatable** | `Ph.D. University of North Carolina at Chapel Hill (Alex Miller)` | card without advisor; panel with advisor |
| `Class Year` | undergrads | `2029` | card and panel as "Class of 2029" |
| `CV` | optional | path inside `assets/`, e.g. `SKDorn_ChemistryCV_11.44_UVM.pdf` | "View CV" link |
| `ORCID` | optional | full URL | icon link |
| `LinkedIn` | optional | full URL | icon link |
| `Google Scholar` | optional | full URL | icon link |
| `Bio` | **yes** | goes **last**; everything after `Bio:` is the bio | panel (PI: below the card) |

**Bio** can be several paragraphs — separate them with a blank line.

**Education** — one line per degree, with the advisor in parentheses at the end:

```
Education:      Ph.D. University of North Carolina at Chapel Hill (Alex Miller)
Education:      BS University of Miami (Carl Hoff)
```

- Postdocs: Ph.D. line first, then the predoctoral degree.
- Graduate students: their predoctoral degree.
- Undergraduates: leave `Education` blank; use `Class Year`.

**Email** — write `[at]`, not `@`. These files are publicly reachable on the site, so a plain address here could be harvested. (If you do type `@`, the page still shows `[at]` and the builder reminds you.)

## Roles and sections

| `Role:` | Section on the page |
|---|---|
| `Principal Investigator` | the large card at the top (only one allowed) |
| `Postdoctoral Researcher` | Postdoctoral Researchers |
| `Graduate Student` | Graduate Students |
| `Undergraduate Researcher` | Undergraduate Students |
| `Lab Mascot` | Lab Mascots |

Within a section, people are listed **newest first** by `Joined`. Anyone without a `Joined` date goes after everyone who has one; people who joined on the same date are listed alphabetically by last name. A section with nobody in it shows a short placeholder note.

`Joined` accepts `August 31, 2026`, `Aug 31 2026`, `March 2026`, `2026-08-31`, `8/31/2026`, or just `2026`. A month without a day counts as the start of that month. Seasons (`Summer 2026`) aren't understood — the builder will tell you.

## Headshots

- Portrait orientation works best — cards are cropped to 4:5 from the center, so keep the face in the upper-middle.
- If the subject still sits off-centre (common with wide originals), set `Headshot Focus:` to a CSS `object-position` value. The first number slides the crop window horizontally: `50%` is centred, higher moves the subject left, lower moves it right. `60% 50%` is a typical nudge.
- At least 900 px wide.
- The web copy lives in `assets/headshots/web/` and is remade whenever the original is newer. To force a fresh copy, delete the web copy and rebuild.

## Not controlled by these files

Edit these directly in the HTML:

- **The PI's positions & education list** (University of Vermont, Caltech, …) — in `thegroup.html`.
- **Section headings and the empty-section notes** — in `build_team.py`.
- **The "bench next to yours is empty" openings** — in `contact.html`.

In `thegroup.html`, the builder only rewrites what sits between `<!-- team -->` and `<!-- /team -->`, between `<!-- member drawers -->` and `</main>`, and inside the `<!-- build:pi-... -->` markers on the PI card. Don't delete those markers.

## Requirements

Python 3. [Pillow](https://pypi.org/project/Pillow/) (`pip install Pillow`) — only needed when a new web headshot has to be made.
