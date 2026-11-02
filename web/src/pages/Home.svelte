<script lang="ts">
  import { onMount } from 'svelte';
  import Button from '../components/Button.svelte';
  import { userMessage } from '../lib/bridge';
  import { listText, paceWords, ROLE_ORDER, ROLE_WORDS } from '../lib/plan-words';
  import { getPractice } from '../lib/practice-api';
  import { navigate } from '../lib/router.svelte';
  import type { TodayView } from '../lib/types';

  let today = $state<TodayView | null>(null);
  let error = $state('');
  let actions: HTMLElement | undefined = $state();

  // Courses with a name (a plan of flashcards only has an unnamed line).
  const courses = $derived((today?.courses ?? []).filter((c) => c.title));
  const tests = $derived((today?.exams ?? []).filter((e) => e.practice_test && e.exam_id !== null));
  // No problems planned (every section Off, or all learned ahead): point to the Library.
  const noProblems = $derived(!!today && today.problems === 0 && !today.session_open && !today.done_today);
  const canStart = $derived(!!today && !today.done_today && (today.problems > 0 || today.flashcards > 0));
  const working = $derived(!!today && !today.done_today);

  // The day's items by role, in a fixed order, only the roles it has.
  const roles = $derived(
    ROLE_ORDER.flatMap((role) => {
      const n = today?.by_role?.[role] ?? 0;
      return n > 0 ? [{ role, n, ...ROLE_WORDS[role] }] : [];
    }),
  );
  // The planner's fields; an older bridge sends none of them.
  const pace = $derived(today?.hours_basis ? paceWords(today) : null);
  const behind = $derived(today?.behind ?? []);
  const setAside = $derived(today?.set_aside ?? []);
  const sittings = $derived((today?.sittings ?? []).filter((s) => s.skills.length > 0));
  const notes = $derived(today?.notes ?? []);

  onMount(() => {
    void (async () => {
      try {
        const { api } = await getPractice();
        today = await api.study_today();
      } catch (caught) {
        error = userMessage(caught) ?? (caught instanceof Error ? caught.message : String(caught));
      }
    })();
  });

  // Start has focus on arrival, so Enter begins the session.
  $effect(() => {
    if (today) actions?.querySelector('button')?.focus();
  });

  function minutes(n: number): string {
    return `about ${n} minute${n === 1 ? '' : 's'}`;
  }

  function days(n: number): string {
    return n === 0 ? 'today' : n === 1 ? 'tomorrow' : `in ${n} days`;
  }
</script>

<section class="page" data-testid="page-home">
  <h1>Today</h1>
  {#if error}
    <p class="note" role="alert" data-testid="home-error">{error}</p>
  {:else if !today}
    <p class="note">Loading…</p>
  {:else}
    {#if today.done_today && !today.session_open}
      <p class="plan" data-testid="today-plan">Today's plan is done.</p>
    {:else}
      <p class="plan" data-testid="today-plan">
        {today.problems} problem{today.problems === 1 ? '' : 's'}, {minutes(today.minutes)}
        {#if today.flashcards > 0}<span class="muted">· {today.flashcards} flashcard{today.flashcards === 1 ? '' : 's'}</span>{/if}
      </p>
    {/if}

    {#if working && roles.length > 0}
      <ul class="roles" aria-label="Today's problems by kind" data-testid="by-role">
        {#each roles as r (r.role)}
          <li title={r.hint} data-role={r.role}><span class="count tabular">{r.n}</span> {r.label}</li>
        {/each}
      </ul>
    {/if}

    {#if noProblems}
      <p class="note" data-testid="nothing-due">
        No problems are planned today. Switch a section on in the Library to start learning it.
      </p>
    {/if}

    <div class="actions" bind:this={actions}>
      {#if noProblems}
        <Button variant="primary" data-testid="open-library" onclick={() => navigate('library')}>Open the Library</Button>
      {/if}
      {#if today.session_open}
        <Button variant="primary" shortcut="Enter" data-testid="start" onclick={() => navigate('study')}>Resume</Button>
      {:else if canStart}
        <Button variant={noProblems ? 'secondary' : 'primary'} shortcut={noProblems ? undefined : 'Enter'} data-testid="start" onclick={() => navigate('study')}>Start</Button>
      {/if}
      {#if today.extra_practice_available || today.done_today}
        <Button variant="quiet" data-testid="extra" onclick={() => navigate('study', { mode: 'extra' })}>Extra practice</Button>
      {/if}
      {#each tests as exam (exam.exam_id)}
        <Button
          variant="quiet"
          data-testid="practice-test"
          onclick={() => navigate('study', { mode: 'practice-test', exam: String(exam.exam_id) })}
          >Practice test: {exam.name}</Button
        >
      {/each}
    </div>

    {#if pace || sittings.length > 0 || behind.length > 0 || setAside.length > 0 || notes.length > 0}
      <dl class="facts">
        {#if pace}
          <div data-testid="pace" data-basis={today.hours_basis}>
            <dt>Pace</dt>
            <dd>
              <span data-testid="pace-hours">{pace.line}</span>
              <span class="muted" data-testid="pace-basis">{pace.basis}</span>
            </dd>
          </div>
        {/if}
        {#each sittings as sitting (sitting.id)}
          <div data-testid="sitting-today">
            <dt>Sitting</dt>
            <dd>A closed-book, timed sitting on {listText(sitting.skills)}, after some warm-up practice.</dd>
          </div>
        {/each}
        {#if behind.length > 0}
          <div data-testid="behind">
            <dt>Behind</dt>
            <dd>
              {listText(behind)}.
              <a href="#/skills?filter=behind" data-testid="behind-skills">See them in Skills</a>
            </dd>
          </div>
        {/if}
        {#if setAside.length > 0}
          <div data-testid="set-aside">
            <dt>Set aside</dt>
            <dd>{listText(setAside)}, for the rest of today. {setAside.length === 1 ? 'It comes' : 'They come'} back tomorrow.</dd>
          </div>
        {/if}
        {#if notes.length > 0}
          <div data-testid="notes">
            <dt>Notes</dt>
            <dd>
              <ul class="notes">
                {#each notes as note, i (i)}
                  <li data-testid="note">{note}</li>
                {/each}
              </ul>
            </dd>
          </div>
        {/if}
      </dl>
    {/if}

    {#if courses.length > 1}
      <ul class="split" aria-label="By course" data-testid="course-split">
        {#each courses as course (course.course_id)}
          <li>
            <span class="name">{course.title}</span>
            <span class="tabular muted">{course.problems} problems, {minutes(course.minutes)}</span>
          </li>
        {/each}
      </ul>
    {/if}

    {#if today.exams.length > 0}
      <ul class="split" aria-label="Exams" data-testid="exams">
        {#each today.exams as exam (exam.exam_id ?? exam.name)}
          <li><span class="name">{exam.name}</span> <span class="muted">{days(exam.days_left)}</span></li>
        {/each}
      </ul>
    {/if}
  {/if}
</section>

<style>
  .page {
    display: grid;
    gap: var(--sp-2);
    max-width: 40rem;
    padding: var(--sp-6) var(--sp-5);
  }

  .plan {
    font-size: var(--fs-title);
    font-weight: 500;
  }

  .note {
    color: var(--text-muted);
  }

  /* The day's mix: a count and a word per role, like the marks on a problem. */
  .roles {
    display: flex;
    flex-wrap: wrap;
    gap: var(--sp-1);
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .roles li {
    display: inline-flex;
    align-items: baseline;
    gap: var(--sp-0);
    padding: 2px var(--sp-1);
    border: 1px solid var(--border);
    border-radius: 999px;
    color: var(--text-muted);
    font-size: var(--fs-small);
  }

  .count {
    color: var(--text);
    font-weight: 600;
  }

  .facts {
    display: grid;
    gap: 0;
    margin: var(--sp-2) 0 0;
  }

  .facts > div {
    display: grid;
    grid-template-columns: 6rem minmax(0, 1fr);
    gap: var(--sp-2);
    padding: var(--sp-1) 0;
    border-top: 1px solid var(--border);
  }

  dt {
    font-weight: 600;
  }

  dd {
    display: grid;
    gap: 2px;
    margin: 0;
  }

  .notes {
    display: grid;
    gap: var(--sp-0);
    margin: 0;
    padding: 0;
    list-style: none;
    color: var(--text-muted);
  }

  a {
    color: var(--accent);
  }

  .split {
    display: grid;
    gap: var(--sp-0);
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .split li {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: var(--sp-1);
    padding: var(--sp-0) 0;
    border-bottom: 1px solid var(--border);
  }

  .name {
    font-weight: 500;
  }

  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: var(--sp-1);
    padding-top: var(--sp-2);
  }
</style>
