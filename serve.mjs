import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFile } from 'node:child_process';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.PORT) || 3000;

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.gif': 'image/gif',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.pdf': 'application/pdf',
  '.txt': 'text/plain; charset=utf-8',
};

http
  .createServer((req, res) => {
    let urlPath = decodeURIComponent(req.url.split('?')[0]);
    if (urlPath.endsWith('/')) urlPath += 'index.html';

    const filePath = path.join(ROOT, urlPath);
    if (!filePath.startsWith(ROOT)) {
      res.writeHead(403).end('Forbidden');
      return;
    }

    fs.readFile(filePath, (err, data) => {
      if (err) {
        res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
        res.end('404 Not Found: ' + urlPath);
        return;
      }
      res.writeHead(200, {
        'Content-Type': TYPES[path.extname(filePath).toLowerCase()] || 'application/octet-stream',
        'Cache-Control': 'no-store',
      });
      res.end(data);
    });
  })
  .listen(PORT, () => {
    console.log(`Serving ${ROOT}\n  http://localhost:${PORT}`);
    watchTeam();
  });

// ── The Group page rebuilds itself ───────────────────────────────────────────
// While this server runs, any change under assets/bios/ (a new or edited bio, a
// bio moved into alumni/), to a headshot or to a group photo re-runs build_team.py, so
// thegroup.html and the publications member list stay current. Refresh the
// browser to see it. The web/ folders are skipped: the build writes there.
function watchTeam() {
  const script = path.join(ROOT, 'build_team.py');
  if (!fs.existsSync(script)) return;
  let timer = null, running = false, again = false;

  // Name, size and modified time of every bio and headshot. Windows and OneDrive
  // report "changes" when a file is merely read, so a build only goes ahead when
  // this fingerprint really differs from the one last built.
  const bios = path.join(ROOT, 'assets', 'bios'), shots = path.join(ROOT, 'assets', 'headshots');
  const group = path.join(ROOT, 'assets', 'group_photos');
  const fingerprint = () => {
    const rows = [];
    const walk = (dir) => {
      for (const ent of fs.existsSync(dir) ? fs.readdirSync(dir, { withFileTypes: true }) : []) {
        const full = path.join(dir, ent.name);
        if (ent.isDirectory()) { if (ent.name !== 'web') walk(full); continue; }
        const st = fs.statSync(full);
        rows.push(`${full}|${st.size}|${st.mtimeMs}`);
      }
    };
    walk(bios); walk(shots); walk(group);
    return rows.sort().join('\n');
  };
  let built = null;

  const build = (why) => {
    if (running) { again = true; return; }
    const now = fingerprint();
    if (now === built) return;
    built = now;
    running = true;
    execFile('python', [script], { cwd: ROOT, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } },
      (err, stdout, stderr) => {
        const out = (stdout + stderr).trim().split('\n').map((l) => '  ' + l).join('\n');
        console.log(`[team] ${why}\n${out || '  (no output)'}`);
        running = false;
        if (again) { again = false; build('changed again during the build'); }
      });
  };

  const watch = (dir, skip) => {
    if (!fs.existsSync(dir)) return;
    fs.watch(dir, { recursive: true }, (event, file) => {
      const name = String(file || '').replace(/\\/g, '/');
      if (skip && skip.test(name)) return;
      if (/(^|\/)(~\$|\.)|\.tmp$|~$/.test(name)) return;           // editor lock and temp files
      clearTimeout(timer);                                         // a save fires several events
      timer = setTimeout(() => build(`${path.basename(dir)}/${name} changed`), 500);
    });
  };
  watch(path.join(ROOT, 'assets', 'bios'));
  watch(path.join(ROOT, 'assets', 'headshots'), /^web(\/|$)/);
  watch(group, /^web(\/|$)/);
  build('server started');
}
