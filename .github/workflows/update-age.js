const fs = require("fs");
const path = require("path");

// ── Config ─────────────────────────────────────────────────────────────────
const BIRTHDATE = new Date("2002-10-09");
const README_PATH = path.join(__dirname, "../../README.md");

// ── Calculate current age ──────────────────────────────────────────────────
function calculateAge(birthdate) {
  const today = new Date();
  let age = today.getFullYear() - birthdate.getFullYear();
  const hasHadBirthdayThisYear =
    today.getMonth() > birthdate.getMonth() ||
    (today.getMonth() === birthdate.getMonth() &&
      today.getDate() >= birthdate.getDate());
  if (!hasHadBirthdayThisYear) age--;
  return age;
}

// ── Patch README ───────────────────────────────────────────────────────────
// Looks for the marker pattern: a number followed by <!-- DYNAMIC_AGE -->
// e.g.  **23-year-old**<!-- DYNAMIC_AGE: born 2002-10-09 -->
// and replaces just the number so everything else stays intact.
function patchReadme(readmePath, newAge) {
  let content = fs.readFileSync(readmePath, "utf8");

  const pattern = /\*\*(\d+)-year-old\*\*<!-- DYNAMIC_AGE: born \d{4}-\d{2}-\d{2} -->/;
  const replacement = `**${newAge}-year-old**<!-- DYNAMIC_AGE: born 2002-10-09 -->`;

  if (!pattern.test(content)) {
    console.error(
      "❌ Marker not found in README.md — make sure this string is present:\n" +
      "   **<number>-year-old**<!-- DYNAMIC_AGE: born 2002-10-09 -->"
    );
    process.exit(1);
  }

  const updated = content.replace(pattern, replacement);
  fs.writeFileSync(readmePath, updated, "utf8");
  console.log(`✅ README updated: age set to ${newAge}`);
}

// ── Run ────────────────────────────────────────────────────────────────────
const age = calculateAge(BIRTHDATE);
console.log(`🎂 Calculated age: ${age}`);
patchReadme(README_PATH, age);
