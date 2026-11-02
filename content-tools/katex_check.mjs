// Renders math with KaTeX in strict mode; prints the failures as JSON.
// usage: node katex_check.mjs <katex package dir>  < items.jsonl
//   each input line: {"id": "...", "tex": "...", "display": false}
//   output: [{"id": "...", "error": "..."}, ...]   (an empty list when everything renders)
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";

const require = createRequire(import.meta.url);
const katex = require(process.argv[2]);
const failures = [];
for (const line of readFileSync(0, "utf8").split("\n")) {
  if (!line.trim()) continue;
  const item = JSON.parse(line);
  try {
    katex.renderToString(item.tex, {
      displayMode: Boolean(item.display),
      throwOnError: true,
      strict: "error",
      trust: false,
    });
  } catch (error) {
    failures.push({ id: item.id, error: String(error && error.message ? error.message : error) });
  }
}
process.stdout.write(JSON.stringify(failures));
