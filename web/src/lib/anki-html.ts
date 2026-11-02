import type { MediaResolver } from './card-media';
import { renderMath } from './markdown';

/**
 * Imported Anki card HTML -> DOM, inert by construction (ADR-0015, ADR-0017).
 *
 * Core already sanitized the HTML at import (core/importers/anki/sanitize.py). This is the
 * second, independent pass the ADR asks for, so a damaged or hand-edited profile cannot run
 * anything either:
 * - The string is parsed by DOMParser into a document with no browsing context: scripts do
 *   not run, nothing loads, handlers never fire. Nothing from it is ever inserted as HTML.
 * - The result is built node by node with createElement from the same allow-list of tags and
 *   attributes core uses (a test compares the two lists). Dropped tags take their content with
 *   them, unknown tags are unwrapped, comments go, `on...`, `href`, `id`, `srcset` and every
 *   other attribute not on the list go.
 * - Media (`src`, `url()` in a style attribute) load only through `resolve`: a reference the
 *   card has no stored file for becomes a "[image: name]" note, never a request.
 * - `\( \)` and `\[ \]` in text become KaTeX (trust: false), as in Markdown cards.
 * The card's own CSS arrives separately (applyAnkiCss), already scoped by core to the card.
 */

export const ANKI_CARD_CLASS = 'anki-card';
export const NIGHT_CLASS = 'anki-night';
const XHTML = 'http://www.w3.org/1999/xhtml';
const MAX_DEPTH = 64;

/** True for card text the importer stored as sanitized HTML (core.importers.anki.is_anki_html). */
export function isAnkiHtml(text: string): boolean {
  return text.trimStart().startsWith(`<div class="${ANKI_CARD_CLASS}`);
}

// Keep these in step with core/importers/anki/sanitize.py (tests/app/test_anki_allowlist.py).
export const ALLOWED_TAGS: ReadonlySet<string> = new Set([
  'a', 'abbr', 'b', 'big', 'blockquote', 'br', 'caption', 'center', 'cite', 'code', 'col',
  'colgroup', 'dd', 'del', 'details', 'dfn', 'div', 'dl', 'dt', 'em', 'figcaption', 'figure',
  'font', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 'ins', 'kbd', 'li', 'mark', 'ol',
  'p', 'pre', 'q', 'rb', 'rp', 'rt', 'ruby', 's', 'samp', 'section', 'small', 'source', 'span',
  'strike', 'strong', 'sub', 'summary', 'sup', 'table', 'tbody', 'td', 'tfoot', 'th', 'thead',
  'tr', 'tt', 'u', 'ul', 'var', 'wbr', 'audio', 'video', 'article', 'aside', 'header', 'footer',
  'main', 'nav', 'label', 'time',
]);

export const DROP_WITH_CONTENT: ReadonlySet<string> = new Set([
  'script', 'style', 'iframe', 'frame', 'frameset', 'object', 'embed', 'applet', 'noscript',
  'template', 'title', 'head', 'textarea', 'select', 'button', 'svg', 'math', 'canvas', 'input',
  'option', 'dialog', 'noembed', 'noframes', 'xmp', 'plaintext',
]);

export const GLOBAL_ATTRS: ReadonlySet<string> = new Set(['class', 'style', 'title', 'lang', 'dir']);

export const TAG_ATTRS: Readonly<Record<string, readonly string[]>> = {
  img: ['src', 'alt', 'width', 'height'],
  audio: ['src', 'controls', 'loop'],
  video: ['src', 'controls', 'loop', 'width', 'height'],
  source: ['src', 'type'],
  td: ['colspan', 'rowspan', 'align', 'valign', 'width', 'height'],
  th: ['colspan', 'rowspan', 'align', 'valign', 'width', 'height'],
  table: ['border', 'cellpadding', 'cellspacing', 'width', 'align'],
  col: ['span', 'width'],
  colgroup: ['span', 'width'],
  font: ['color', 'face', 'size'],
  ol: ['start', 'type', 'reversed'],
  li: ['value'],
  div: ['align'],
  p: ['align'],
  details: ['open'],
};

const DATA_ATTR = /^data-[\p{L}_][\p{L}\p{N}_]*$/u;
const CSS_FILE = /^_anki-nt-[0-9a-f]{12}\.css$/;
const MATH = /\\\(([\s\S]+?)\\\)|\\\[([\s\S]+?)\\\]/g;
const NO_MATH_INSIDE = 'pre, code, kbd, samp';
// What a style attribute or stylesheet may not contain: script-ish values, CSS escapes (they
// hide the rest from this list) and functions that fetch by URL other than url().
const BAD_CSS =
  /expression\s*\(|javascript:|vbscript:|behavior\s*:|-moz-binding|@import|\\|(?:image-set|cross-fade|element|paint|src|attr)\s*\(|\bimage\s*\(/i;
const URL_FN = /url\(\s*(['"]?)(.*?)\1\s*\)/gi;
const REWRITTEN_URL = /url\s*\((?!"\/media\/)/i;

interface Build {
  resolve: MediaResolver;
  css: string[];
}

function allowedAttr(tag: string, name: string): boolean {
  return GLOBAL_ATTRS.has(name) || (TAG_ATTRS[tag]?.includes(name) ?? false) || DATA_ATTR.test(name);
}

/** A style attribute's declarations without anything that can run code or fetch; url(ref)
 * becomes the card's own media URL, and a declaration pointing anywhere else goes. */
export function cleanStyle(style: string, resolve: MediaResolver): string {
  const kept: string[] = [];
  for (const piece of style.split(';')) {
    const declaration = piece.trim();
    if (!declaration || BAD_CSS.test(declaration)) continue;
    let ok = true;
    const rewritten = declaration.replace(URL_FN, (_whole, _quote, ref: string) => {
      const url = resolve(ref.trim());
      if (url === null) ok = false;
      return `url("${url ?? ''}")`;
    });
    if (ok && !REWRITTEN_URL.test(rewritten)) kept.push(rewritten);
  }
  return kept.join('; ');
}

function missing(note: string): HTMLElement {
  const span = document.createElement('span');
  span.className = 'anki-missing';
  span.textContent = note;
  return span;
}

function copyAttributes(source: Element, target: HTMLElement, tag: string, build: Build, root: boolean): void {
  for (const attr of Array.from(source.attributes)) {
    const name = attr.name.toLowerCase();
    const value = attr.value;
    if (name === 'src' && (tag === 'img' || tag === 'audio' || tag === 'video' || tag === 'source')) {
      const url = build.resolve(value.trim());
      if (url !== null) target.setAttribute('src', url);
    } else if (name === 'style') {
      const style = cleanStyle(value, build.resolve);
      if (style) target.setAttribute('style', style);
    } else if (root && name === 'data-anki-css') {
      // The wrapper's own stylesheet (core adds it after sanitizing, so it is not on the list).
      if (CSS_FILE.test(value)) {
        target.setAttribute(name, value);
        build.css.push(value);
      }
    } else if (allowedAttr(tag, name)) {
      target.setAttribute(name, value);
    }
  }
}

/** An <img>/<audio>/<video> with nothing to load becomes a note; <source> without src goes. */
function finishMedia(element: HTMLElement, tag: string, original: Element): Node | null {
  if (tag === 'img' && !element.hasAttribute('src')) {
    const name = original.getAttribute('alt') || original.getAttribute('src') || '';
    return missing(name ? `[image: ${name}]` : '[image]');
  }
  if ((tag === 'audio' || tag === 'video') && !element.hasAttribute('src') && !element.querySelector('source')) {
    return missing(tag === 'audio' ? '[sound]' : '[video]');
  }
  if (tag === 'source' && !element.hasAttribute('src')) return null;
  return element;
}

function copyChildren(from: Node, to: Node, build: Build, depth: number, root: boolean): void {
  for (const child of Array.from(from.childNodes)) {
    if (child.nodeType === Node.TEXT_NODE) {
      to.appendChild(document.createTextNode(child.nodeValue ?? ''));
    } else if (child.nodeType === Node.ELEMENT_NODE) {
      copyElement(child as Element, to, build, depth, root);
    } // comments, instructions, anything else: dropped
  }
}

function copyElement(source: Element, to: Node, build: Build, depth: number, root: boolean): void {
  if (source.namespaceURI !== XHTML) return;
  const tag = source.localName;
  if (DROP_WITH_CONTENT.has(tag)) return;
  if (depth > MAX_DEPTH) {
    to.appendChild(document.createTextNode(source.textContent ?? '')); // absurdly deep: text only
    return;
  }
  if (!ALLOWED_TAGS.has(tag)) {
    copyChildren(source, to, build, depth + 1, false); // unwrap: its content stays
    return;
  }
  const element = document.createElement(tag);
  copyAttributes(source, element, tag, build, root);
  if (tag === 'audio' || tag === 'video') {
    element.setAttribute('preload', 'none'); // nothing is requested until it is played
    element.setAttribute('controls', '');
  }
  if (tag === 'img') element.setAttribute('decoding', 'async');
  copyChildren(source, element, build, depth + 1, false);
  const done = finishMedia(element, tag, source);
  if (done) to.appendChild(done);
}

/** `\( \)` and `\[ \]` in the text nodes below `root` -> KaTeX nodes. */
export function typesetMath(root: Node): void {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const texts: Text[] = [];
  for (let node = walker.nextNode(); node; node = walker.nextNode()) texts.push(node as Text);
  for (const text of texts) {
    const value = text.nodeValue ?? '';
    if (!value.includes('\\') || text.parentElement?.closest(NO_MATH_INSIDE)) continue;
    const fragment = document.createDocumentFragment();
    let last = 0;
    for (const match of value.matchAll(MATH)) {
      const inline = match[1] !== undefined;
      const tex = (match[1] ?? match[2] ?? '').replace(/ /g, ' ').trim();
      if (match.index > last) fragment.appendChild(document.createTextNode(value.slice(last, match.index)));
      fragment.appendChild(renderMath(tex, !inline));
      last = match.index + match[0].length;
    }
    if (last === 0) continue;
    if (last < value.length) fragment.appendChild(document.createTextNode(value.slice(last)));
    text.replaceWith(fragment);
  }
}

/**
 * Replace the children of `target` with the card. Returns the card's stylesheet references
 * (`_anki-nt-....css`, see applyAnkiCss). `html` is never inserted as markup.
 */
export function renderAnkiHtml(target: HTMLElement, html: string, resolve: MediaResolver): string[] {
  const parsed = new DOMParser().parseFromString(html, 'text/html');
  const build: Build = { resolve, css: [] };
  const fragment = document.createDocumentFragment();
  copyChildren(parsed.body, fragment, build, 0, true);
  typesetMath(fragment);
  target.replaceChildren(fragment);
  return build.css;
}

/** Night mode: note types' `.nightMode` CSS was mapped onto `.anki-night` on the card's wrapper. */
export function setAnkiNight(target: ParentNode, night: boolean): void {
  for (const card of target.querySelectorAll(`.${ANKI_CARD_CLASS}`)) card.classList.toggle(NIGHT_CLASS, night);
}

// ---------------------------------------------------------------- the card's CSS

const sheets = new Map<string, Promise<void>>();

/** A note type's stored CSS with its `url(_bg.png)` / `url(_font.woff)` made into media URLs. */
export function rewriteCss(css: string, resolve: MediaResolver): string {
  return css
    .replace(/@import[^;{}]*;?/gi, '')
    .replace(URL_FN, (_whole, _quote, ref: string) => {
      const url = resolve(ref.trim());
      return url === null ? 'none' : `url("${url}")`;
    });
}

function addSheet(url: string, resolve: MediaResolver): Promise<void> {
  let ready = sheets.get(url);
  if (!ready) {
    ready = fetch(url, { credentials: 'omit' })
      .then((reply) => (reply.ok ? reply.text() : ''))
      .then((css) => {
        if (!css) return;
        // Core scoped every selector to `.anki-nt-<hash>`; the rules cannot reach the app.
        const style = document.createElement('style');
        style.setAttribute('data-anki-css', url);
        style.textContent = rewriteCss(css, resolve);
        document.head.appendChild(style);
      })
      .catch(() => {
        sheets.delete(url); // not stored yet or the server is busy: try again with the next card
      });
    sheets.set(url, ready);
  }
  return ready;
}

/** The longest a card is held back for its stylesheet. */
const CSS_WAIT_MS = 3000;

/** Load the stylesheets a card names, once each. Null when there is nothing to wait for. */
export function applyAnkiCss(refs: readonly string[], resolve: MediaResolver): Promise<void> | null {
  const waiting: Promise<void>[] = [];
  for (const ref of new Set(refs)) {
    const url = resolve(ref);
    if (url !== null) waiting.push(addSheet(url, resolve));
  }
  if (!waiting.length) return null;
  const limit = new Promise<void>((done) => window.setTimeout(done, CSS_WAIT_MS));
  return Promise.race([Promise.all(waiting).then(() => undefined), limit]);
}
