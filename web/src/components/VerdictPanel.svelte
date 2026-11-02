<script lang="ts">
  import type { AttemptResult, ProblemView } from '../lib/types';
  import Markdown from './Markdown.svelte';
  import Tex from './Tex.svelte';
  import VerdictBadge from './VerdictBadge.svelte';

  interface Props {
    problem: ProblemView;
    result: AttemptResult;
  }

  let { problem, result }: Props = $props();

  const solution = $derived(result.solution);
  const outcome = $derived(result.outcome === 'correct' ? 'correct' : 'incorrect');
  const multi = $derived(problem.card.parts.length > 1);
  const yours = $derived(result.verdicts.filter((v) => v.read_as));
  const feedback = $derived(result.verdicts.filter((v) => v.feedback));
</script>

{#if solution}
  <section
    class={`verdict ${outcome}`}
    role="status"
    aria-live="polite"
    data-testid="verdict"
    data-outcome={result.outcome}
  >
    <div class="top">
      <VerdictBadge kind={outcome} />
      <!-- Time appears only now, never as a countdown; never in an Untimed session. -->
      {#if solution.time_text}
        <span class="time tabular" data-testid="time-note">{solution.time_text}</span>
      {/if}
    </div>
    {#if solution.skill_name}
      <p class="skill">Skill: <strong data-testid="skill-name">{solution.skill_name}</strong></p>
    {/if}
    {#if result.outcome === 'correct' && result.first_try_counted === false}
      <p class="note" data-testid="first-try-note">Right on a later try. Only the first try counts.</p>
    {/if}
    {#if multi && result.verdicts.length > 0}
      <ul class="parts">
        {#each result.verdicts as verdict, i (i)}
          <li data-testid={`part-verdict-${verdict.part ?? 'main'}`}>
            <span class="plabel">({verdict.part ?? i + 1})</span>
            <VerdictBadge kind={verdict.status === 'correct' ? 'correct' : 'incorrect'} compact />
          </li>
        {/each}
      </ul>
    {/if}
    {#if outcome === 'incorrect'}
      <div class="compare" data-testid="compare">
        <div class="cell">
          <span class="cap">Your answer</span>
          <span class="val">
            {#if yours.length > 0}
              {#each yours as verdict, i (i)}
                <span class="one">
                  {#if multi}<span class="plabel">({verdict.part})</span>{/if}
                  <Tex latex={verdict.read_as ?? ''} />
                </span>
              {/each}
            {:else}
              <span class="muted">No answer</span>
            {/if}
          </span>
        </div>
        {#if solution.answer_md}
          <div class="cell">
            <span class="cap">Correct answer</span>
            <span class="val" data-testid="correct-answer"><Markdown source={solution.answer_md} inline /></span>
          </div>
        {/if}
        {#each feedback as verdict, i (i)}
          <div class="feedback" data-testid="feedback"><Markdown source={verdict.feedback ?? ''} inline /></div>
        {/each}
      </div>
      {#if solution.confident_error}
        <p class="note" data-testid="confident-error">
          You marked this one as sure. That makes it worth a second look; it will come back tomorrow.
        </p>
      {/if}
      {#if solution.textbook_ref}
        <p class="note" data-testid="textbook-ref">In your textbook: {solution.textbook_ref}</p>
      {/if}
    {/if}
  </section>
{/if}

<style>
  .verdict {
    display: grid;
    gap: var(--sp-1);
    max-width: var(--measure);
    margin: var(--sp-3) auto 0;
    padding: var(--sp-2) var(--sp-3);
    border: 1px solid var(--border);
    border-inline-start: 4px solid var(--correct);
    border-radius: var(--radius-sm);
    background: var(--surface);
  }

  .verdict.incorrect {
    border-inline-start-color: var(--incorrect);
  }

  .top {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: var(--sp-1);
  }

  .time {
    color: var(--text-muted);
    font-size: var(--fs-small);
  }

  .skill,
  .note {
    margin: 0;
    color: var(--text-muted);
    font-size: var(--fs-small);
  }

  .skill strong {
    color: var(--text);
    font-weight: 600;
  }

  .parts,
  .picks {
    display: flex;
    flex-wrap: wrap;
    gap: var(--sp-2);
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .parts li {
    display: flex;
    align-items: center;
    gap: var(--sp-1);
  }

  .plabel {
    color: var(--text-muted);
    font-size: var(--fs-small);
    font-weight: 600;
  }

  .compare {
    display: grid;
    grid-template-columns: 1fr 1fr;
    align-items: start;
    gap: var(--sp-2);
    padding-top: var(--sp-1);
    border-top: 1px solid var(--border);
  }

  .one {
    display: inline-flex;
    gap: var(--sp-0);
    margin-inline-end: var(--sp-2);
  }

  .cell {
    display: grid;
    gap: var(--sp-0);
  }

  .cap {
    color: var(--text-muted);
    font-size: var(--fs-caption);
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }

  .val {
    font-family: var(--font-text);
    font-size: 1.125rem;
  }

  .feedback {
    grid-column: 1 / -1;
    font-family: var(--font-text);
    font-size: 1rem;
  }
</style>
