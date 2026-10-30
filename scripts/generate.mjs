// Draws the profile cards as SVG files, so the README needs no outside
// widgets: a neofetch-style card with an ASCII portrait, and a heatmap of the
// last year of contributions. Runs daily from .github/workflows/profile.yml.
//
//   GITHUB_TOKEN=... node scripts/generate.mjs [outDir]
//
// Writes card-dark.svg, card-light.svg, heatmap-dark.svg and heatmap-light.svg.
import { readFile, writeFile, mkdir } from 'node:fs/promises';

const LOGIN = 'stinoooo';
const BORN = '2002-10-09';
const out = process.argv[2] || 'dist';

// Everything here is said by hand and kept true; the numbers come from GitHub.
const PROFILE = {
  name: 'stijn',
  host: 'the Netherlands',
  role: 'software engineering student',
  languages: 'TypeScript, JavaScript, Rust, PHP, Python, GDScript',
  web: 'Next.js, React, Node.js, Prisma, WordPress',
  desktop: 'Tauri, Electron',
  games: 'Godot, Blender',
  data: 'PostgreSQL, MongoDB, Redis',
  ships: 'Vercel, Railway, Cloudflare, GitHub Actions',
  learning: 'Java',
  into: 'games, desktop apps, AI',
  making: 'Exit Only, Arcnode Games',
  dog: 'Banjer, head of quality assurance',
};

const THEMES = {
  dark: {
    bg: '#1f1a17', border: '#3a302a', text: '#f3e7d9', muted: '#a8968a',
    key: '#f4a261', accent: '#e9c46a', rule: '#4a3d34',
    cells: ['#2b241f', '#5c3a22', '#9a5a2c', '#d9822b', '#f6b26b'],
  },
  light: {
    bg: '#fbf5ec', border: '#eadccb', text: '#3d2f25', muted: '#8a7462',
    key: '#c4622d', accent: '#b5832a', rule: '#e6d6c3',
    cells: ['#efe4d6', '#f6cfa1', '#eda564', '#d9782f', '#a8501c'],
  },
};

const FONT = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace";
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

async function github(query) {
  const token = process.env.GITHUB_TOKEN;
  if (!token) throw new Error('GITHUB_TOKEN is not set');
  const res = await fetch('https://api.github.com/graphql', {
    method: 'POST',
    headers: { Authorization: `bearer ${token}`, 'Content-Type': 'application/json', 'User-Agent': LOGIN },
    body: JSON.stringify({ query }),
  });
  const body = await res.json();
  if (!res.ok || body.errors) throw new Error(JSON.stringify(body.errors || body));
  return body.data;
}

function uptime(today = new Date()) {
  const born = new Date(`${BORN}T00:00:00Z`);
  let years = today.getUTCFullYear() - born.getUTCFullYear();
  let months = today.getUTCMonth() - born.getUTCMonth();
  let days = today.getUTCDate() - born.getUTCDate();
  if (days < 0) {
    months -= 1;
    days += new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 0)).getUTCDate();
  }
  if (months < 0) { years -= 1; months += 12; }
  const plural = (n, w) => `${n} ${w}${n === 1 ? '' : 's'}`;
  return `${plural(years, 'year')}, ${plural(months, 'month')}, ${plural(days, 'day')}`;
}

// The portrait sits on its own dark panel in both themes: colored ASCII
// reads best light-on-dark.
const PANEL = '#1f1a17';

function card(theme, portrait, stats) {
  const t = THEMES[theme];
  const lineH = 8.6;
  const charW = 5.9;
  const artW = portrait[0].length * charW;
  const artH = portrait.length * lineH;
  const x0 = 24 + artW + 24 + 30;
  const rows = [
    ['title'],
    ['rule'],
    ['Home', PROFILE.host],
    ['Uptime', stats.uptime],
    ['Role', PROFILE.role],
    ['Into', PROFILE.into],
    ['Making', PROFILE.making],
    ['Dog', PROFILE.dog],
    ['gap'],
    ['Languages', PROFILE.languages],
    ['Web', PROFILE.web],
    ['Desktop', PROFILE.desktop],
    ['Games', PROFILE.games],
    ['Data', PROFILE.data],
    ['Ships on', PROFILE.ships],
    ['Learning', PROFILE.learning],
    ['gap'],
    ['Repos', `${stats.repos} public`],
    ['Stars', String(stats.stars)],
    ['Contributions', `${stats.contributions.toLocaleString('en-US')} in the last year`],
    ['gap'],
    ['swatches'],
  ];
  const height = Math.max(artH + 48, rows.length * 22 + 52);
  let y = 46;
  const parts = [];
  for (const [k, v] of rows) {
    if (k === 'title') {
      parts.push(`<text x="${x0}" y="${y}" font-size="15" font-weight="700"><tspan fill="${t.key}">${PROFILE.name}</tspan><tspan fill="${t.muted}">@</tspan><tspan fill="${t.key}">github</tspan></text>`);
    } else if (k === 'rule') {
      parts.push(`<line x1="${x0}" x2="${x0 + 150}" y1="${y - 8}" y2="${y - 8}" stroke="${t.rule}" stroke-width="2" stroke-linecap="round"/>`);
    } else if (k === 'swatches') {
      t.cells.slice(1).concat(t.accent).forEach((c, i) => {
        parts.push(`<rect x="${x0 + i * 26}" y="${y - 13}" width="20" height="14" rx="3" fill="${c}"/>`);
      });
    } else if (k !== 'gap') {
      parts.push(`<text x="${x0}" y="${y}" font-size="13"><tspan fill="${t.key}" font-weight="700">${esc(k)}</tspan><tspan fill="${t.muted}">: </tspan><tspan fill="${t.text}">${esc(v)}</tspan></text>`);
    }
    y += k === 'gap' ? 10 : 22;
  }
  const width = x0 + 500;
  const panelY = (height - artH - 24) / 2;
  const artText = portrait.map((row, i) => {
    const chars = row.map(([c, color]) => `<tspan fill="${color}">${c === ' ' ? '&#160;' : esc(c)}</tspan>`).join('');
    // Monospace widths differ per system; pin every row to the panel width.
    return `<text x="36" y="${(panelY + 18 + i * lineH).toFixed(1)}" textLength="${artW.toFixed(1)}" lengthAdjust="spacingAndGlyphs">${chars}</text>`;
  }).join('\n');
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(`${PROFILE.name}: ${PROFILE.role} in ${PROFILE.host}. Writes ${PROFILE.languages}. Builds with ${PROFILE.web}, ${PROFILE.desktop}, ${PROFILE.games}. Learning ${PROFILE.learning}. Into ${PROFILE.into}.`)}">
<rect x="1" y="1" width="${width - 2}" height="${height - 2}" rx="16" fill="${t.bg}" stroke="${t.border}" stroke-width="2"/>
<g font-family="${FONT}">
<rect x="24" y="${panelY.toFixed(1)}" width="${(artW + 24).toFixed(1)}" height="${(artH + 24).toFixed(1)}" rx="12" fill="${PANEL}"/>
<g font-size="9.8" font-weight="700" xml:space="preserve">${artText}</g>
${parts.join('\n')}
</g>
</svg>
`;
}

function heatmap(theme, weeks, total) {
  const t = THEMES[theme];
  const cell = 11;
  const gap = 3;
  const left = 34;
  const top = 46;
  const days = weeks.flatMap((w) => w.contributionDays.map((d) => d.contributionCount));
  // Quartiles of the days with activity, so a few huge days do not wash out the rest.
  const active = days.filter((n) => n > 0).sort((a, b) => a - b);
  const q = (p) => active[Math.min(active.length - 1, Math.floor(active.length * p))] || 1;
  const steps = [q(0.25), q(0.5), q(0.75)];
  const level = (n) => (n === 0 ? 0 : n <= steps[0] ? 1 : n <= steps[1] ? 2 : n <= steps[2] ? 3 : 4);
  const rects = [];
  const months = [];
  let lastMonth = '';
  weeks.forEach((week, wi) => {
    const first = week.contributionDays[0];
    const month = new Date(`${first.date}T00:00:00Z`).toLocaleString('en-US', { month: 'short', timeZone: 'UTC' });
    if (month !== lastMonth && new Date(`${first.date}T00:00:00Z`).getUTCDate() <= 7) {
      months.push(`<text x="${left + wi * (cell + gap)}" y="${top - 10}">${month}</text>`);
      lastMonth = month;
    }
    for (const day of week.contributionDays) {
      const d = new Date(`${day.date}T00:00:00Z`).getUTCDay();
      rects.push(`<rect x="${left + wi * (cell + gap)}" y="${top + d * (cell + gap)}" width="${cell}" height="${cell}" rx="2.5" fill="${t.cells[level(day.contributionCount)]}"><title>${day.date}: ${day.contributionCount}</title></rect>`);
    }
  });
  const width = left * 2 + weeks.length * (cell + gap) - gap;
  const height = top + 7 * (cell + gap) + 40;
  const legendX = width - left - 5 * (cell + gap) - 70;
  const legend = t.cells.map((c, i) => `<rect x="${legendX + 36 + i * (cell + gap)}" y="${height - 30}" width="${cell}" height="${cell}" rx="2.5" fill="${c}"/>`).join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img" aria-label="${total.toLocaleString('en-US')} contributions in the last year">
<rect x="1" y="1" width="${width - 2}" height="${height - 2}" rx="16" fill="${t.bg}" stroke="${t.border}" stroke-width="2"/>
<g font-family="${FONT}" font-size="10" fill="${t.muted}">
${months.join('\n')}
${rects.join('\n')}
<text x="${left}" y="${height - 20}" font-size="12"><tspan fill="${t.key}" font-weight="700">${total.toLocaleString('en-US')}</tspan><tspan fill="${t.muted}"> contributions in the last year</tspan></text>
<text x="${legendX}" y="${height - 21}">less</text>${legend}<text x="${legendX + 36 + 5 * (cell + gap) + 4}" y="${height - 21}">more</text>
</g>
</svg>
`;
}

const data = await github(`query {
  user(login: "${LOGIN}") {
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes { stargazerCount }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}`);
const user = data.user;
const calendar = user.contributionsCollection.contributionCalendar;
const stats = {
  uptime: uptime(),
  repos: user.repositories.totalCount,
  stars: user.repositories.nodes.reduce((sum, r) => sum + r.stargazerCount, 0),
  contributions: calendar.totalContributions,
};
const portrait = JSON.parse(await readFile(new URL('../assets/portrait.json', import.meta.url), 'utf8'));

await mkdir(out, { recursive: true });
for (const theme of Object.keys(THEMES)) {
  await writeFile(`${out}/card-${theme}.svg`, card(theme, portrait, stats));
  await writeFile(`${out}/heatmap-${theme}.svg`, heatmap(theme, calendar.weeks, calendar.totalContributions));
}
console.log(`Wrote cards to ${out}:`, JSON.stringify(stats));
