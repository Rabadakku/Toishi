<script lang="ts">
  import { PICKER_OPTIONS } from '../lib/study-session.svelte';
  import type { Diagnosis, StepView, WentWrongChoice } from '../lib/types';
  import StepSolution from './StepSolution.svelte';

  interface Props {
    steps: StepView[];
    picked: { choice: WentWrongChoice; step: number | null } | null;
    diagnosis: Diagnosis | null;
    onpick: (choice: WentWrongChoice, step: number | null) => void;
    /** The picker itself, so the study screen can move the keyboard and the view to it. */
    el?: HTMLElement;
  }

  let { steps, picked, diagnosis, onpick, el = $bindable() }: Props = $props();

  const pickedStep = $derived(picked?.choice === 'step' ? picked.step : picked?.choice === 'setup' ? 0 : null);
  // Step 0 is "set up"; when the solution lists it, the setup option is its tap.
  const others = $derived(PICKER_OPTIONS.filter((option) => option.choice !== 'setup' || !steps.some((s) => s.number === 0)));
  const keys = $derived<Record<number, string>>(steps.some((s) => s.number === 0) ? { 0: '1' } : {});
</script>

<section class="wrong" aria-labelledby="wrong-title" tabindex="-1" bind:this={el} data-testid="what-went-wrong">
  <h3 id="wrong-title">What went wrong?</h3>
  {#if steps.length > 0}
    <p class="lead muted">
      Tap the first step where your work went differently. A tap is a hint to the app, not a verdict.
    </p>

    <StepSolution
    {steps}
    pickable={picked === null}
    picked={pickedStep}
    {keys}
    label="Which step first went differently?"
    onpick={(index) => onpick('step', index)}
    />

    <p class="or muted">Or it was something else</p>
  {/if}
  <div class="others" role="group" aria-label="Other things that went wrong">
    {#each others as option (option.n)}
      <button
        type="button"
        class="option"
        class:chosen={picked?.choice === option.choice}
        disabled={picked !== null}
        aria-pressed={picked?.choice === option.choice}
        data-testid={`wrong-${option.choice}`}
        onclick={() => onpick(option.choice, null)}
      >
        <span class="text">
          <span class="name">{option.label}</span>
          {#if option.hint}<span class="hint muted">{option.hint}</span>{/if}
        </span>
        <kbd aria-hidden="true">{option.n}</kbd>
      </button>
    {/each}
  </div>

  {#if diagnosis}
    <p class="follow" role="status" data-testid="follow-up">{diagnosis.follow_up}</p>
  {:else}
    <p class="muted small">Pick one to continue. "Can't tell" is fine.</p>
  {/if}
</section>

<style>
  .wrong {
    display: grid;
    gap: var(--sp-2);
    outline: none;
  }

  .lead,
  .or,
  .small {
    font-size: var(--fs-small);
  }

  .others {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
    gap: var(--sp-1);
  }

  .option {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--sp-1);
    min-height: 48px;
    padding: var(--sp-1) var(--sp-2);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--surface);
    color: var(--text);
    text-align: start;
    transition: border-color var(--dur) ease-out;
  }

  .option:hover:not(:disabled) {
    border-color: var(--text-muted);
  }

  .option:disabled {
    cursor: default;
  }

  .option.chosen {
    border-color: var(--accent);
    background: var(--selection);
  }

  .text {
    display: grid;
  }

  .name {
    font-weight: 600;
    font-size: var(--fs-small);
  }

  .hint {
    font-size: var(--fs-caption);
  }

  .follow {
    color: var(--text);
    font-size: var(--fs-small);
  }
</style>
