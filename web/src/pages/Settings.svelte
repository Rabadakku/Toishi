<script lang="ts">
  import Tex from '../components/Tex.svelte';
  import { bridge } from '../lib/ui.svelte';
  import { preferences, setTextSize, setTheme } from '../lib/settings.svelte';
  import { TEXT_SIZE_MAX, TEXT_SIZE_MIN, type ThemeChoice } from '../lib/types';

  const THEMES: { id: ThemeChoice; label: string; hint: string }[] = [
    { id: 'auto', label: 'Automatic', hint: 'Follows the Mac' },
    { id: 'day', label: 'Day', hint: 'Warm, for a lit room' },
    { id: 'night', label: 'Night', hint: 'Soft, for the dark' },
  ];

  let reply = $state('');

  async function ping(): Promise<void> {
    if (!bridge.api) return;
    reply = await bridge.api.ping('hello from the page');
  }
</script>

<section class="page" data-testid="page-settings">
  <h1>Settings</h1>

  <fieldset class="group">
    <legend>Theme</legend>
    <div class="themes" role="radiogroup" aria-label="Theme">
      {#each THEMES as theme (theme.id)}
        <label class="theme" class:on={preferences.theme === theme.id}>
          <input
            type="radio"
            name="theme"
            value={theme.id}
            checked={preferences.theme === theme.id}
            data-testid={`theme-${theme.id}`}
            onchange={() => setTheme(theme.id)}
          />
          <span class="name">{theme.label}</span>
          <span class="hint">{theme.hint}</span>
        </label>
      {/each}
    </div>
  </fieldset>

  <div class="group">
    <label class="legend" for="text-size">Text size</label>
    <div class="size">
      <input
        id="text-size"
        type="range"
        min={TEXT_SIZE_MIN}
        max={TEXT_SIZE_MAX}
        step="1"
        value={preferences.text_size}
        data-testid="text-size"
        aria-valuetext={`${preferences.text_size} pixels`}
        oninput={(event) => setTextSize(Number(event.currentTarget.value))}
      />
      <output class="tabular" for="text-size" data-testid="text-size-value">{preferences.text_size} px</output>
    </div>
    <div class="sample problem-sample" data-testid="text-sample">
      <p>Find the critical numbers of <Tex latex={String.raw`f(x) = x^4 - 2x^2`} />. The math grows with the text.</p>
    </div>
  </div>

  <div class="group diagnostics" data-testid="diagnostics">
    <h2>Diagnostics</h2>
    <p class="muted" data-testid="bridge-status">
      {#if bridge.info}
        v{bridge.info.version} · Python {bridge.info.python}
      {:else if bridge.error}
        Bridge unavailable: {bridge.error}
      {:else}
        Connecting to Python…
      {/if}
    </p>
    <div class="row">
      <button type="button" class="ping" data-testid="ping" disabled={!bridge.api} onclick={ping}>
        Send to Python
      </button>
      <output class="mono" data-testid="ping-reply">{reply}</output>
    </div>

    {#if bridge.selfTest}
      <div data-testid="selftest" data-status={bridge.selfTest.ok ? 'pass' : 'fail'}>
        <h3>Self-test: {bridge.selfTest.ok ? 'pass' : 'FAIL'}</h3>
        <ul>
          {#each bridge.selfTest.checks as check (check.name)}
            <li class:fail={!check.ok}>{check.ok ? '✓' : '✗'} {check.name}: {check.detail}</li>
          {/each}
        </ul>
      </div>
    {/if}
  </div>
</section>

<style>
  .page {
    display: grid;
    gap: var(--sp-4);
    max-width: 40rem;
    padding: var(--sp-6) var(--sp-5);
  }

  .group {
    display: grid;
    gap: var(--sp-1);
    margin: 0;
    padding: 0;
    border: 0;
  }

  legend,
  .legend {
    padding: 0;
    margin-bottom: var(--sp-1);
    font-weight: 600;
  }

  .themes {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--sp-1);
  }

  .theme {
    position: relative;
    display: grid;
    gap: 2px;
    padding: var(--sp-1) var(--sp-2);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--surface);
    cursor: pointer;
  }

  .theme.on {
    border-color: var(--accent);
    background: var(--selection);
  }

  .theme:has(input:focus-visible) {
    outline: var(--focus-width) solid var(--accent);
    outline-offset: 2px;
  }

  .theme input {
    position: absolute;
    opacity: 0;
    pointer-events: none;
  }

  .name {
    font-weight: 600;
  }

  .hint {
    color: var(--text-muted);
    font-size: var(--fs-small);
  }

  .size {
    display: flex;
    align-items: center;
    gap: var(--sp-2);
  }

  .size input {
    flex: 1;
    accent-color: var(--accent);
  }

  output {
    min-width: 4rem;
    text-align: end;
  }

  .problem-sample {
    padding: var(--sp-2) var(--sp-3);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--surface);
    font-family: var(--font-text);
    font-size: var(--fs-problem);
    line-height: var(--lh-problem);
  }

  .diagnostics h2 {
    font-size: 1.125rem;
  }

  .diagnostics h3 {
    font-size: var(--fs-body);
  }

  .row {
    display: flex;
    align-items: center;
    gap: var(--sp-2);
  }

  .ping {
    padding: var(--sp-1) var(--sp-2);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--surface);
  }

  .ping:disabled {
    opacity: 0.45;
    cursor: default;
  }

  .mono {
    font-family: var(--font-mono);
    font-size: var(--fs-small);
  }

  ul {
    margin: 0;
    padding-left: var(--sp-3);
    font-size: var(--fs-small);
  }

  li.fail {
    color: var(--incorrect);
  }
</style>
