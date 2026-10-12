# Dorn Lab website

The website of the Dorn Lab, Department of Chemistry, University of Vermont.

It is a plain static site: one `.html` file per page, with everything else in `assets/`. It is published with GitHub Pages: a GitHub Actions workflow rebuilds and republishes the site every time this repository changes.

## Updating the site

Edit a file here on GitHub (or push a change) and the live site updates itself a minute or two later. Nothing needs to be run by hand.

| To change | Edit | Details |
|---|---|---|
| Group members, bios, headshots | `assets/bios/` and `assets/headshots/` | [`assets/bios/README.md`](assets/bios/README.md) |
| Publications | the `.bib` files in `assets/publications/` | [`assets/publications/README.md`](assets/publications/README.md) |
| Extra buttons and TOC graphics on publications | `extras.txt`, `TOC.txt` and `TOCs/` in `assets/publications/` | same README |
| News (landing page and News page) | `assets/news.txt` | instructions at the top of that file |
| Group photo on the landing page | `assets/group_photos/` | replace a photo, keeping its file name |
| Wording and layout of a page | the page's `.html` file | |

A former member stays in bold on the Publications page if their bio is moved into `assets/bios/alumni/` instead of being deleted.

File names are case-sensitive on the live site: `Headshot.JPG` and `headshot.jpg` are different files there, even though Windows treats them as the same. Write a file name in a bio or text file exactly as the file is saved.

## How the updating works

- **News and publications** are read by the page in the visitor's browser, straight from `assets/news.txt` and `assets/publications/`. A change is live as soon as the workflow has republished.
- **The Group page** is written by `build_team.py`, which the workflow runs on every deployment (`.github/workflows/deploy.yml`). It reads the bios, rewrites `thegroup.html`, writes `assets/publications/group_members.txt` (the names set in bold on the Publications page) and makes the web-sized copies of headshots and group photos in the two `web/` folders.

- **Search engines** get a `sitemap.xml` and `robots.txt`, written by `build_sitemap.py` on every deployment. A new page is listed automatically. Each page's description for search results is the `<meta name="description">` line near the top of its `.html` file.

If a deployment fails, open the failed run under the repository's **Actions** tab and read its log: `build_team.py` stops with a plain message when a bio has a problem, for example a headshot file name that does not exist.

## Working on the site locally

    node serve.mjs

then open <http://localhost:3000>. While it runs, the server re-runs `build_team.py` whenever a bio, headshot or group photo changes. It needs Node.js, Python 3 and Pillow (`pip install Pillow`).

The pages must be opened through a server, not by double-clicking the `.html` files, or the browser will not let them read the news and publication files.
