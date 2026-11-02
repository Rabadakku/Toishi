<script lang="ts">
  import { formatMs } from '../lib/format';
  import type { Summary } from '../lib/types';
  import Button from './Button.svelte';
  import Icon from './Icon.svelte';

  interface Props {
    summary: Summary;
    onhome: () => void;
    onmore: () => void;
  }

  let { summary, onhome, onmore }: Props = $props();
  const test = $derived(summary.test);

  /** "To revisit": one line per skill, however many of its problems were missed. */
  const revisit = $derived.by(() => {
    const groups = new Map<string, { key: string; name: string; label: string; count: number }>();
    for (const miss of summary.misses) {
      const id = miss.skill_id ?? miss.item_key;
      const group = groups.get(id);
      if (group) group.count += 1;
      else groups.set(id, { key: id, name: miss.skill_name, label: miss.label, count: 1 });
    }
    return [...groups.values()];
  });
</script>

<section class="summary" aria-labelledby="summary-title" data-testid="summary">
  <h2 id="summary-title">{test ? 'Practice test finished' : 'Session complete'}</h2>

  <dl class="stats">
    <div>
      <dt>Correct</dt>
      <dd class="tabular" data-testid="summary-correct">{summary.correct} of {summary.problems}</dd>
    </div>
    <div>
      <dt>To revisit</dt>
      <dd class="tabular" data-testid="summary-missed">{revisit.length}</dd>
    </div>
    <div>
      <dt>Active time</dt>
      <dd class="tabular" data-testid="summary-time">{formatMs(summary.active_ms)}</dd>
    </div>
  </dl>

  {#if test}
    <ul class="skills" aria-label="Practice test results" data-testid="test-lines">
      {#each test.lines as line (line.item_key)}
        <li class={line.correct ? 'correct' : 'incorrect'}>
          <Icon name={line.correct ? 'check-circle' : 'x-circle'} size={1.125} />
          <span class="name">{line.skill_name}</span>
          <span class="word">{line.correct ? 'Correct' : line.answered ? 'Missed' : 'Not answered'}</span>
        </li>
      {/each}
    </ul>
  {/if}

  {#if revisit.length > 0}
    <ul class="skills" aria-label="Skills to revisit" data-testid="summary-misses">
      {#each revisit as group (group.key)}
        <li class="incorrect" data-testid="revisit-skill">
          <Icon name="x-circle" size={1.125} />
          <span class="name">{group.name}</span>
          <span class="word">{group.count > 1 ? `${group.count} missed` : group.label}</span>
        </li>
      {/each}
    </ul>
  {/if}

  {#if summary.learned.length > 0}
    <ul class="skills" aria-label="Skills learned" data-testid="summary-learned">
      {#each summary.learned as name (name)}
        <li class="correct">
          <Icon name="check-circle" size={1.125} />
          <span class="name">{name}</span>
          <span class="word">Learned</span>
        </li>
      {/each}
    </ul>
  {/if}

  {#if summary.flashcards > 0}
    <p class="muted">{summary.flashcards} flashcard{summary.flashcards === 1 ? '' : 's'} reviewed.</p>
  {/if}

  {#if summary.ready_today > 0}
    <p class="forecast" data-testid="ready-today">
      {summary.ready_today} more learning problem{summary.ready_today === 1 ? ' is' : 's are'} ready today.
    </p>
  {/if}
  <p class="forecast" data-testid="forecast">
    Tomorrow: {summary.forecast.problems} problems, about {summary.forecast.minutes} minutes.
  </p>

  <div class="actions">
    <Button variant="primary" data-testid="summary-home" onclick={onhome}>Back to Home</Button>
    {#if summary.extra_practice_available}
      <!-- Offered, never pushed. -->
      <Button variant="quiet" data-testid="summary-more" onclick={onmore}>Extra practice</Button>
    {/if}
  </div>
</section>

<style>
  .summary {
    display: grid;
    gap: var(--sp-3);
    max-width: 36rem;
    margin: var(--sp-6) auto 0;
    padding: var(--sp-4);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--surface);
    box-shadow: var(--shadow);
  }

  .stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--sp-2);
    margin: 0;
  }

  dt {
    color: var(--text-muted);
    font-size: var(--fs-caption);
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }

  dd {
    margin: var(--sp-0) 0 0;
    font-size: var(--fs-title);
    font-weight: 600;
  }

  .skills {
    display: grid;
    gap: var(--sp-1);
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .skills li {
    display: flex;
    align-items: center;
    gap: var(--sp-1);
    font-size: var(--fs-small);
  }

  .skills .correct {
    color: var(--correct);
  }

  .skills .incorrect {
    color: var(--incorrect);
  }

  .name {
    flex: 1;
    color: var(--text);
  }

  .word {
    font-weight: 600;
  }

  .forecast {
    color: var(--text-muted);
  }

  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: var(--sp-1);
  }
</style>
