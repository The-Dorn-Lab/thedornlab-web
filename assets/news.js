// Group news, read from assets/news.txt each time a page loads.
//
// Any element with id="news-list" is filled with the entries, newest first.
// data-limit="3" keeps it to the latest three (the landing page); without it
// every entry is listed (news.html). The format of news.txt is described at
// the top of that file.
(() => {
  const root = document.getElementById('news-list');
  if (!root) return;
  const limit = parseInt(root.dataset.limit, 10) || Infinity;
  const MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'];

  // "Aug 2026" / "August 31, 2026" / "2026-08-31" / "2024" -> a number that sorts by date
  function when(text) {
    const t = text.toLowerCase();
    const iso = /(\d{4})-(\d{1,2})(?:-(\d{1,2}))?/.exec(t);
    if (iso) return +iso[1] * 10000 + +iso[2] * 100 + (+iso[3] || 0);
    const year = /\b(19|20)\d\d\b/.exec(t);
    const word = /[a-z]{3,}/.exec(t);
    const month = word ? MONTHS.indexOf(word[0].slice(0, 3)) + 1 : 0;
    const day = /\b(\d{1,2})(?:st|nd|rd|th)?\b(?!\d)/.exec(t.replace(/\b(19|20)\d\d\b/, ''));
    return (year ? +year[0] : 0) * 10000 + month * 100 + (month && day ? +day[1] : 0);
  }

  function parse(text) {
    const entries = [];
    let e = null, field = null;
    for (const raw of text.split(/\r?\n/)) {
      if (/^\s*#/.test(raw)) continue;
      const line = raw.trim();
      // "Date Aug 2026" without the colon is accepted too, as long as it holds a year
      const m = /^(date|title|content|category)\s*:\s*(.*)$/i.exec(line) ||
                (/^date\s+.*\b(19|20)\d\d\b/i.test(line) && line.length < 40 ? /^(date)\s+(.*)$/i.exec(line) : null);
      if (m) {
        field = m[1].toLowerCase();
        if (field === 'date') { e = { date: '', title: '', content: '', category: '' }; entries.push(e); }
        if (e) e[field] = m[2].trim();
      } else if (line && e && field === 'content') {
        e.content += (e.content ? ' ' : '') + line;          // content carried over several lines
      } else if (!line) {
        field = null;
      }
    }
    return entries
      .filter((x) => x.title)
      .map((x, i) => ({ ...x, at: when(x.date), order: i }))
      .sort((a, b) => b.at - a.at || a.order - b.order);
  }

  const el = (tag, cls, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  };

  // latest: the newest entry of all - its category label is the gold badge
  function row(x, latest) {
    const art = el('article', 'newsrow');
    const date = el('p', 'datum', x.date);
    date.style.color = 'var(--ink-faint)';
    const body = el('div');
    const h = el('h3', 'display-sm', x.title);
    h.style.cssText = 'font-size:20px;color:var(--catamount)';
    body.appendChild(h);
    if (x.content) {
      const p = el('p', '', x.content);
      p.style.cssText = 'margin-top:4px;max-width:86ch;font-size:16px;line-height:1.7;color:var(--ink-soft)';
      body.appendChild(p);
    }
    art.append(date, body);
    if (x.category) {
      const tag = el('span', 'tag news-cat', x.category);
      if (latest) {
        tag.style.cssText = 'background:var(--gold);color:var(--catamount);border-radius:999px;padding:6px 12px';
      } else tag.style.color = 'var(--ink-faint)';
      art.appendChild(tag);
    }
    return art;
  }

  const say = (text) => {
    root.textContent = '';
    const p = el('p', 'datum', text);
    p.style.cssText = 'color:var(--ink-faint);padding:var(--s5) 0';
    root.appendChild(p);
  };

  fetch('assets/news.txt', { cache: 'no-cache' })
    .then((res) => (res.ok && !/text\/html/i.test(res.headers.get('content-type') || '') ? res.text() : Promise.reject()))
    .then((text) => {
      const entries = parse(text);
      if (!entries.length) return say('News will be posted here.');
      root.textContent = '';
      entries.slice(0, limit).forEach((x, i) => root.appendChild(row(x, i === 0)));
    })
    .catch(() => say(location.protocol === 'file:'
      ? 'Open this page through the site (not as a file) to see the news.'
      : 'News will be posted here.'));
})();
