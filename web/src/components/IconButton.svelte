<script lang="ts">
  import type { HTMLButtonAttributes } from 'svelte/elements';
  import type { IconName } from '../lib/icons';
  import Icon from './Icon.svelte';

  interface Props extends HTMLButtonAttributes {
    /** The accessible name. Required: an icon alone says nothing to a screen reader. */
    label: string;
    icon: IconName;
    /** Toggle buttons: whether it is currently on. */
    pressed?: boolean;
    /** Shortcut, appended to the tooltip. */
    shortcut?: string;
  }

  let { label, icon, pressed, shortcut, type = 'button', ...rest }: Props = $props();
</script>

<button
  class="icon-btn"
  {type}
  aria-label={label}
  aria-pressed={pressed}
  title={shortcut ? `${label} (${shortcut})` : label}
  {...rest}
>
  <Icon name={icon} />
</button>

<style>
  .icon-btn {
    display: inline-grid;
    place-items: center;
    width: 40px;
    height: 40px;
    padding: 0;
    border: 1px solid transparent;
    border-radius: var(--radius-sm);
    background: transparent;
    color: var(--text-muted);
    transition:
      background-color var(--dur) ease-out,
      color var(--dur) ease-out;
  }

  .icon-btn:hover:not(:disabled) {
    background: var(--surface-sunken);
    color: var(--text);
  }

  .icon-btn[aria-pressed='true'] {
    background: var(--surface-sunken);
    color: var(--text);
  }

  .icon-btn:disabled {
    opacity: 0.45;
    cursor: default;
  }
</style>
