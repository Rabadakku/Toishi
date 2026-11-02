<script lang="ts">
  import Icon from './Icon.svelte';

  interface Props {
    kind: 'correct' | 'incorrect' | 'invalid' | 'retry';
    /** Overrides the word. */
    word?: string;
    /** Smaller, for one part of a multi-part problem. */
    compact?: boolean;
  }

  let { kind, word, compact = false }: Props = $props();

  // Color is never the only signal: every verdict has an icon and a word.
  const view = $derived(
    kind === 'correct'
      ? { icon: 'check-circle' as const, word: 'Correct' }
      : kind === 'invalid'
        ? { icon: 'alert' as const, word: 'Check your answer' }
        : kind === 'retry'
          ? { icon: 'x-circle' as const, word: 'Not quite' }
          : { icon: 'x-circle' as const, word: 'Incorrect' },
  );
</script>

<span class={`badge ${kind}`} class:compact data-verdict={kind}>
  <Icon name={view.icon} size={compact ? 1.125 : 1.5} />
  <span class="word">{word ?? view.word}</span>
</span>

<style>
  .badge {
    display: inline-flex;
    align-items: center;
    gap: var(--sp-1);
    font-weight: 600;
    font-size: 1.125rem;
  }

  .compact {
    font-size: var(--fs-small);
  }

  .correct {
    color: var(--correct);
  }

  .incorrect,
  .retry {
    color: var(--incorrect);
  }

  .invalid {
    color: var(--warning);
  }
</style>
