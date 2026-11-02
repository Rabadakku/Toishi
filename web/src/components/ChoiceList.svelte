<script lang="ts">
  import type { ChoiceItem } from '../lib/study-session.svelte';
  import Icon from './Icon.svelte';
  import Markdown from './Markdown.svelte';

  interface Props {
    choices: ChoiceItem[];
    selected: string[];
    multiple?: boolean;
    disabled?: boolean;
    label: string;
    /** Marks the right and wrong picks after grading. */
    correctIds?: string[] | null;
    onpick: (id: string) => void;
  }

  let { choices, selected, multiple = false, disabled = false, label, correctIds = null, onpick }: Props = $props();
</script>

<div class="choices" role={multiple ? 'group' : 'radiogroup'} aria-label={label} data-testid="choices">
  {#each choices as choice, i (choice.id)}
    {@const on = selected.includes(choice.id)}
    <button
      type="button"
      class="choice"
      class:on
      class:right={correctIds?.includes(choice.id)}
      role={multiple ? 'checkbox' : 'radio'}
      aria-checked={on}
      {disabled}
      data-testid={`choice-${choice.id}`}
      onclick={() => onpick(choice.id)}
    >
      <kbd aria-hidden="true">{i + 1}</kbd>
      <span class="text"><Markdown source={choice.text} inline /></span>
      {#if correctIds?.includes(choice.id)}
        <span class="status"><Icon name="check-circle" size={1.125} /> Correct choice</span>
      {:else if on}
        <Icon name="check" size={1.125} />
      {/if}
    </button>
  {/each}
</div>

<style>
  .choices {
    display: grid;
    gap: var(--sp-1);
  }

  .choice {
    display: flex;
    align-items: center;
    gap: var(--sp-2);
    min-height: 48px;
    padding: var(--sp-1) var(--sp-2);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--surface);
    color: var(--text);
    font-family: var(--font-text);
    font-size: 1.0625rem;
    text-align: start;
    transition: border-color var(--dur) ease-out;
  }

  .choice:hover:not(:disabled) {
    border-color: var(--text-muted);
  }

  .choice:disabled {
    cursor: default;
  }

  .choice.on {
    border-color: var(--accent);
    background: var(--selection);
  }

  .choice.right {
    border-color: var(--correct);
    background: var(--surface);
  }

  .text {
    flex: 1;
  }

  .status {
    display: inline-flex;
    align-items: center;
    gap: var(--sp-0);
    color: var(--correct);
    font-family: var(--font-ui);
    font-size: var(--fs-small);
    font-weight: 600;
  }
</style>
