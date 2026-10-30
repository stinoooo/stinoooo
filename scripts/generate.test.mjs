import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { uptime, card, heatmap } from './generate.mjs';

const portrait = JSON.parse(await readFile(new URL('../assets/portrait.json', import.meta.url), 'utf8'));
const stats = { uptime: '24 years, 0 months, 21 days', repos: 15, stars: 5, contributions: 13900 };

test('counts the uptime from the birthday', () => {
  assert.equal(uptime(new Date('2026-10-30T12:00:00Z')), '24 years, 0 months, 21 days');
  assert.equal(uptime(new Date('2026-10-09T00:00:00Z')), '24 years, 0 months, 0 days');
  assert.equal(uptime(new Date('2026-10-08T00:00:00Z')), '23 years, 11 months, 29 days');
});

test('draws a valid card in both themes', () => {
  for (const theme of ['dark', 'light']) {
    const svg = card(theme, portrait, stats);
    assert.match(svg, /^<svg [^>]*viewBox="0 0 \d+(\.\d+)? \d+(\.\d+)?"/);
    assert.match(svg, /Banjer/);
    assert.match(svg, /13,900 in the last year/);
    assert.equal((svg.match(/<text /g) || []).length > portrait.length, true);
    // No raw markup characters leak from the portrait into the SVG.
    assert.doesNotMatch(svg.replace(/<[^>]+>/g, ''), /[<>]/);
  }
});

test('draws the heatmap with one cell per day and five levels', () => {
  const weeks = Array.from({ length: 53 }, (_, w) => ({
    contributionDays: Array.from({ length: 7 }, (_, d) => {
      const date = new Date(Date.UTC(2025, 9, 26 + w * 7 + d)).toISOString().slice(0, 10);
      return { date, contributionCount: (w * 7 + d) % 9 };
    }),
  }));
  const svg = heatmap('dark', weeks, 1234);
  assert.equal((svg.match(/<title>/g) || []).length, 53 * 7);
  assert.match(svg, /1,234/);
  assert.equal(new Set(svg.match(/fill="#[0-9a-f]{6}"><title>/g)).size, 5);
});
