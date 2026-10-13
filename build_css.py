# -*- coding: utf-8 -*-
"""
Compile the Tailwind styles for the published site.

    python build_css.py _site

Run by the publishing workflow after the site has been collected into a folder. The pages
in the repository load Tailwind's in-browser script, which builds the styles on every
visit and is meant for development only. This replaces it, in the published copies of the
pages, with one small stylesheet (assets/tailwind.css) holding just the classes the site
uses. The pages in the repository are left as they are, so nothing changes when working
on the site locally.

The Tailwind settings (colours, fonts) are read from the pages themselves, so they are
still edited in one place: the "tailwind.config = {...}" block at the top of each page.

Needs Node.js (for npx), which the workflow's machine already has.
"""
import glob, io, os, re, shutil, subprocess, sys, tempfile

TAILWIND = 'tailwindcss@3.4.17'        # same major version as the in-browser script
OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '_site')
CSS = 'assets/tailwind.css'

# the in-browser script and the settings block that follows it
BLOCK = re.compile(r'<script src="https://cdn\.tailwindcss\.com"></script>\s*'
                   r'<script>\s*tailwind\.config\s*=\s*(\{.*?\});?\s*</script>[ \t]*\r?\n?', re.S)


def main():
    pages = sorted(glob.glob(os.path.join(OUT, '*.html')))
    if not pages:
        sys.exit('No pages found in ' + OUT)
    text, configs = {}, set()
    for page in pages:
        text[page] = io.open(page, encoding='utf-8', newline='').read()
        found = BLOCK.search(text[page])
        if not found:
            sys.exit(os.path.basename(page) + ': the Tailwind script and settings block were not found.')
        configs.add(re.sub(r'\s+', ' ', found.group(1)))
    if len(configs) > 1:
        sys.exit('The pages do not all have the same tailwind.config block; make them match.')

    work = tempfile.mkdtemp()
    try:
        config, source = os.path.join(work, 'tailwind.config.js'), os.path.join(work, 'in.css')
        # every place a class name can appear: the pages, and the scripts that draw rows into them
        content = [os.path.join(OUT, '*.html').replace(os.sep, '/'),
                   os.path.join(OUT, 'assets', '*.js').replace(os.sep, '/')]
        io.open(config, 'w', encoding='utf-8').write(
            'module.exports = Object.assign({ content: %r }, %s);\n' % (content, configs.pop()))
        io.open(source, 'w', encoding='utf-8').write('@tailwind base;\n@tailwind components;\n@tailwind utilities;\n')
        npx = shutil.which('npx') or sys.exit('npx (Node.js) is needed to compile the styles.')
        subprocess.run([npx, '--yes', TAILWIND, '-c', config, '-i', source,
                        '-o', os.path.join(OUT, *CSS.split('/')), '--minify'], check=True, cwd=work)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    # The in-browser script adds its styles at the end of <head>, after the page's own
    # <style>; the stylesheet goes in the same place so the same rules win.
    link = '<link rel="stylesheet" href="%s">' % CSS
    for page in pages:
        s = BLOCK.sub('', text[page], count=1)
        nl = '\r\n' if '\r\n' in s else '\n'
        if '</head>' not in s:
            sys.exit(os.path.basename(page) + ': no </head> to put the stylesheet before.')
        s = s.replace('</head>', link + nl + '</head>', 1)
        io.open(page, 'w', encoding='utf-8', newline='').write(s)
    size = os.path.getsize(os.path.join(OUT, *CSS.split('/')))
    print('%s: %.1f KB, linked from %d pages' % (CSS, size / 1024.0, len(pages)))


if __name__ == '__main__':
    main()
