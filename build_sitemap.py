# -*- coding: utf-8 -*-
"""
Write sitemap.xml and robots.txt for search engines.

    python build_sitemap.py _site

Run by the publishing workflow after the site has been collected into a folder. Every
.html page in that folder is listed, so a new page is picked up without editing this
file. The site's address comes from the CNAME file.

Each page's "last changed" date is taken from the repository's history: the most recent
change to the page itself or to the files that fill it (bios for The Group, the .bib
files for Publications, news.txt for the landing and News pages).
"""
import io, os, subprocess, sys, glob
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else ROOT

# what else, besides the page's own file, changes what the page shows
FED_BY = {
    'index.html':        ['assets/news.txt', 'assets/group_photos'],
    'news.html':         ['assets/news.txt'],
    'publications.html': ['assets/publications'],
    'thegroup.html':     ['assets/bios', 'assets/headshots'],
    'research.html':     ['assets/research_schemes'],
}


def site_address():
    cname = os.path.join(ROOT, 'CNAME')
    if os.path.exists(cname):
        host = io.open(cname, encoding='utf-8').read().strip()
        if host:
            return 'https://' + host
    sys.exit('No CNAME file: cannot tell what the site\'s address is.')


def last_changed(paths):
    """YYYY-MM-DD of the newest commit touching any of the paths, or '' without git history."""
    try:
        out = subprocess.run(['git', 'log', '-1', '--format=%cs', '--'] + paths, cwd=ROOT,
                             capture_output=True, text=True, timeout=30).stdout.strip()
        return out
    except Exception:
        return ''


def main():
    base = site_address()
    pages = sorted(os.path.basename(p) for p in glob.glob(os.path.join(OUT, '*.html')))
    pages.sort(key=lambda p: (p != 'index.html', p))            # the landing page first
    rows = []
    for page in pages:
        loc = base + '/' + ('' if page == 'index.html' else page[:-len('.html')])     # /research, not /research.html
        when = last_changed([page] + FED_BY.get(page, []))
        rows.append('  <url>\n    <loc>' + escape(loc) + '</loc>\n' +
                    ('    <lastmod>' + when + '</lastmod>\n' if when else '') + '  </url>')
    io.open(os.path.join(OUT, 'sitemap.xml'), 'w', encoding='utf-8', newline='\n').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(rows) + '\n</urlset>\n')
    io.open(os.path.join(OUT, 'robots.txt'), 'w', encoding='utf-8', newline='\n').write(
        'User-agent: *\nAllow: /\n\nSitemap: ' + base + '/sitemap.xml\n')
    print('sitemap.xml: %d pages | robots.txt -> %s/sitemap.xml' % (len(pages), base))


if __name__ == '__main__':
    main()
