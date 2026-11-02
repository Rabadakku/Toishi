<script lang="ts">
  import Button from './Button.svelte';
  import Icon from './Icon.svelte';

  let { onconfirm }: { onconfirm: () => void } = $props();
</script>

<!-- Non-modal: the problem stays usable. Any key or click also counts as an answer. -->
<div class="note" role="status" data-testid="still-working">
  <Icon name="info" size={1.25} />
  <div class="text">
    <strong>Still working?</strong>
    <span class="muted">If you are away, the clock pauses in a minute and this wait will not count.</span>
  </div>
  <Button variant="secondary" data-testid="still-working-yes" onclick={onconfirm}>Yes, still here</Button>
</div>

<style>
  .note {
    display: flex;
    align-items: center;
    gap: var(--sp-2);
    max-width: var(--measure);
    margin: var(--sp-2) auto 0;
    padding: var(--sp-1) var(--sp-2);
    border: 1px solid var(--warning);
    border-radius: var(--radius-sm);
    background: var(--surface);
    color: var(--warning);
    font-size: var(--fs-small);
  }

  .text {
    display: grid;
    flex: 1;
  }

  strong {
    color: var(--warning);
  }

  .muted {
    color: var(--text-muted);
  }
</style>
