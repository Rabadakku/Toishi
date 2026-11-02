<script lang="ts">
  import type { Progress, Reason } from '../lib/types';
  import Button from './Button.svelte';
  import IconButton from './IconButton.svelte';
  import ReasonTag from './ReasonTag.svelte';

  interface Props {
    progress: Progress | null;
    reason: Reason | null;
    /** What the item is when it is not a numbered problem ("Flashcard", "Worked example"). */
    itemLabel?: string | null;
    canEnd?: boolean;
    onend?: () => void;
    reasonOpen: boolean;
    paused: boolean;
    canPause: boolean;
    /** False on the summary and the "nothing to study" screens: there is no clock to pause. */
    showPause?: boolean;
    focusMode: boolean;
    onreason: (open: boolean) => void;
    onpause: () => void;
    onfocusmode: () => void;
  }

  let {
    progress,
    reason,
    itemLabel = null,
    canEnd = false,
    reasonOpen,
    paused,
    canPause,
    showPause = true,
    focusMode,
    onreason,
    onpause,
    onfocusmode,
    onend,
  }: Props = $props();
</script>

<header class="top">
  <div class="left">
    <IconButton
      label={focusMode ? 'Show the sidebar' : 'Enter focus mode'}
      icon={focusMode ? 'unfocus' : 'focus'}
      shortcut="F"
      pressed={focusMode}
      data-testid="focus-toggle"
      onclick={onfocusmode}
    />
    {#if itemLabel}
      <span class="progress" data-testid="progress">{itemLabel}</span>
    {:else if progress && progress.total > 0}
      <span class="progress tabular" data-testid="progress">
        <span class="sr-only">Problem </span>{Math.max(1, progress.position)} of {progress.total}
      </span>
    {/if}
  </div>

  <div class="center">
    {#if reason}
      <ReasonTag {reason} open={reasonOpen} ontoggle={onreason} disabled={paused} />
    {/if}
  </div>

  <div class="right">
    {#if canEnd}
      <Button variant="quiet" title="End the session now and see the summary" data-testid="end-session" onclick={() => onend?.()}
        >End</Button
      >
    {/if}
    {#if showPause}
      <Button
        variant="quiet"
        icon={paused ? 'play' : 'pause'}
        shortcut="Esc"
        aria-pressed={paused}
        disabled={!canPause}
        title={paused ? 'Resume (Esc or P)' : 'Pause (Esc or P)'}
        data-testid="pause-button"
        onclick={onpause}
      >
        {paused ? 'Resume' : 'Pause'}
      </Button>
    {/if}
  </div>

  {#if progress}
    <div
      class="bar"
      role="progressbar"
      aria-label="Session progress"
      aria-valuemin={0}
      aria-valuemax={progress.total}
      aria-valuenow={progress.answered}
    >
      <div class="fill" style:width={`${(progress.answered / Math.max(1, progress.total)) * 100}%`}></div>
    </div>
  {/if}
</header>

<style>
  .top {
    position: relative;
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: var(--sp-2);
    padding-bottom: var(--sp-1);
  }

  .left {
    display: flex;
    align-items: center;
    gap: var(--sp-1);
  }

  .right {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: var(--sp-0);
  }

  .progress {
    color: var(--text-muted);
    font-size: var(--fs-small);
    font-weight: 500;
  }

  .bar {
    position: absolute;
    inset-inline: 0;
    bottom: 0;
    height: 2px;
    border-radius: 2px;
    background: var(--border);
    overflow: hidden;
  }

  .fill {
    height: 100%;
    background: var(--accent);
    transition: width var(--dur) ease-out;
  }
</style>
