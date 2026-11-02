<script lang="ts">
  import Button from './Button.svelte';

  interface Props {
    kind: 'manual' | 'idle';
    onresume: () => void;
  }

  let { kind, onresume }: Props = $props();
  let card: HTMLElement | undefined = $state();

  $effect(() => {
    card?.querySelector('button')?.focus();
  });
</script>

<div class="overlay" role="group" aria-label="Paused" data-testid="pause-overlay">
  <div class="card" bind:this={card}>
    <h2>Paused</h2>
    <p class="muted">
      {#if kind === 'idle'}
        No activity for a while, so the clock stopped. Time since the "Still working?" note was not counted.
      {:else}
        The clock is stopped and the problem is hidden. Take your time.
      {/if}
    </p>
    <Button variant="primary" shortcut="Esc" data-testid="resume-button" onclick={onresume}>
      Resume
    </Button>
  </div>
</div>

<style>
  .overlay {
    position: absolute;
    inset: 0;
    z-index: 10;
    display: grid;
    place-items: center;
    padding: var(--sp-3);
    background: var(--scrim);
  }

  .card {
    display: grid;
    justify-items: center;
    gap: var(--sp-2);
    max-width: 24rem;
    padding: var(--sp-4);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--surface);
    box-shadow: var(--shadow);
    text-align: center;
  }

  p {
    font-size: var(--fs-small);
  }
</style>
