# -*- coding: utf-8 -*-
"""
Build the people on The Group page (thegroup.html) from the files in assets/bios/.

    python build_team.py

What it does
  1. Reads every assets/bios/*.txt (files starting with "_" are skipped - that's the template).
  2. Makes a web-sized copy of each headshot in assets/headshots/web/ if it's missing
     or the original is newer. (Needs Pillow only when a copy has to be made.)
  3. Rewrites, in thegroup.html:
       - the Principal Investigator's photo, name, title, email, CV/profile links and bio
       - every member card and pop-out panel, grouped by Role
  4. Writes assets/publications/group_members.txt - everyone with a bio anywhere under
     assets/bios/ (subfolders such as alumni/ included), current or former. The
     Publications page reads it to decide whose names are set in bold.
  5. Makes a web-sized copy of each photo in assets/group_photos/ (not its subfolders)
     in assets/group_photos/web/ if it's missing or the original is newer. The landing
     page uses those copies; which photos it shows is set in index.html.

What it leaves alone
  - The PI's "positions and education" list  -> edit that directly in thegroup.html

Format of a bio file: see assets/bios/README.md
"""
import io, os, re, sys, glob, html, textwrap

ROOT = os.path.dirname(os.path.abspath(__file__))
BIOS = os.path.join(ROOT, 'assets', 'bios')
SHOTS = os.path.join(ROOT, 'assets', 'headshots')
WEB = os.path.join(SHOTS, 'web')
PAGE = os.path.join(ROOT, 'thegroup.html')
ROSTER = os.path.join(ROOT, 'assets', 'publications', 'group_members.txt')
GROUP = os.path.join(ROOT, 'assets', 'group_photos')
GROUP_WEB = os.path.join(GROUP, 'web')
GROUP_WIDTH = 1800      # px; the landing page shows the photo about 1150 px wide, doubled for sharp screens
NL = '\n'
e = html.escape

# Role (as written in a bio file) -> section on the page, in page order.
SECTIONS = [
    ('Postdoctoral Researchers', 'Postdoctoral Researcher', None),
    ('Graduate Students',        'Graduate Student',        'recruiting'),
    ('Undergraduate Students',   'Undergraduate Researcher', None),
    ('Lab Mascots',              'Lab Mascot',              'soon'),
]
PI_ROLE = 'Principal Investigator'
ROLES = {PI_ROLE.lower(): PI_ROLE, **{r.lower(): r for _, r, _ in SECTIONS}}
ROLES['furry companion'] = 'Lab Mascot'  # the section's old name still works in bio files

FIELDS = ['Name', 'Role', 'Title', 'Joined', 'Headshot', 'Headshot Focus', 'Card Shift', 'Email', 'Fellowship', 'Education',
          'Class Year', 'CV', 'ORCID', 'LinkedIn', 'Google Scholar', 'Bio']
KEYS = {f.lower(): f for f in FIELDS}
KEYS['scholar'] = 'Google Scholar'

problems, notes = [], []

MONTHS = {m: i for i, m in enumerate(
    ['january', 'february', 'march', 'april', 'may', 'june', 'july',
     'august', 'september', 'october', 'november', 'december'], 1)}
MONTHS.update({m[:3]: i for m, i in list(MONTHS.items())})
MONTHS['sept'] = 9


def join_date(text):
    """'August 31, 2026' / 'March 2026' / '2026-08-31' / '8/31/2026' / '2026' -> (year, month, day); 0 = not given."""
    t = text.strip().lower().replace(',', ' ')
    t = re.sub(r'(\d)(st|nd|rd|th)\b', r'\1', t)
    t = ' '.join(t.replace('.', ' ').split())
    y = mo = dy = None
    for pat, order in ((r'^(\d{4})-(\d{1,2})(?:-(\d{1,2}))?$', 'ymd'),
                       (r'^(\d{1,2})/(\d{1,2})/(\d{4})$', 'mdy'),
                       (r'^(\d{1,2})/(\d{4})$', 'my'),
                       (r'^([a-z]+) (\d{1,2}) (\d{4})$', 'Mdy'),
                       (r'^(\d{1,2}) ([a-z]+) (\d{4})$', 'dMy'),
                       (r'^([a-z]+) (\d{4})$', 'My'),
                       (r'^(\d{4})$', 'y')):
        m = re.match(pat, t)
        if not m:
            continue
        g = dict(zip(order, m.groups()))
        y = int(g.get('y'))
        mo = MONTHS.get(g['M']) if 'M' in g else int(g.get('m') or 0)
        dy = int(g.get('d') or 0)
        break
    if y is None or mo is None or not (0 <= mo <= 12) or not (0 <= dy <= 31):
        return None
    return (y, mo, dy)


# ------------------------------------------------------------------ read a bio file
def read_text(path):
    raw = open(path, 'rb').read()
    for enc in ('utf-8-sig', 'cp1252'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode('utf-8', errors='replace')


def parse(path):
    name = os.path.basename(path)
    text = read_text(path).replace('\r\n', '\n').replace('\xa0', ' ')
    d = {k: '' for k in FIELDS}
    d['Education'] = []
    d['file'] = name
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        m = re.match(r'^\s*([A-Za-z][A-Za-z ]*?)\s*:\s?(.*)$', line)
        key = KEYS.get(m.group(1).strip().lower()) if m else None
        if not key:
            problems.append(f'{name}: line {i} is not a recognised field -> "{line.strip()[:60]}"')
            continue
        value = m.group(2).strip()
        if key == 'Bio':  # everything from here to the end of the file
            rest = [value] + lines[i:]
            d['Bio'] = '\n'.join(rest).strip()
            break
        if key == 'Education':
            if value:
                d['Education'].append(value)
        else:
            d[key] = value

    for req in ('Name', 'Role', 'Headshot', 'Bio'):
        if not (d[req] if req != 'Bio' else d['Bio'].strip()):
            problems.append(f'{name}: "{req}:" is required but empty')

    role = ROLES.get(d['Role'].lower())
    if d['Role'] and not role:
        problems.append(f'{name}: Role "{d["Role"]}" is not one of: ' + ', '.join(dict.fromkeys(ROLES.values())))
    d['Role'] = role or d['Role']

    # emails stay harvest-proof: always " [at] " on the site
    if '@' in d['Email']:
        notes.append(f'{name}: write the email as "user [at] uvm.edu" - these files are public on the site')
    d['Email'] = re.sub(r'\s*(?:\[at\]|@)\s*', ' [at] ', d['Email']) if d['Email'] else ''

    # "Ph.D. Somewhere (Advisor)" -> ("Ph.D. Somewhere", "Advisor")
    creds = []
    for ed in d['Education']:
        m = re.match(r'^(.*?)\s*\(([^)]*)\)\s*$', ed)
        creds.append((m.group(1).strip(), m.group(2).strip()) if m else (ed, ''))
    if d['Class Year']:
        creds.append(('Class of ' + re.sub(r'^class of\s*', '', d['Class Year'], flags=re.I), ''))
    d['creds'] = creds
    d['paragraphs'] = [' '.join(p.split()) for p in re.split(r'\n\s*\n', d['Bio']) if p.strip()]
    d['slug'] = re.sub(r'[^a-z0-9]+', '-', d['Name'].lower()).strip('-')
    # sections list newest first; no date -> after everyone dated; ties -> last name
    joined = join_date(d['Joined']) if d['Joined'] else None
    if d['Joined'] and not joined:
        problems.append(f'{name}: can\'t read Joined "{d["Joined"]}" - write it like "August 31, 2026" or "March 2026"')
    parts = d['Name'].split()
    newest = (0, -joined[0], -joined[1], -joined[2]) if joined else (1, 0, 0, 0)
    d['sort'] = newest + ((parts[-1].lower(), d['Name'].lower()) if parts else ('', ''))

    if d['CV'] and not os.path.exists(os.path.join(ROOT, 'assets', d['CV'])):
        problems.append(f'{name}: CV file not found -> assets/{d["CV"]}')
    return d


# ------------------------------------------------------------------ headshots
def focus(d):
    """Cards crop 4:5 from the centre. 'Headshot Focus:' re-aims that crop when the
    subject sits off-centre in a wide original (CSS object-position, e.g. "60% 50%")."""
    return ' style="object-position:' + e(d['Headshot Focus']) + '"' if d['Headshot Focus'] else ''


def card_style(d):
    """The card's photo only: the focus, plus 'Card Shift: 5%' to slide the photo up
    behind the caption so the face sits higher (see .member-photo in thegroup.html)."""
    parts = []
    if d['Headshot Focus']:
        parts.append('object-position:' + e(d['Headshot Focus']))
    m = re.search(r'-?\d+(?:\.\d+)?', d['Card Shift'])
    if m:
        if not 0 < float(m.group(0)) <= 15:
            problems.append(f'{d["file"]}: "Card Shift:" should be between 1% and 15%')
        else:
            parts.append('--lift:' + m.group(0) + '%')
    return ' style="' + ';'.join(parts) + '"' if parts else ''


# When the site is built by the host (GitHub Actions and most others set CI) the files
# have just been checked out of git, so their dates say nothing about which is newer.
# There, every web copy is remade from its original; on your own computer only the
# ones whose original has changed.
ON_HOST = bool(os.environ.get('CI'))


def stale(src, out):
    return ON_HOST or not os.path.exists(out) or os.path.getmtime(src) > os.path.getmtime(out)


def web_headshot(d):
    src = os.path.join(SHOTS, d['Headshot'])
    if not os.path.exists(src):
        problems.append(f'{d["file"]}: headshot not found -> assets/headshots/{d["Headshot"]}')
        return 'assets/headshots/web/' + os.path.splitext(d['Headshot'])[0] + '.jpg'
    out_name = os.path.splitext(d['Headshot'])[0] + '.jpg'
    out = os.path.join(WEB, out_name)
    if stale(src, out):
        try:
            from PIL import Image, ImageOps
        except ImportError:
            if os.path.exists(out):
                notes.append(f'Pillow is not installed, so the existing web headshot {out_name} was kept as it is')
            else:
                problems.append('Pillow is needed to make web headshots: pip install Pillow')
        else:
            os.makedirs(WEB, exist_ok=True)
            im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
            if im.width > 900:
                im = im.resize((900, round(im.height * 900 / im.width)), Image.LANCZOS)
            im.save(out, 'JPEG', quality=84, optimize=True, progressive=True)
            notes.append(f'made web headshot assets/headshots/web/{out_name} '
                         f'({os.path.getsize(src) / 1e6:.1f} MB -> {os.path.getsize(out) / 1024:.0f} KB)')
    return 'assets/headshots/web/' + out_name


# ------------------------------------------------------------------ markup pieces
ICON = {
    'LinkedIn': 'M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z',
    'Google Scholar': 'M5.242 13.769 0 9.5 12 0l12 9.5-5.242 4.269C17.548 11.249 14.978 9.5 12 9.5c-2.977 0-5.548 1.748-6.758 4.269zM12 10a7 7 0 1 0 0 14 7 7 0 0 0 0-14z',
    'ORCID': 'M12 0C5.372 0 0 5.372 0 12s5.372 12 12 12 12-5.372 12-12S18.628 0 12 0zM7.369 4.378c.525 0 .947.431.947.947s-.422.947-.947.947a.95.95 0 0 1-.947-.947c0-.525.422-.947.947-.947zm-.722 3.038h1.444v10.041H6.647V7.416zm3.562 0h3.9c3.712 0 5.344 2.653 5.344 5.025 0 2.578-2.016 5.025-5.325 5.025h-3.919V7.416zm1.444 1.303v7.444h2.297c3.272 0 4.022-2.484 4.022-3.722 0-2.016-1.284-3.722-4.097-3.722h-2.222z',
}
PROFILES = ('LinkedIn', 'Google Scholar', 'ORCID')  # display order
MAIL = ('<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/>'
        '<path d="m3.5 6.5 8.5 6.5 8.5-6.5"/></svg>')
ARROW = ('<svg width="15" height="10" viewBox="0 0 17 11" fill="none" aria-hidden="true"><path d="M1 5.5H15M15 5.5L10.6 1M15 5.5L10.6 10" '
         'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>')
CLOSE_X = ('<svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M1 1l10 10M11 1 1 11" '
           'stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>')


def social(kind, url, who, ind):
    return (ind + '<a href="' + e(url) + '" class="sociallink" aria-label="' + e(who) + ' on ' + kind + '">' + NL +
            ind + '  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="' + ICON[kind] + '"/></svg>' + NL +
            ind + '</a>' + NL)


def cv_link(path, ind):
    return (ind + '<a href="assets/' + e(path) + '" class="arrowlink">' + NL +
            ind + '  View CV' + NL +
            ind + '  <svg width="17" height="11" viewBox="0 0 17 11" fill="none" aria-hidden="true">' + NL +
            ind + '    <path d="M1 5.5H15M15 5.5L10.6 1M15 5.5L10.6 10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>' + NL +
            ind + '  </svg>' + NL +
            ind + '</a>' + NL)


# ------------------------------------------------------------------ PI
def pi_regions(d, shot):
    photo = '        <img src="' + shot + '" alt="Portrait of ' + e(d['Name']) + '"' + focus(d) + '>' + NL

    head = ('        <h3 class="display-sm mt-[var(--s3)] text-[clamp(1.8rem,3.4vw,2.4rem)]" style="color:var(--catamount)">' + NL +
            '          ' + e(d['Name']) + NL + '        </h3>' + NL)
    if d['Title']:
        head += '        <p class="datum mt-2" style="color:var(--ink-faint)">' + e(d['Title']) + '</p>' + NL
    if d['Email']:
        head += '        <p class="datum mt-[var(--s1)]" style="color:var(--ink-faint)">' + e(d['Email']) + '</p>' + NL

    links = ''
    profiles = [(k, d[k]) for k in PROFILES if d[k]]
    if d['CV'] or profiles:
        # CV link on top, profile icons stacked beneath it
        links = '            <div class="mt-[var(--s6)] flex flex-col items-start gap-[var(--s4)]">' + NL
        if d['CV']:
            links += cv_link(d['CV'], '              ')
        if profiles:
            # -3px: the 24px hit box insets the 18px glyph, so pull it back to line up with "View CV"
            links += '              <div class="flex items-center gap-[var(--s3)] -ml-[3px]">' + NL
            links += ''.join(social(k, u, d['Name'], '                ') for k, u in profiles)
            links += '              </div>' + NL
        links += '            </div>' + NL

    bio = ''
    for i, para in enumerate(d['paragraphs']):
        cls = 'text-[16px] leading-[1.75]' + (' mt-[var(--s4)]' if i else '')
        bio += ('        <p class="' + cls + '" style="color:var(--ink-soft);text-align:justify;text-justify:inter-word;-webkit-hyphens:auto;hyphens:auto;">' + NL +
                textwrap.fill(e(para, quote=False), width=96, initial_indent=' ' * 10, subsequent_indent=' ' * 10,
                              break_long_words=False, break_on_hyphens=False) + NL +
                '        </p>' + NL)
    return {'pi-photo': photo, 'pi-head': head, 'pi-links': links, 'pi-bio': bio}


# ------------------------------------------------------------------ members
def card(d, shot):
    has_contact = d['Email'] or d['CV'] or any(d[k] for k in PROFILES)
    cue = 'Bio &amp; contact' if has_contact else 'Read bio'
    out = [
        '        <li class="reveal">',
        '          <button type="button" class="member" data-open="member-' + d['slug'] + '" aria-haspopup="dialog">',
        '            <span class="portrait member-photo aspect-[4/5]">',
        '              <img src="' + shot + '" alt="" loading="lazy" decoding="async"' + card_style(d) + '>',
        '              <span class="tone"></span>',
        '            </span>',
        '            <span class="member-cap">',
        '              <span class="member-name">' + e(d['Name']) + '</span>',
    ]
    if d['Fellowship']:  # directly under the name, in the name's typeface and colour
        out.append('              <span class="member-fellow">' + e(d['Fellowship']) + '</span>')
    out += ['              <span class="member-role tag">' + e(t) + '</span>' for t, _ in d['creds']]
    out += ['              <span class="member-cue tag">' + cue + ' ' + ARROW + '</span>',
            '            </span>', '          </button>', '        </li>']
    return NL.join(out) + NL


def drawer(d, shot):
    did = 'member-' + d['slug']
    out = [
        '<dialog class="drawer" id="' + did + '" aria-labelledby="' + did + '-name">',
        '  <div class="drawer-scrim" data-close></div>',
        '  <div class="drawer-panel">',
        '    <div class="drawer-bar">',
        '      <button type="button" class="drawer-close tag" data-close autofocus>',
        '        Close',
        '        ' + CLOSE_X,
        '      </button>',
        '    </div>',
        '    <div class="drawer-body">',
        '      <div class="portrait aspect-[4/5]">',
        '        <img src="' + shot + '" alt="Portrait of ' + e(d['Name']) + '" loading="lazy" decoding="async"' + focus(d) + '>',
        '        <span class="tone"></span>',
        '      </div>',
        '      <h2 id="' + did + '-name" class="display-sm mt-[var(--s5)] text-[28px]" style="color:var(--catamount)">' + e(d['Name']) + '</h2>',
        # a fellowship replaces the role line; otherwise title, else role
        '      <p class="datum mt-2" style="color:var(--ink-faint)">' + e(d['Fellowship'] or d['Title'] or d['Role']) + '</p>',
    ]
    if d['creds']:  # the panel keeps the advisors the cards leave out
        out.append('      <ul class="mt-[var(--s4)] space-y-[var(--s3)] text-[15px] leading-[1.55]" style="color:var(--ink)" role="list">')
        for t, adv in d['creds']:
            a = ('<br><span style="color:var(--ink-soft)"><em>Advisor:</em> ' + e(adv) + '</span>') if adv else ''
            out.append('        <li>' + e(t) + a + '</li>')
        out.append('      </ul>')
    for i, para in enumerate(d['paragraphs']):
        out.append('      <p class="' + ('mt-[var(--s5)]' if i == 0 else 'mt-[var(--s4)]') +
                   ' text-[15.5px] leading-[1.75]" style="color:var(--ink-soft)">' + e(para) + '</p>')

    rows = []
    if d['Email']:
        rows += ['        <p class="flex items-center gap-[var(--s3)] text-[15px]" style="color:var(--ink)">',
                 '          <span style="color:var(--catamount)">' + MAIL + '</span><span class="sr-only">Email: </span>' + e(d['Email']),
                 '        </p>']
    profiles = [(k, d[k]) for k in PROFILES if d[k]]
    if d['CV'] or profiles:
        rows.append('        <div class="' + ('mt-[var(--s4)] ' if d['Email'] else '') + 'flex flex-wrap items-center gap-[var(--s3)]">')
        if d['CV']:
            rows.append(cv_link(d['CV'], '          ').rstrip(NL))
        rows += [social(k, u, d['Name'], '          ').rstrip(NL) for k, u in profiles]
        rows.append('        </div>')
    if rows:
        out.append('      <div class="mt-[var(--s6)] border-t pt-[var(--s5)]" style="border-color:var(--rule)">')
        out += rows
        out.append('      </div>')
    out += ['    </div>', '  </div>', '</dialog>']
    return NL.join(out) + NL


def empty(kind):
    body = ('Recruiting &mdash; <a class="advisorlink" href="contact.html#openings">see open positions</a>'
            if kind == 'recruiting' else 'Coming soon')
    return '    <p class="team-empty reveal mt-[var(--s5)] datum" style="color:var(--ink-faint)">' + body + '</p>' + NL


# ------------------------------------------------------------------ group photos
def web_group_photos():
    """assets/group_photos/landscape.png -> assets/group_photos/web/landscape.jpg.
    Phone originals run to several MB each; these are what the site serves."""
    made = 0
    for f in sorted(glob.glob(os.path.join(GROUP, '*'))):
        stem, ext = os.path.splitext(os.path.basename(f))
        if ext.lower() not in ('.png', '.jpg', '.jpeg', '.webp', '.tif', '.tiff', '.bmp') or stem.startswith('_'):
            continue
        out = os.path.join(GROUP_WEB, stem + '.jpg')
        if not stale(f, out):
            continue
        try:
            from PIL import Image, ImageOps
        except ImportError:
            notes.append('Pillow is needed to make web group photos: pip install Pillow')
            return made
        os.makedirs(GROUP_WEB, exist_ok=True)
        im = ImageOps.exif_transpose(Image.open(f)).convert('RGB')
        if im.width > GROUP_WIDTH:
            im = im.resize((GROUP_WIDTH, round(im.height * GROUP_WIDTH / im.width)), Image.LANCZOS)
        im.save(out, 'JPEG', quality=82, optimize=True, progressive=True)
        made += 1
        notes.append(f'made web group photo assets/group_photos/web/{stem}.jpg '
                     f'({os.path.getsize(f) / 1e6:.1f} MB -> {os.path.getsize(out) / 1024:.0f} KB)')
    return made


# ------------------------------------------------------------------ roster for the Publications page
def write_roster():
    """Everyone who has, or had, a bio: assets/bios/ and every folder beneath it.
    Lab mascots are left out. Only the Name: and Role: lines are read, so a former
    member's file can be moved into a subfolder as it is - a missing headshot there
    does not matter."""
    names = []
    for f in sorted(glob.glob(os.path.join(BIOS, '**', '*.txt'), recursive=True)):
        if os.path.basename(f).startswith('_'):
            continue
        text = read_text(f).replace('\r\n', '\n')
        name = re.search(r'^[ \t]*Name[ \t]*:[ \t]*(.+?)[ \t]*$', text, re.M)
        role = re.search(r'^[ \t]*Role[ \t]*:[ \t]*(.+?)[ \t]*$', text, re.M)
        if not name:
            notes.append(os.path.relpath(f, BIOS) + ': no "Name:" line, so left out of group_members.txt')
            continue
        if role and ROLES.get(role.group(1).lower()) == 'Lab Mascot':
            continue
        if name.group(1) not in names:
            names.append(name.group(1))
    os.makedirs(os.path.dirname(ROSTER), exist_ok=True)
    io.open(ROSTER, 'w', encoding='utf-8', newline='').write(
        '# Group members, current and former - one name per line.\n'
        '# The Publications page sets these people in bold wherever they appear as an author.\n'
        '# Written by build_team.py from assets/bios/ and its subfolders: edit the bio files,\n'
        '# not this list, which is replaced each time the script runs.\n\n'
        + ''.join(n + '\n' for n in names))
    return names


# ------------------------------------------------------------------ run
def replace_between(s, start, end, new, label):
    a = s.find(start)
    b = s.find(end, a + len(start)) if a >= 0 else -1
    if a < 0 or b < 0:
        problems.append(f'thegroup.html: marker for {label} not found - was it deleted?')
        return s
    return s[:a + len(start)] + new + s[b:]


def main():
    files = sorted(f for f in glob.glob(os.path.join(BIOS, '*.txt')) if not os.path.basename(f).startswith('_'))
    people = [parse(f) for f in files]
    shots = {d['file']: web_headshot(d) for d in people}

    pis = [d for d in people if d['Role'] == PI_ROLE]
    if len(pis) > 1:
        problems.append('more than one bio file has Role: Principal Investigator -> ' + ', '.join(d['file'] for d in pis))
    slugs = [d['slug'] for d in people]
    for s_ in {x for x in slugs if slugs.count(x) > 1}:
        problems.append(f'two bio files share the name that makes id "member-{s_}"')

    if problems:
        print('Nothing was changed. Fix these first:')
        for p in problems:
            print('  - ' + p)
        sys.exit(1)

    s = io.open(PAGE, encoding='utf-8').read()

    if pis:
        d = pis[0]
        for key, block in pi_regions(d, shots[d['file']]).items():
            ind = ' ' * (8 if key in ('pi-photo', 'pi-head', 'pi-bio') else 12)
            s = replace_between(s, f'<!-- build:{key} -->\n', ind + f'<!-- /build:{key} -->', block, key)

    team = ['    <!-- team -->' + NL]
    counts = []
    for i, (heading, role, empty_kind) in enumerate(SECTIONS):
        members = sorted((d for d in people if d['Role'] == role), key=lambda d: d['sort'])
        counts.append(f'{heading}: {len(members)}')
        hid = 'team-' + re.sub(r'[^a-z]+', '-', heading.lower()).strip('-')
        team.append('    <h3 id="' + hid + '" class="reveal mt-[var(--' + ('s9' if i == 0 else 's8') + ')] tag pb-[var(--s3)] border-b" '
                    'style="color:var(--ink-faint);border-color:var(--rule)">' + NL + '      ' + heading + NL + '    </h3>' + NL)
        if members:
            team.append('    <ul class="mt-[var(--s5)] grid gap-[var(--s4)] grid-cols-2 sm:grid-cols-3 lg:grid-cols-4" role="list">' + NL)
            team += [card(d, shots[d['file']]) for d in members]
            team.append('    </ul>' + NL + NL)
        else:
            team.append(empty(empty_kind) + NL)

    ordered = [d for _, role, _ in SECTIONS for d in sorted((x for x in people if x['Role'] == role), key=lambda x: x['sort'])]
    drawers = '<!-- member drawers -->' + NL + ''.join(drawer(d, shots[d['file']]) for d in ordered)

    a = s.find('    <!-- team -->\n'); b = s.find('    <!-- /team -->\n')
    c = s.find('<!-- member drawers -->\n'); z = s.find('\n</main>')
    if min(a, b, c, z) < 0:
        print('Nothing was changed: thegroup.html is missing the <!-- team -->, <!-- /team --> '
              'or <!-- member drawers --> marker.')
        sys.exit(1)
    s = s[:a] + ''.join(team) + s[b:]
    c = s.find('<!-- member drawers -->\n'); z = s.find('\n</main>')
    s = s[:c] + drawers + s[z:]

    if problems:
        print('Nothing was changed. Fix these first:')
        for p in problems:
            print('  - ' + p)
        sys.exit(1)

    io.open(PAGE, 'w', encoding='utf-8', newline='').write(s)
    roster = write_roster()
    web_group_photos()
    for n in notes:
        print('note: ' + n)
    print('thegroup.html updated -> ' + ('PI: ' + pis[0]['Name'] + ' | ' if pis else '') + ' | '.join(counts))
    print('group_members.txt updated -> ' + str(len(roster)) + ' names for the Publications page')


if __name__ == '__main__':
    main()
