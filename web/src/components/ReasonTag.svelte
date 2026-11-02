<script lang="ts">
  import type { Reason } from '../lib/types';
  import Icon from './Icon.svelte';
  import Markdown from './Markdown.svelte';

  interface Props {
    reason: Reason;
    open: boolean;
    ontoggle: (open: boolean) => void;
    disabled?: boolean;
  }

  let { reason, open, ontoggle, disabled = false }: Props = $props();
  let root: HTMLElement | undefined = $state();

  function closeOnOutside(event: MouseEvent): void {
    if (open && root && event.target instanceof Node && !root.contains(event.target)) ontoggle(false);
  }
</script>

<svelte:window onclick={closeOnOutside} />

<div class="reason" bind:this={root}>
  <button
    type="button"
    class="tag"
    aria-expanded={open}
    aria-controls="why-popover"
    aria-label={`${reason.label}. Why is this here?`}
    {disabled}
    data-testid="reason-tag"
    onclick={() => ontoggle(!open)}
  >
    <span>{reason.label}</span>
    <Icon name="help" size={1} />
  </button>
  {#if open}
    <!-- Non-modal: it never blocks the problem, and Esc or a click elsewhere closes it. -->
    <div id="why-popover" class="popover" role="group" aria-label="Why is this here?" data-testid="why-popover">
      <strong>Why is this here?</strong>
      <Markdown source={reason.why} />
    </div>
  {/if}
</div>

<style>
  .reason {
    position: relative;
  }

  .tag {
    display: inline-flex;
    align-items: center;
    gap: var(--sp-0);
    min-height: 32px;
    padding: 0 var(--sp-1) 0 var(--sp-2);
    border: 1px solid var(--border);
    border-radius: 999px;
    background: transparent;
    color: var(--text-muted);
    font-size: var(--fs-small);
    font-weight: 500;
    transition: background-color var(--dur) ease-out;
  }

  .tag:hover:not(:disabled) {
    background: var(--surface-sunken);
    color: var(--text);
  }

  .popover {
    position: absolute;
    z-index: 5;
    inset-inline-start: 50%;
    top: calc(100% + var(--sp-1));
    display: grid;
    gap: var(--sp-0);
    width: min(22rem, 80vw);
    padding: var(--sp-2);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--surface);
    box-shadow: var(--shadow);
    color: var(--text);
    font-size: var(--fs-small);
    transform: translateX(-50%);
  }
</style>
