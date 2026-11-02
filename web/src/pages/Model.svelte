<script lang="ts">
  import { onMount, tick } from 'svelte';
  import Button from '../components/Button.svelte';
  import { userMessage } from '../lib/bridge';
  import { formatMoment, formatNumber, formatPercent } from '../lib/format';
  import { getPractice } from '../lib/practice-api';
  import { navigate } from '../lib/router.svelte';
  import type { Bin, ModelView, RefitReport } from '../lib/types';

  /** The parameters in plain words (core.learner SharedParams), most telling first. */
  const PARAMS: readonly { key: string; label: string; gloss?: (value: number) => string }[] = [
    { key: 'slip', label: 'Careless-slip rate', gloss: (v) => `a ${formatPercent(v)} chance of a slip on a problem you know` },
    { key: 'calib_a', label: 'Calibration shift by tier (1 to 5)' },
    { key: 'calib_b', label: 'Calibration slope' },
    { key: 'tau', label: 'Your speed against standard time', gloss: (v) => `about ${formatNumber(Math.exp(v), 2)} times the standard time` },
    { key: 'sigma_t', label: 'Spread of your solve times' },
    { key: 'delta4', label: 'Extra difficulty of tier 4' },
    { key: 'delta5', label: 'Extra difficulty of tier 5' },
    { key: 'phi', label: 'Forgetting time scale' },
    { key: 'gamma', label: 'Gain from each success' },
    { key: 'rho', label: 'Gain from each miss' },
    { key: 'alpha', label: 'Speed-up with practice' },
    { key: 'q_drift', label: 'Uncertainty added per day away' },
    { key: 'kappa', label: 'Weight of a matched wrong answer' },
    { key: 'same_day_weight', label: 'Weight of a second success the same day' },
    { key: 'prior_new_mean', label: 'Starting estimate for a new skill' },
    { key: 'prior_new_var', label: 'Starting uncertainty for a new skill' },
    { key: 'prior_background_mean', label: 'Starting estimate for a skill from earlier courses' },
    { key: 'prior_background_var', label: 'Starting uncertainty for a skill from earlier courses' },
    { key: 'fsrs_weights', label: 'Memory model weights (FSRS)' },
  ];

  const BLOCKS: Record<string, string> = { accuracy: 'Accuracy predictions', time: 'Time predictions' };

  let model = $state<ModelView | null>(null);
  let error = $state('');
  let status = $state('');
  let busy = $state<'refit' | 'reset' | null>(null);
  let confirming = $state(false);
  let cancelEl: HTMLElement | undefined = $state();
  let resetEl: HTMLElement | undefined = $state();

  onMount(() => {
    void load();
  });

  function message(caught: unknown): string {
    return userMessage(caught) ?? (caught instanceof Error ? caught.message : String(caught));
  }

  async function load(): Promise<void> {
    try {
      const { api } = await getPractice();
      model = await api.model_get();
    } catch (caught) {
      error = message(caught);
    }
  }

  /** Every parameter the bridge sent: the known ones in plain words first, then any others by name. */
  const rows = $derived.by(() => {
    const params = model?.params ?? {};
    const known = PARAMS.filter((p) => Object.hasOwn(params, p.key));
    const rest = Object.keys(params)
      .filter((key) => !PARAMS.some((p) => p.key === key))
      .sort()
      .map((key) => ({ key, label: key, gloss: undefined }));
    return [...known, ...rest].map((p) => {
      const value = params[p.key] ?? [];
      return { key: p.key, label: p.label, value, gloss: p.gloss && typeof value === 'number' ? p.gloss(value) : null };
    });
  });

  function valueText(key: string, value: number | number[]): string {
    if (Array.isArray(value)) {
      if (value.length === 0) return key === 'fsrs_weights' ? 'The FSRS-6 defaults' : 'None';
      return value.map((v) => formatNumber(v)).join(', ');
    }
    return formatNumber(value);
  }

  function sourceText(view: ModelView): string {
    const day = formatMoment(view.created_at);
    if (view.source === 'refit') return `Fitted to your practice on ${day}.`;
    if (view.source === 'reset') return `Reset to the starting values on ${day}.`;
    return `The starting values, taken from research, in use since ${day}.`;
  }

  async function refit(): Promise<void> {
    busy = 'refit';
    error = '';
    status = '';
    try {
      const { api } = await getPractice();
      const report = await api.model_refit();
      model = await api.model_get();
      // The view's own last refit, or the report just made if the bridge hasn't stored it.
      if (model && !model.last_refit) model = { ...model, last_refit: report };
      status = report.adopted ? 'Refit done: the new values are in use.' : 'Refit done: the current values stay.';
    } catch (caught) {
      error = message(caught);
    } finally {
      busy = null;
    }
  }

  async function openConfirm(): Promise<void> {
    confirming = true;
    status = '';
    await tick();
    cancelEl?.querySelector('button')?.focus();
  }

  async function closeConfirm(): Promise<void> {
    confirming = false;
    await tick();
    resetEl?.querySelector('button')?.focus();
  }

  async function reset(): Promise<void> {
    busy = 'reset';
    error = '';
    try {
      const { api } = await getPractice();
      model = await api.model_reset();
      confirming = false;
      status = 'Reset: the model uses its starting values again.';
      await tick();
      resetEl?.querySelector('button')?.focus();
    } catch (caught) {
      error = message(caught);
    } finally {
      busy = null;
    }
  }

  function share(bin: Bin, value: number): string {
    return bin.n > 0 ? formatPercent(value) : '–';
  }
</script>

{#snippet calibrationTable(id: string, title: string, first: string, bins: Bin[])}
  <table class="table calibration" data-testid={`calibration-${id}`}>
    <caption>{title}</caption>
    <thead>
      <tr>
        <th scope="col">{first}</th>
        <th scope="col" class="num">First tries</th>
        <th scope="col" class="num">Predicted</th>
        <th scope="col" class="num">Actual</th>
      </tr>
    </thead>
    <tbody>
      {#each bins as bin (bin.label)}
        <tr data-testid="bin">
          <th scope="row">{bin.label}</th>
          <td class="num tabular">{bin.n}</td>
          <td class="num tabular">{share(bin, bin.predicted)}</td>
          <td class="num tabular">{share(bin, bin.observed)}</td>
        </tr>
      {:else}
        <tr><td colspan="4" class="muted">No first tries yet.</td></tr>
      {/each}
    </tbody>
  </table>
{/snippet}

{#snippet refitReport(report: RefitReport)}
  <div class="report" data-testid="refit-report" data-adopted={report.adopted}>
    <p>
      <strong data-testid="refit-outcome">{report.adopted ? 'Kept the new values.' : 'Kept the current values.'}</strong>
      Refit on {formatMoment(report.at)} from {report.attempts} first tries; p = {formatNumber(report.p_value, 2)}.
    </p>
    <table class="table">
      <caption class="sr-only">Held-out log loss per first try, before and after the refit</caption>
      <thead>
        <tr>
          <th scope="col">Part</th>
          <th scope="col" class="num">Before</th>
          <th scope="col" class="num">After</th>
          <th scope="col" class="num">p</th>
          <th scope="col">Result</th>
        </tr>
      </thead>
      <tbody>
        {#each report.blocks as block (block.name)}
          <tr data-testid="refit-block" data-name={block.name} data-adopted={block.adopted}>
            <th scope="row">{BLOCKS[block.name] ?? block.name}</th>
            <td class="num tabular">{formatNumber(block.current)}</td>
            <td class="num tabular">{formatNumber(block.candidate)}</td>
            <td class="num tabular">{formatNumber(block.p_value, 2)}</td>
            <td>{block.adopted ? 'New values kept' : 'Current values kept'}</td>
          </tr>
        {/each}
      </tbody>
    </table>
    <p class="muted small">
      Before and after are the log loss per first try on your most recent tries, which the fit never saw: lower is
      better. New values are kept only when they lower it clearly and the p value says chance is unlikely.
    </p>
  </div>
{/snippet}

<section class="page" data-testid="page-model">
  <div class="title">
    <h1>Student model</h1>
    <p class="muted">
      How the app predicts your chance of getting a problem right on the first try. It plans your practice from these
      predictions and refits them to your own practice as your history grows.
    </p>
  </div>

  {#if error}
    <p class="error" role="alert" data-testid="model-error">{error}</p>
  {/if}
  {#if status}
    <p class="status" role="status" data-testid="model-status">{status}</p>
  {/if}

  {#if !model}
    {#if !error}<p class="muted">Loading…</p>{/if}
  {:else}
    <section class="group" aria-labelledby="values-title">
      <h2 id="values-title">Current values</h2>
      <p data-testid="model-source" data-source={model.source}>
        {sourceText(model)} <span class="muted">Version {model.version}, from {model.attempts} first tries so far.</span>
      </p>
      <table class="table params" data-testid="params">
        <caption class="sr-only">The model's parameters, read-only</caption>
        <tbody>
          {#each rows as row (row.key)}
            <tr data-testid="param" data-key={row.key}>
              <th scope="row">{row.label}</th>
              <td class="tabular">
                {valueText(row.key, row.value)}
                {#if row.gloss}<span class="muted">({row.gloss})</span>{/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </section>

    <section class="group" aria-labelledby="refit-title">
      <h2 id="refit-title">Refit</h2>
      <p class="muted">
        The app refits on its own as your history grows. Refit now runs it at once and shows what it found.
      </p>
      <div>
        <Button variant="secondary" disabled={busy !== null} data-testid="refit" onclick={refit}
          >{busy === 'refit' ? 'Refitting…' : 'Refit now'}</Button
        >
      </div>
      {#if model.last_refit}
        {@render refitReport(model.last_refit)}
      {:else}
        <p class="muted" data-testid="no-refit">No refit yet.</p>
      {/if}
    </section>

    <section class="group" aria-labelledby="calibration-title">
      <h2 id="calibration-title">How well predictions have matched</h2>
      <p class="muted">
        For each group of your first tries: the chance the model gave on average, and the share you actually got right.
        Close numbers mean the predictions can be trusted.
      </p>
      {@render calibrationTable('tier', 'By tier', 'Tier', model.calibration.by_tier)}
      {@render calibrationTable('gap', 'By days since the skill was last practiced', 'Gap', model.calibration.by_gap)}
      {@render calibrationTable('components', 'By number of skills in the problem', 'Skills', model.calibration.by_components)}
    </section>

    <section class="group" aria-labelledby="reset-title">
      <h2 id="reset-title">Reset</h2>
      {#if confirming}
        <div class="confirm" role="group" aria-label="Confirm the reset" data-testid="reset-confirmation">
          <p>
            Reset the model to its starting values? Your practice history stays; the values fitted to it are replaced
            until the next refit.
          </p>
          <div class="row">
            <Button variant="primary" disabled={busy !== null} data-testid="reset-confirm" onclick={reset}>Reset the model</Button>
            <span bind:this={cancelEl}><Button variant="quiet" data-testid="reset-cancel" onclick={closeConfirm}>Cancel</Button></span>
          </div>
        </div>
      {:else}
        <span bind:this={resetEl}
          ><Button variant="secondary" disabled={busy !== null} data-testid="reset" onclick={openConfirm}>Reset to starting values</Button></span
        >
      {/if}
    </section>
  {/if}

  <div>
    <Button variant="quiet" data-testid="back-settings" onclick={() => navigate('settings')}>Back to Settings</Button>
  </div>
</section>

<style>
  .page {
    display: grid;
    gap: var(--sp-4);
    max-width: 44rem;
    padding: var(--sp-6) var(--sp-5);
  }

  .title {
    display: grid;
    gap: var(--sp-1);
  }

  .group {
    display: grid;
    gap: var(--sp-2);
  }

  h2 {
    font-size: 1.125rem;
  }

  .table {
    width: 100%;
    border-collapse: collapse;
    font-size: var(--fs-small);
  }

  caption {
    padding-bottom: var(--sp-1);
    font-weight: 600;
    text-align: start;
  }

  th,
  td {
    padding: var(--sp-0) var(--sp-1);
    border-bottom: 1px solid var(--border);
    text-align: start;
    vertical-align: top;
  }

  thead th {
    color: var(--text-muted);
    font-weight: 600;
  }

  tbody th {
    font-weight: 500;
  }

  .num {
    text-align: end;
  }

  .params th {
    width: 55%;
  }

  /* The three calibration tables line up column for column. */
  .calibration {
    table-layout: fixed;
  }

  .calibration thead th:first-child {
    width: 40%;
  }

  .report,
  .confirm {
    display: grid;
    gap: var(--sp-1);
    padding: var(--sp-2) var(--sp-3);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--surface);
  }

  .row {
    display: flex;
    flex-wrap: wrap;
    gap: var(--sp-1);
  }

  .small {
    font-size: var(--fs-small);
  }

  .status {
    color: var(--text-muted);
  }

  .error {
    color: var(--incorrect);
  }
</style>
