<script lang="ts">
  import { textbookLine } from '../lib/plan-words';
  import type { Textbook } from '../lib/types';
  import Icon from './Icon.svelte';
  import Markdown from './Markdown.svelte';

  interface Props {
    /** Markdown with \( \) and \[ \] math, images and tables. Rendered without raw HTML. */
    prompt: string;
    /** MATH-16: a small calculator mark when a calculator is allowed. */
    calculator?: boolean;
    /** MATH-16: a "degrees" note when the card works in degrees. */
    degrees?: boolean;
    /** The textbook section under the problem (wave 2); none in a closed-book sitting. */
    textbook?: Textbook | null;
  }

  let { prompt, calculator = false, degrees = false, textbook = null }: Props = $props();
</script>

<article class="problem" aria-label="Problem" data-testid="problem">
  {#if calculator || degrees}
    <div class="marks">
      {#if calculator}
        <span class="mark" data-testid="calculator-mark" title="A calculator is allowed on this problem">
          <Icon name="calculator" size={1} /> Calculator allowed
        </span>
      {/if}
      {#if degrees}
        <span class="mark" data-testid="degrees-note" title="Angles are in degrees on this problem">
          <span class="deg" aria-hidden="true">°</span> Angles in degrees
        </span>
      {/if}
    </div>
  {/if}
  <div class="text"><Markdown source={prompt} /></div>
  {#if textbook}
    <p class="textbook" data-testid="textbook">
      <Icon name="book" size={1} />
      <span><span class="sr-only">Textbook: </span>{textbookLine(textbook)}</span>
    </p>
  {/if}
</article>

<style>
  .problem {
    max-width: var(--measure);
    margin-inline: auto;
    font-family: var(--font-text);
    font-size: var(--fs-problem);
    line-height: var(--lh-problem);
    font-variation-settings: 'opsz' 18;
  }

  .marks {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: var(--sp-1);
    margin-bottom: var(--sp-1);
    font-family: var(--font-ui);
  }

  .mark {
    display: inline-flex;
    align-items: center;
    gap: var(--sp-0);
    padding: 2px var(--sp-1);
    border: 1px solid var(--border);
    border-radius: 999px;
    color: var(--text-muted);
    font-size: var(--fs-caption);
    line-height: 1.5;
  }

  .deg {
    font-size: 1rem;
    line-height: 1;
  }

  /* A citation under the problem, in the problem's own face: where to read, not what to do. */
  .textbook {
    display: flex;
    align-items: center;
    gap: var(--sp-1);
    margin-top: var(--sp-2);
    color: var(--text-muted);
    font-size: var(--fs-small);
    font-style: italic;
    line-height: 1.4;
  }
</style>
