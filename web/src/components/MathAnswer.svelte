<script lang="ts">
  import type { MathfieldElement } from 'mathlive';
  import { tick } from 'svelte';
  import { helpersFor, type ShapeHelper } from '../lib/answer-helpers';
  import type { EntryMode } from '../lib/study-session.svelte';
  import { applyInlineShortcuts } from '../lib/math-shortcuts';
  import type { AnswerPreview, AnswerType } from '../lib/types';
  import Icon from './Icon.svelte';
  import IconButton from './IconButton.svelte';
  import Markdown from './Markdown.svelte';
  import Tex from './Tex.svelte';

  interface Props {
    partId: string;
    /** Accessible name, e.g. "Answer" or "Answer for part a". */
    label: string;
    answerType: AnswerType;
    mode: EntryMode;
    latex: string;
    text: string;
    /** The bridge's reading of the current entry; fills the "We read your answer as ..." slot. */
    preview: AnswerPreview | null;
    readonly?: boolean;
    onvalue: (mode: EntryMode, value: string) => void;
    onmode: (mode: EntryMode) => void;
    onactive?: () => void;
  }

  let { partId, label, answerType, mode, latex, text, preview, readonly = false, onvalue, onmode, onactive }: Props =
    $props();

  let field: MathfieldElement | undefined = $state();
  let plain: HTMLInputElement | undefined = $state();

  const helpers = $derived(helpersFor(answerType));
  // The helpers are one tab stop (a toolbar); arrow keys move between them. That keeps
  // Tab going straight from one answer box to the next.
  let helperIndex = $state(0);
  let toolbar: HTMLElement | undefined = $state();

  function moveHelper(event: KeyboardEvent): void {
    const last = helpers.length - 1;
    const key = event.key;
    if (key !== 'ArrowRight' && key !== 'ArrowLeft' && key !== 'Home' && key !== 'End') return;
    event.preventDefault();
    helperIndex =
      key === 'Home' ? 0 : key === 'End' ? last : Math.min(last, Math.max(0, helperIndex + (key === 'ArrowRight' ? 1 : -1)));
    void tick().then(() => toolbar?.querySelectorAll('button')[helperIndex]?.focus());
  }

  /** The field's current content, read straight from it (MathLive's events can lag a keystroke). */
  export function read(): string {
    return mode === 'math' ? (field?.getValue('latex') ?? latex) : (plain?.value ?? text);
  }

  export function focus(attempt = 0): void {
    if (mode !== 'math') {
      plain?.focus();
      return;
    }
    if (!field || document.activeElement === field) return;
    // MathLive moves the focus 60 ms after focus() and gives up if the active element
    // changed meanwhile (as it does when the pause overlay's Resume button goes away), yet
    // still believes it has focus. Let go of the old focus first, and if the focus did not
    // arrive, reset MathLive's idea of it and try again.
    if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
    if (attempt > 0) field.blur();
    field.focus();
    if (attempt < 3) {
      window.setTimeout(() => {
        if (field?.isConnected && !readonly && document.activeElement === document.body) focus(attempt + 1);
      }, 120);
    }
  }

  $effect(() => {
    if (field && field.getValue('latex') !== latex) field.setValue(latex, { silenceNotifications: true });
  });

  $effect(() => {
    if (field) field.readOnly = readonly;
  });

  $effect(() => {
    if (field) applyInlineShortcuts(field);
  });

  async function switchMode(): Promise<void> {
    onmode(mode === 'math' ? 'text' : 'math');
    await tick();
    focus();
  }

  function insert(helper: ShapeHelper): void {
    if (readonly) return;
    if (mode === 'math' && field) {
      field.insert(helper.latex, { format: 'latex', focus: true, feedback: false });
      onvalue('math', field.getValue('latex'));
    } else if (plain) {
      const start = plain.selectionStart ?? plain.value.length;
      const end = plain.selectionEnd ?? start;
      plain.setRangeText(helper.text, start, end, 'end');
      onvalue('text', plain.value);
      plain.focus();
    }
  }
</script>

<div class="answer" data-testid={`answer-${partId}`} data-mode={mode}>
  <div class="row">
    <div class="entry" onfocusin={onactive}>
      {#if mode === 'math'}
        <math-field
          bind:this={field}
          aria-label={label}
          math-virtual-keyboard-policy="manual"
          data-testid={`field-${partId}`}
          oninput={() => field && onvalue('math', field.getValue('latex'))}
        ></math-field>
      {:else}
        <input
          class="plain"
          type="text"
          bind:this={plain}
          value={text}
          {readonly}
          aria-label={`${label}, plain text`}
          spellcheck="false"
          autocomplete="off"
          autocapitalize="off"
          data-testid={`field-${partId}`}
          oninput={() => plain && onvalue('text', plain.value)}
        />
      {/if}
    </div>
    <IconButton
      label={mode === 'math' ? 'Switch to plain-text entry' : 'Switch to math entry'}
      icon={mode === 'math' ? 'text' : 'math'}
      shortcut="`"
      disabled={readonly}
      data-testid={`mode-${partId}`}
      onclick={switchMode}
    />
  </div>

  {#if helpers.length > 0 && !readonly}
    <div class="helpers" role="toolbar" aria-label="Answer shape helpers" tabindex="-1" bind:this={toolbar} onkeydown={moveHelper}>
      {#each helpers as helper, i (helper.id)}
        <button
          type="button"
          class="chip"
          tabindex={i === helperIndex ? 0 : -1}
          onfocus={() => (helperIndex = i)}
          aria-label={helper.name}
          title={helper.name}
          data-testid={`helper-${partId}-${helper.id}`}
          onclick={() => insert(helper)}>{helper.label}</button
        >
      {/each}
    </div>
  {/if}

  <div
    class="preview"
    aria-live="polite"
    data-testid={`preview-${partId}`}
    data-status={preview === null ? 'empty' : preview.ok ? 'ok' : 'error'}
  >
    {#if preview?.ok && preview.read_as_latex}
      <span class="lead">We read your answer as</span>
      <span class="read"><Tex latex={preview.read_as_latex} /></span>
    {:else if preview && !preview.ok && preview.message}
      <span class="problem-note">
        <Icon name="alert" size={1.125} />
        <span class="message"><Markdown source={preview.message} inline /></span>
      </span>
    {/if}
    {#each preview?.hints ?? [] as note (note)}
      <span class="note muted">{note}</span>
    {/each}
  </div>
</div>

<style>
  .answer {
    display: grid;
    gap: var(--sp-1);
  }

  .row {
    display: flex;
    align-items: flex-start;
    gap: var(--sp-1);
  }

  .entry {
    flex: 1;
    min-width: 0;
  }

  .plain {
    width: 100%;
    min-height: 3rem;
    padding: var(--sp-1) var(--sp-2);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--surface-sunken);
    color: var(--text);
    font-family: var(--font-mono);
    font-size: var(--fs-answer);
  }

  .plain:focus {
    border-color: var(--accent);
    outline: var(--focus-width) solid var(--accent);
    outline-offset: 2px;
  }

  .helpers {
    display: flex;
    flex-wrap: wrap;
    gap: var(--sp-1);
  }

  .chip {
    min-width: 40px;
    min-height: 32px;
    padding: 0 var(--sp-1);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--surface);
    color: var(--text);
    font-size: var(--fs-small);
    transition: background-color var(--dur) ease-out;
  }

  .chip:hover {
    background: var(--surface-sunken);
  }

  .preview {
    min-height: 2rem;
    padding-top: var(--sp-0);
    color: var(--text-muted);
    font-size: var(--fs-small);
  }

  .lead {
    margin-inline-end: var(--sp-1);
  }

  .read {
    color: var(--text);
    font-family: var(--font-text);
    font-size: 1.0625rem;
  }

  .problem-note {
    display: inline-flex;
    align-items: flex-start;
    gap: var(--sp-1);
    color: var(--warning);
    font-weight: 500;
  }

  .note {
    display: block;
    font-size: var(--fs-caption);
  }

  .message {
    padding-top: 1px;
  }
</style>
