<script lang="ts">
  import type { Snippet } from 'svelte';
  import type { HTMLButtonAttributes } from 'svelte/elements';
  import type { IconName } from '../lib/icons';
  import Icon from './Icon.svelte';

  interface Props extends HTMLButtonAttributes {
    variant?: 'primary' | 'secondary' | 'quiet';
    /** Icon shown before the label. */
    icon?: IconName;
    /** The keyboard shortcut for this button, shown as a small key hint. */
    shortcut?: string;
    children: Snippet;
  }

  let { variant = 'secondary', icon, shortcut, children, type = 'button', ...rest }: Props = $props();
</script>

<button class={`btn ${variant}`} {type} {...rest}>
  {#if icon}<Icon name={icon} size={1.125} />{/if}
  <span>{@render children()}</span>
  {#if shortcut}<span class="key" aria-hidden="true">{shortcut}</span>{/if}
</button>

<style>
  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--sp-1);
    min-height: 40px;
    padding: 0 var(--sp-2);
    border: 1px solid transparent;
    border-radius: var(--radius-sm);
    font-size: 0.9375rem;
    font-weight: 500;
    line-height: 1;
    white-space: nowrap;
    transition:
      background-color var(--dur) ease-out,
      border-color var(--dur) ease-out,
      color var(--dur) ease-out;
  }

  .primary {
    background: var(--accent);
    color: var(--on-accent);
  }

  .primary:hover:not(:disabled) {
    background: var(--accent-strong);
  }

  .secondary {
    background: var(--surface);
    border-color: var(--border);
    color: var(--text);
  }

  .secondary:hover:not(:disabled) {
    background: var(--surface-sunken);
  }

  .quiet {
    background: transparent;
    color: var(--text-muted);
  }

  .quiet:hover:not(:disabled) {
    background: var(--surface-sunken);
    color: var(--text);
  }

  .btn:disabled {
    opacity: 0.45;
    cursor: default;
  }

  .key {
    padding: 2px 6px;
    border: 1px solid currentColor;
    border-radius: 6px;
    font-size: var(--fs-caption);
    font-weight: 500;
    line-height: 1.2;
    opacity: 0.7;
  }
</style>
