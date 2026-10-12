# Publications

The list on the **Publications** page (`publications.html`) is read from the `.bib` files in this folder every time the page loads. There is nothing to run: save a file here and refresh the page.

## Adding or changing papers

Export from Zotero as BibTeX / Better BibTeX and save the file here under one of these names:

| File | Heading on the page | What goes in it |
|---|---|---|
| `prior_uvm.bib` | Prior to UVM | papers published before the lab opened at UVM |
| `2026.bib`, `2027.bib`, … | the year | papers published from UVM in that year |

- A heading appears only if its file exists. Delete a file and its heading goes away.
- Years are listed newest first, with "Prior to UVM" last. The top heading starts open; the rest start collapsed.
- A file with any other name is ignored. The page looks for `prior_uvm.bib` and for year files from 2020 up to next year (`FIRST_YEAR` in the script at the foot of `publications.html`).

## What each entry needs

`title`, `author` and `year`. `journal`, `volume`, `pages`, `month` and `doi` are used when present:

- `doi` makes the title and the DOI button link to the article (`url` is the fallback).
- `month` sets the order within a year. Without it, papers from the same year fall back to alphabetical by citation key.

Zotero "Contributor" creators (exported as `collaborator`) are added to the end of the author list — except in *Organic Syntheses* papers, where they are the checkers and are shown as "checked by …" after the authors. This happens for any entry whose journal is `Org. Synth.` or `Organic Syntheses`. A `checked` field does the same for any journal.

Everything else in the export (abstract, keywords, file paths) is ignored.

## Extra buttons (`extras.txt`)

Each paper has a button linking to the article. To add more under it (supporting information, a highlight, a preprint), add an entry to `extras.txt` in this folder:

```
DOI:    10.1002/anie.202103435
Link:   https://example.com/highlight
Label:  Highlight
```

The paper is found by its DOI across all the `.bib` files. Start every entry with its `DOI:` line; repeat the DOI in a second entry for a second button. An entry missing a field, or whose DOI matches no paper, is ignored.

## Graphical abstracts (`TOC.txt`)

To show a paper's TOC graphic under its citation, save the image in the `TOCs` folder and add an entry to `TOC.txt`:

```
DOI:  10.1002/anie.202103435
TOC:  dorn2021_modular.png
```

The paper is found by its DOI across all the `.bib` files. Write the file name exactly as saved, capitals and ending included. An entry whose DOI matches no paper, or whose file is not in `TOCs`, is ignored.

## Numbers and bold names

- Papers are numbered oldest to newest across the whole list, so the newest paper carries the highest number.
- Names listed in `group_members.txt` are set in bold. That file is written by `build_team.py` from every bio under `assets/bios/`, subfolders included — so to keep a former member in bold, move their bio into a subfolder such as `assets/bios/alumni/` rather than deleting it, then run `python build_team.py`. Don't edit `group_members.txt` by hand; it is replaced on each run.
- A name is matched on surname plus first initial ("Stanna Dorn" matches "Dorn, S. K.").

## Seeing it locally

Open the page through the dev server (`node serve.mjs`, then `http://localhost:3000/publications.html`). Opened straight from the folder as a file, a browser will not let the page read the `.bib` files.

## Not controlled by these files

The line above the list and the Google Scholar / ORCID links are edited directly in `publications.html`.
