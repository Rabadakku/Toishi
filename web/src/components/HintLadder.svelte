<script lang="ts">
  import type { HintReveal } from '../lib/types';
  import Icon from './Icon.svelte';
  import Markdown from './Markdown.svelte';

  let { hints }: { hints: HintReveal[] } = $props();

  const last = $derived(hints[hints.length - 1]);
</script>

{#if hints.length > 0}
  <section class="ladder" aria-label="Hints" data-testid="hints">
    {#each hints as hint (hint.index)}
      <div class="hint" data-testid="hint">
        <div class="meta"><Icon name="hint" size={1} /> Hint {hint.index} of {hint.total}</div>
        <div class="text"><Markdown source={hint.text} /></div>
      </div>
    {/each}
    {#if last}
      <p class="effect" role="status">
        {#if last.rating_effect === 'again'}
          That hint gave the first step, so this problem will count as a miss and come back later.
        {:else}
          With a hint, this problem counts as Hard at best.
        {/if}
      </p>
    {/if}
  </section>
{/if}

<style>
  .ladder {
    display: grid;
    gap: var(--sp-1);
    max-width: var(--measure);
    margin: var(--sp-3) auto 0;
  }

  .hint {
    padding: var(--sp-1) var(--sp-2);
    border-inline-start: 3px solid var(--accent);
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    background: var(--surface-sunken);
  }

  .meta {
    display: flex;
    align-items: center;
    gap: var(--sp-0);
    color: var(--text-muted);
    font-size: var(--fs-caption);
    font-weight: 600;
  }

  .text {
    font-family: var(--font-text);
    font-size: 1rem;
  }

  .effect {
    margin: 0;
    color: var(--text-muted);
    font-size: var(--fs-small);
  }
</style>
