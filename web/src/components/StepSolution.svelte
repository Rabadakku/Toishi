<script lang="ts">
  import type { StepView } from '../lib/types';
  import Icon from './Icon.svelte';
  import Markdown from './Markdown.svelte';

  interface Props {
    steps: StepView[];
    /** Find-the-error: steps are buttons, and the student picks the wrong one. */
    pickable?: boolean;
    picked?: number | null;
    /** Find-the-error: the step that is actually wrong. */
    flagged?: number | null;
    /** Key hint chips by step number (the digit that picks it). */
    keys?: Record<number, string>;
    onpick?: (index: number) => void;
    label?: string;
    /** Skill names are section labels: hidden until the problem has been answered. */
    showSkill?: boolean;
  }

  let {
    steps,
    pickable = false,
    picked = null,
    flagged = null,
    keys = {},
    onpick,
    label = 'Worked solution',
    showSkill = true,
  }: Props = $props();
</script>

<ol class="steps" aria-label={label} data-testid="steps">
  {#each steps as step (step.number)}
    <li
      class="step"
      class:picked={picked === step.number}
      class:flagged={flagged === step.number}
      data-step={step.number}
    >
      <div class="head">
        {#if pickable}
          <button
            type="button"
            class="pick"
            aria-pressed={picked === step.number}
            data-testid={`step-${step.number}`}
            onclick={() => onpick?.(step.number)}
          >
            <span class="num">Step {step.number}</span>
            <span class="label">{step.label}</span>
            {#if picked === step.number}<Icon name="check" size={1} />{/if}
          </button>
        {:else}
          <span class="num">Step {step.number}</span>
          <span class="label">{step.label}</span>
        {/if}
        {#if showSkill && step.skill_name}<span class="skill">{step.skill_name}</span>{/if}
        {#if flagged === step.number}
          <span class="tag wrong-tag"><Icon name="x-circle" size={1} /> Wrong step</span>
        {/if}
        {#if keys[step.number]}<kbd aria-hidden="true">{keys[step.number]}</kbd>{/if}
      </div>
      <div class="body"><Markdown source={step.body_md} /></div>
    </li>
  {/each}
</ol>

<style>
  .steps {
    display: grid;
    gap: var(--sp-1);
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .step {
    position: relative;
    padding: var(--sp-1) var(--sp-2);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--surface);
    transition: border-color var(--dur) ease-out;
  }

  .step.picked {
    border-color: var(--accent);
    background: var(--selection);
  }

  .step.flagged {
    border-color: var(--incorrect);
    border-inline-start-width: 4px;
  }

  .head {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--sp-1);
    font-size: var(--fs-small);
  }

  .num {
    color: var(--text-muted);
    font-weight: 600;
    font-variant-numeric: tabular-nums;
  }

  .label {
    font-weight: 600;
  }

  .skill {
    margin-inline-start: auto;
    color: var(--text-muted);
  }

  .pick {
    display: inline-flex;
    align-items: center;
    gap: var(--sp-1);
    padding: 0;
    border: 0;
    background: none;
    font-size: inherit;
    text-align: start;
  }

  /* The whole row is the tap target. */
  .pick::after {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: var(--radius-sm);
  }

  .pick:focus-visible {
    outline: none;
  }

  .pick:focus-visible::after {
    outline: var(--focus-width) solid var(--accent);
    outline-offset: 2px;
  }

  .step:has(.pick):hover:not(.picked) {
    border-color: var(--text-muted);
  }

  .tag {
    display: inline-flex;
    align-items: center;
    gap: var(--sp-0);
    padding: 0 var(--sp-1);
    border: 1px solid currentColor;
    border-radius: 999px;
    font-size: var(--fs-caption);
    font-weight: 600;
  }

  .wrong-tag {
    color: var(--incorrect);
  }

  .body {
    padding-top: var(--sp-0);
    font-family: var(--font-text);
    font-size: 1rem;
    line-height: 1.5;
  }
</style>
