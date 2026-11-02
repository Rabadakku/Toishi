<script lang="ts">
  import { formatMs } from '../lib/format';
  import type { SittingView } from '../lib/types';
  import Icon from './Icon.svelte';

  interface Props {
    sitting: SittingView;
    /** This item's active time so far, from the study clock (pauses left out). */
    elapsedMs: () => number;
  }

  let { sitting, elapsedMs }: Props = $props();

  // The block's time runs on screen, like an exam clock (design v1.3); it never cuts anything off.
  let tick = $state(0);
  $effect(() => {
    const timer = window.setInterval(() => (tick += 1), 1_000);
    return () => window.clearInterval(timer);
  });

  const used = $derived.by(() => {
    void tick;
    return sitting.block_elapsed_ms + elapsedMs();
  });
  const over = $derived(used > sitting.time_limit_ms);
</script>

<section class="sitting" aria-label="Closed-book sitting" data-testid="sitting-banner">
  <div class="head">
    <strong>Closed-book sitting</strong>
    <span class="tabular" data-testid="sitting-index">Problem {sitting.index} of {sitting.total}</span>
  </div>
  <p class="rule">Notes and textbook away. Nothing stops at the time limit.</p>
  <p class="time tabular" class:over data-testid="sitting-time">
    <Icon name={over ? 'alert' : 'clock'} size={1} />
    <span
      >Time on this block: <span data-testid="sitting-used">{formatMs(used)}</span> of
      <span data-testid="sitting-limit">{formatMs(sitting.time_limit_ms)}</span></span
    >
    {#if over}<strong data-testid="sitting-over">Over the limit</strong>{/if}
  </p>
</section>

<style>
  .sitting {
    display: grid;
    gap: var(--sp-0);
    max-width: var(--measure);
    margin: 0 auto var(--sp-3);
    padding: var(--sp-1) var(--sp-2);
    border: 1px solid var(--border);
    border-inline-start: 4px solid var(--accent);
    border-radius: var(--radius-sm);
    background: var(--surface);
    font-size: var(--fs-small);
  }

  .head {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: var(--sp-1);
    font-size: var(--fs-body);
  }

  .rule {
    color: var(--text-muted);
  }

  .time {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--sp-1);
  }

  /* Past the limit the block can no longer pass on time; the icon and the words say so, not only the color. */
  .time.over {
    color: var(--warning);
  }
</style>
