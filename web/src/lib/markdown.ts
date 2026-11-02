import katex from 'katex';
import MarkdownIt, { type MarkdownIt as MarkdownItInstance, type StateInline, type Token } from 'markdown-it';

/**
 * Problem Markdown -> DOM, safe by construction.
 *
 * - markdown-it runs with `html: false`, so raw HTML is plain text to it, and its output is a
 *   token list, not an HTML string. This module builds DOM nodes from that list with
 *   createElement / textContent and a fixed set of tag names. There is no innerHTML and no
 *   `{@html}` anywhere for author-supplied text.
 * - The only HTML that is ever parsed from a string is KaTeX's own output for `\( \)` and
 *   `\[ \]` math, rendered with `trust: false` (no \href, \url or \includegraphics).
 * - Links never navigate (the app is offline and a navigation would replace the page); they
 *   are shown as styled text.
 * - Images load only through `resolveImage`, which maps a relative path to a bundled file;
 *   any scheme (http:, data:, javascript:, ...) or protocol-relative URL is refused.
 */

export interface RenderOptions {
  /** Map an image path from the Markdown to a URL on this origin, or null to refuse it. */
  resolveImage?: (src: string) => string | null;
}

const md = new MarkdownIt({ html: false, linkify: false, typographer: false, breaks: false });
md.use(mathDelimiters);

/** `\( ... \)` inline math and `\[ ... \]` display math, before markdown-it's escape rule eats the backslash. */
function mathDelimiters(instance: MarkdownItInstance): void {
  instance.inline.ruler.before('escape', 'math_delimited', (state: StateInline, silent: boolean) => {
    const src = state.src;
    const start = state.pos;
    if (src.charCodeAt(start) !== 0x5c) return false; // backslash
    const opener = src[start + 1];
    const closer = opener === '(' ? '\\)' : opener === '[' ? '\\]' : null;
    if (closer === null) return false;
    const end = src.indexOf(closer, start + 2);
    if (end < 0) return false;
    if (!silent) {
      const token = state.push(opener === '(' ? 'math_inline' : 'math_display', 'math', 0);
      token.content = src.slice(start + 2, end).trim();
    }
    state.pos = end + 2;
    return true;
  });
}

const CONTAINER_TAGS: Record<string, string> = {
  paragraph: 'p',
  blockquote: 'blockquote',
  bullet_list: 'ul',
  ordered_list: 'ol',
  list_item: 'li',
  table: 'table',
  thead: 'thead',
  tbody: 'tbody',
  tr: 'tr',
  th: 'th',
  td: 'td',
  strong: 'strong',
  em: 'em',
  s: 's',
};

/** KaTeX output for one formula, as a DOM node (also used for math inside imported Anki HTML). */
export function renderMath(tex: string, display: boolean): HTMLElement {
  const host = document.createElement(display ? 'div' : 'span');
  host.className = display ? 'math math-display' : 'math math-inline';
  try {
    katex.render(tex, host, {
      displayMode: display,
      throwOnError: false,
      trust: false,
      strict: 'ignore',
      maxExpand: 1000,
      output: 'htmlAndMathml',
    });
  } catch {
    host.textContent = tex; // never let one bad formula blank the problem
  }
  return host;
}

function renderImage(token: Token, options: RenderOptions): Node {
  const src = String(token.attrGet('src') ?? '');
  const alt = token.content;
  const url = options.resolveImage?.(src) ?? null;
  if (url === null) {
    const missing = document.createElement('span');
    missing.className = 'md-missing-image';
    missing.textContent = alt ? `[figure: ${alt}]` : '[figure]';
    return missing;
  }
  const img = document.createElement('img');
  img.src = url;
  img.alt = alt;
  img.decoding = 'async';
  return img;
}

function appendTokens(parent: Node, tokens: Token[], options: RenderOptions): void {
  const stack: Node[] = [parent];
  const top = (): Node => stack[stack.length - 1] ?? parent;
  const open = (tag: string, token?: Token): void => {
    const element = document.createElement(tag);
    if (token?.type === 'ordered_list_open') {
      const start = String(token.attrGet('start') ?? '');
      if (/^\d{1,6}$/.test(start)) element.setAttribute('start', start);
    }
    if (token && (token.type === 'th_open' || token.type === 'td_open')) {
      const style = String(token.attrGet('style') ?? '');
      const align = /text-align:(left|center|right)/.exec(style)?.[1];
      if (align) element.setAttribute('data-align', align);
    }
    top().appendChild(element);
    stack.push(element);
  };
  const close = (): void => {
    if (stack.length > 1) stack.pop();
  };

  for (const token of tokens) {
    const { type } = token;
    if (type.endsWith('_open')) {
      const base = type.slice(0, -5);
      if (base === 'paragraph' && token.hidden) {
        stack.push(top()); // tight list: no <p>; the matching close pops this copy
      } else if (base === 'heading') {
        const level = Math.min(6, Math.max(3, Number(token.tag.slice(1)) + 2));
        open(`h${level}`);
      } else if (base === 'link') {
        open('span'); // never navigates
        (top() as HTMLElement).className = 'md-link';
      } else if (base === 'table') {
        const wrap = document.createElement('div');
        wrap.className = 'md-table';
        top().appendChild(wrap);
        stack.push(wrap);
        open('table');
      } else {
        const tag = CONTAINER_TAGS[base];
        if (tag) open(tag, token);
        else stack.push(top()); // unknown container: keep its children, drop the wrapper
      }
    } else if (type.endsWith('_close')) {
      if (type === 'table_close') close();
      close();
    } else {
      switch (type) {
        case 'inline':
          appendTokens(top(), token.children ?? [], options);
          break;
        case 'text':
          top().appendChild(document.createTextNode(token.content));
          break;
        case 'softbreak':
          top().appendChild(document.createTextNode(' '));
          break;
        case 'hardbreak':
          top().appendChild(document.createElement('br'));
          break;
        case 'code_inline': {
          const code = document.createElement('code');
          code.textContent = token.content;
          top().appendChild(code);
          break;
        }
        case 'fence':
        case 'code_block': {
          const pre = document.createElement('pre');
          const code = document.createElement('code');
          code.textContent = token.content;
          pre.appendChild(code);
          top().appendChild(pre);
          break;
        }
        case 'hr':
          top().appendChild(document.createElement('hr'));
          break;
        case 'image':
          top().appendChild(renderImage(token, options));
          break;
        case 'math_inline':
          top().appendChild(renderMath(token.content, false));
          break;
        case 'math_display':
          top().appendChild(renderMath(token.content, true));
          break;
        default:
          // Anything unexpected (html_block and html_inline are off) shows as text.
          if (token.content) top().appendChild(document.createTextNode(token.content));
      }
    }
  }
}

/** Replace the children of `target` with the rendered Markdown. */
export function renderMarkdown(target: HTMLElement, source: string, options: RenderOptions = {}): void {
  const fragment = document.createDocumentFragment();
  appendTokens(fragment, md.parse(source, {}), options);
  target.replaceChildren(fragment);
}

/** Same, for a single line of inline Markdown (labels, options): no <p> wrapper. */
export function renderInlineMarkdown(target: HTMLElement, source: string, options: RenderOptions = {}): void {
  const fragment = document.createDocumentFragment();
  appendTokens(fragment, md.parseInline(source, {}), options);
  target.replaceChildren(fragment);
}
