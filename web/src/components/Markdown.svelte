<script lang="ts">
  import { getContext, untrack } from 'svelte';
  import { applyAnkiCss, isAnkiHtml, renderAnkiHtml, setAnkiNight } from '../lib/anki-html';
  import {
    CARD_CONTEXT,
    loadCardMedia,
    mediaResolver,
    peekCardMedia,
    type CardContext,
    type MediaMap,
  } from '../lib/card-media';
  import { resolveFigure } from '../lib/figures';
  import { renderInlineMarkdown, renderMarkdown } from '../lib/markdown';
  import { isNight } from '../lib/night.svelte';

  interface Props {
    source: string;
    /** One line of inline Markdown, no paragraph wrapper (labels, options). */
    inline?: boolean;
  }

  let { source, inline = false }: Props = $props();
  let host: HTMLElement | undefined = $state();

  // Text of an imported Anki card is sanitized HTML (ADR-0015), drawn by anki-html.ts; all
  // other text is Markdown. Either may show images: their files come from the open card.
  const card = getContext<CardContext | undefined>(CARD_CONTEXT);
  const anki = $derived(isAnkiHtml(source));
  const cardId = $derived(card?.cardId ?? null);
  const showsMedia = $derived(anki || /!\[[^\]]*\]\(/.test(source));
  let files: MediaMap | undefined = $state();
  // Text with images waits for its card's media, so it never shows a note where a picture
  // is about to be (and never draws one card's text with another card's files).
  const waiting = $derived(showsMedia && cardId !== null && files === undefined);

  $effect(() => {
    const id = showsMedia ? cardId : null;
    const cached = id === null ? undefined : peekCardMedia(id);
    files = cached;
    if (id === null || cached) return;
    let live = true;
    void loadCardMedia(id).then((loaded) => {
      if (live) files = loaded;
    });
    return () => {
      live = false;
    };
  });

  $effect(() => {
    if (!host) return;
    if (waiting) {
      host.replaceChildren();
      return;
    }
    const fromCard = mediaResolver(files);
    if (anki) {
      const sheets = renderAnkiHtml(host, source, fromCard);
      setAnkiNight(host, untrack(isNight));
      // Hold the card back until its stylesheet is in, so it never flashes unstyled.
      const waiting = applyAnkiCss(sheets, fromCard);
      if (!waiting) {
        host.style.visibility = '';
        return;
      }
      const shown = host;
      shown.style.visibility = 'hidden';
      let live = true;
      void waiting.then(() => {
        if (live) shown.style.visibility = '';
      });
      return () => {
        live = false;
        shown.style.visibility = '';
      };
    }
    const options = { resolveImage: (src: string) => resolveFigure(src) ?? fromCard(src) };
    if (inline) renderInlineMarkdown(host, source, options);
    else renderMarkdown(host, source, options);
  });

  // A theme change only toggles the class: the card is not drawn again.
  $effect(() => {
    const night = isNight();
    if (host && anki) setAnkiNight(host, night);
  });
</script>

{#if anki}
  <div class="anki-host" bind:this={host}></div>
{:else if inline}
  <span class="md inline" bind:this={host}></span>
{:else}
  <div class="md" bind:this={host}></div>
{/if}

<style>
  .md > :global(:first-child) {
    margin-top: 0;
  }

  .md > :global(:last-child) {
    margin-bottom: 0;
  }

  .md :global(p),
  .md :global(ul),
  .md :global(ol),
  .md :global(blockquote),
  .md :global(pre),
  .md :global(.md-table) {
    margin: 0 0 var(--sp-2);
  }

  .md :global(ul),
  .md :global(ol) {
    padding-inline-start: var(--sp-3);
  }

  .md :global(li + li) {
    margin-top: var(--sp-0);
  }

  .md :global(h3),
  .md :global(h4),
  .md :global(h5),
  .md :global(h6) {
    margin: var(--sp-3) 0 var(--sp-1);
    font-family: var(--font-ui);
    font-size: 1rem;
  }

  .md :global(blockquote) {
    padding-inline-start: var(--sp-2);
    border-inline-start: 3px solid var(--border);
    color: var(--text-muted);
  }

  .md :global(code) {
    padding: 0 0.3em;
    border-radius: 4px;
    background: var(--surface-sunken);
    font-family: var(--font-mono);
    font-size: 0.875em;
  }

  .md :global(pre) {
    padding: var(--sp-2);
    border-radius: var(--radius-sm);
    background: var(--surface-sunken);
    overflow-x: auto;
  }

  .md :global(pre code) {
    padding: 0;
    background: none;
  }

  .md :global(.md-link) {
    color: var(--accent);
    text-decoration: underline;
    text-underline-offset: 3px;
  }

  .md :global(.md-table) {
    overflow-x: auto;
  }

  .md :global(table) {
    border-collapse: collapse;
    font-variant-numeric: tabular-nums;
  }

  .md :global(th),
  .md :global(td) {
    padding: var(--sp-1) var(--sp-2);
    border: 1px solid var(--border);
    text-align: start;
  }

  .md :global(th) {
    background: var(--surface-sunken);
    font-weight: 600;
  }

  .md :global([data-align='right']) {
    text-align: end;
  }

  .md :global([data-align='center']) {
    text-align: center;
  }

  .md :global(img) {
    display: block;
    max-width: 100%;
    height: auto;
    margin: var(--sp-2) auto;
    border-radius: var(--radius-sm);
    filter: var(--image-filter);
  }

  .md :global(.md-missing-image) {
    color: var(--text-muted);
    font-style: italic;
  }

  .md :global(.math-display) {
    overflow-x: auto;
    overflow-y: hidden;
  }

  /* An imported Anki card: its own CSS (scoped by core to the card) does the styling. The host
     only keeps whatever that CSS does, including position: fixed, inside the card's box. */
  .anki-host {
    contain: layout;
    overflow-x: auto;
    overflow-y: hidden;
    max-width: 100%;
  }

  /* Defaults with no specificity at all, so a note type's CSS always wins. */
  :global(:where(.anki-card) :where(img, video)) {
    max-width: 100%;
    height: auto;
  }

  :global(:where(.anki-card) :where(img)) {
    filter: var(--image-filter);
  }

  :global(:where(.anki-card) :where(audio)) {
    max-width: 100%;
  }

  :global(:where(.anki-card) :where(.cloze)) {
    color: var(--accent);
    font-weight: 600;
  }

  :global(:where(.anki-card) :where(.anki-missing)) {
    color: var(--text-muted);
    font-style: italic;
  }

  :global(:where(.anki-card) :where(.math-display)) {
    overflow-x: auto;
    overflow-y: hidden;
  }
</style>
