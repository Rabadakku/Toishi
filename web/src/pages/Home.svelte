<script lang="ts">
  import { onMount } from 'svelte';
  import Button from '../components/Button.svelte';
  import { userMessage } from '../lib/bridge';
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
  const canStart = $derived(!!today && !today.vacation && !today.done_today && (today.problems > 0 || today.flashcards > 0));

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
    {#if today.vacation}
      <p class="plan" data-testid="today-plan">Vacation: nothing is scheduled today.</p>
    {:else if today.done_today && !today.session_open}
      <p class="plan" data-testid="today-plan">Today's plan is done.</p>
    {:else}
      <p class="plan" data-testid="today-plan">
        {today.problems} problem{today.problems === 1 ? '' : 's'}, {minutes(today.minutes)}
        {#if today.flashcards > 0}<span class="muted">· {today.flashcards} flashcard{today.flashcards === 1 ? '' : 's'}</span>{/if}
      </p>
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

    {#each today.proposals as proposal (proposal.kind)}
      <p class="note" data-testid="proposal">{proposal.message}</p>
    {/each}

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
      {#if canStart && !noProblems}
        <Button variant="quiet" data-testid="lighter" onclick={() => navigate('study', { mode: 'lighter' })}>Lighter set</Button>
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
