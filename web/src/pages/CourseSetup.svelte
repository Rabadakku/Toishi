<script lang="ts">
  import { untrack } from 'svelte';
  import Button from '../components/Button.svelte';
  import { userMessage } from '../lib/bridge';
  import { formatDay, localDay } from '../lib/format';
  import { listText, TIER_WORDS } from '../lib/plan-words';
  import { getPractice } from '../lib/practice-api';
  import { navigate, router } from '../lib/router.svelte';
  import type { CourseSettings, Exam, ExamIn } from '../lib/types';

  /** How the course's schedule is anchored: a first-class date, "my class is at section X today", or not yet. */
  type ScheduleMode = 'date' | 'aligned' | 'none';

  interface Draft {
    mode: ScheduleMode;
    start: string;
    aligned_deck: string;
    /** The day the alignment was said; it becomes today when the section changes. */
    aligned_day: string;
    end: string;
    pace: number;
    /** Percent, 80 to 95. */
    accuracy: number;
    tier: number;
    band: 'standard' | 'hard';
  }

  interface ExamDraft {
    exam_id?: number;
    name: string;
    day: string;
    scope: string[];
    minutes: string;
    problems: string;
    target: number | null;
  }

  const MODES: readonly { id: ScheduleMode; label: string; hint: string }[] = [
    { id: 'date', label: 'From a start date', hint: 'The day of the first class' },
    { id: 'aligned', label: 'My class is at a section today', hint: 'For starting partway through' },
    { id: 'none', label: 'Not set yet', hint: 'New skills wait until there is a schedule' },
  ];

  const BANDS: readonly { id: Draft['band']; label: string; hint: string }[] = [
    { id: 'standard', label: 'Standard', hint: 'Problems you get right about 70 to 90% of the time' },
    { id: 'hard', label: 'Hard', hint: 'About 50 to 75% of the time: slower going, more struggle' },
  ];

  const TIERS = [3, 4, 5] as const;

  let settings = $state<CourseSettings | null>(null);
  let draft = $state<Draft | null>(null);
  let exams = $state<Exam[]>([]);
  let examDraft = $state<ExamDraft | null>(null);
  let error = $state('');
  let examError = $state('');
  let status = $state('');
  let busy = $state(false);
  const today = localDay();

  const titles = $derived(new Map((settings?.sections ?? []).map((s) => [s.deck, s.title])));

  $effect(() => {
    const course = router.params.course;
    untrack(() => void load(course));
  });

  function message(caught: unknown): string {
    return userMessage(caught) ?? (caught instanceof Error ? caught.message : String(caught));
  }

  function toDraft(s: CourseSettings): Draft {
    return {
      mode: s.aligned ? 'aligned' : s.start ? 'date' : 'none',
      start: s.start ?? '',
      aligned_deck: s.aligned?.deck ?? '',
      aligned_day: s.aligned?.day ?? today,
      end: s.end ?? '',
      pace: s.pace_factor,
      accuracy: Math.min(95, Math.max(80, Math.round(s.accuracy_target * 100))),
      tier: s.target_tier,
      band: s.growth_band,
    };
  }

  async function load(course: string | undefined): Promise<void> {
    error = '';
    status = '';
    try {
      const { api } = await getPractice();
      const id = course ?? (await api.library_get()).courses[0]?.id;
      if (!id) {
        error = 'There are no courses yet. Packs and imported cards appear in the Library.';
        return;
      }
      const loaded = await api.course_settings_get(id);
      settings = loaded;
      exams = loaded.exams;
      draft = toDraft(loaded);
      examDraft = null;
    } catch (caught) {
      error = message(caught);
    }
  }

  /** What stops the settings from saving, in the words the student needs to fix it. */
  function problemWith(d: Draft, hasPace: boolean): string | null {
    if (hasPace && d.mode === 'date' && !d.start) return 'Choose the day of the first class, or set the schedule another way.';
    if (hasPace && d.mode === 'aligned' && !d.aligned_deck) return 'Choose the section your class is at.';
    if (hasPace && d.mode === 'date' && d.start && d.end && d.end < d.start) {
      return 'The course ends before it starts. Check the two dates.';
    }
    return null;
  }

  async function save(event: SubmitEvent): Promise<void> {
    event.preventDefault();
    if (!settings || !draft) return;
    const problem = problemWith(draft, settings.has_pace);
    if (problem) {
      error = problem;
      status = '';
      return;
    }
    busy = true;
    error = '';
    status = '';
    try {
      const { api } = await getPractice();
      const saved = await api.course_settings_set({
        course_id: settings.course_id,
        start: draft.mode === 'date' ? draft.start : null,
        aligned: draft.mode === 'aligned' ? { deck: draft.aligned_deck, day: draft.aligned_day } : null,
        pace_factor: draft.pace,
        accuracy_target: draft.accuracy / 100,
        target_tier: draft.tier,
        end: draft.end || null,
        keep_target: settings.keep_target,
        keep_tier: settings.keep_tier,
        growth_band: draft.band,
      });
      settings = saved;
      exams = saved.exams;
      draft = toDraft(saved);
      status = 'Saved.';
    } catch (caught) {
      error = message(caught);
    } finally {
      busy = false;
    }
  }

  function pickSection(deck: string): void {
    if (!draft) return;
    draft.aligned_deck = deck;
    draft.aligned_day = today; // "today": the alignment is a fact about this day
  }

  // --- exams -----------------------------------------------------------------

  function editExam(exam: Exam | null): void {
    examError = '';
    status = '';
    examDraft = exam
      ? {
          exam_id: exam.exam_id,
          name: exam.name,
          day: exam.day,
          scope: [...exam.scope_decks],
          minutes: exam.minutes == null ? '' : String(exam.minutes),
          problems: exam.problems == null ? '' : String(exam.problems),
          target: exam.target ?? null,
        }
      : { name: '', day: '', scope: [], minutes: '', problems: '', target: null };
  }

  function toggleScope(deck: string, on: boolean): void {
    if (!examDraft) return;
    examDraft.scope = on ? [...examDraft.scope.filter((d) => d !== deck), deck] : examDraft.scope.filter((d) => d !== deck);
  }

  /** '' is "not given"; otherwise a whole number of at least 1, or undefined when it is not one. */
  function count(text: string): number | null | undefined {
    const value = text.trim();
    if (value === '') return null;
    const n = Number(value);
    return Number.isInteger(n) && n >= 1 ? n : undefined;
  }

  async function saveExam(event: SubmitEvent): Promise<void> {
    event.preventDefault();
    if (!settings || !examDraft) return;
    const d = examDraft;
    const minutes = count(d.minutes);
    const problems = count(d.problems);
    if (!d.name.trim()) examError = 'Give the exam a name.';
    else if (!d.day) examError = 'Choose the day of the exam.';
    else if (d.scope.length === 0) examError = 'Choose at least one section the exam covers.';
    else if (minutes === undefined) examError = 'Its length is a whole number of minutes, or leave it empty.';
    else if (problems === undefined) examError = 'The number of problems is a whole number, or leave it empty.';
    else examError = '';
    if (examError) return;
    busy = true;
    try {
      const { api } = await getPractice();
      // Keep the sections in course order, whatever order they were ticked in.
      const scope = settings.sections.map((s) => s.deck).filter((deck) => d.scope.includes(deck));
      const exam: ExamIn = {
        course_id: settings.course_id,
        name: d.name.trim(),
        day: d.day,
        scope_decks: scope,
        target: d.target,
        minutes: minutes ?? null,
        problems: problems ?? null,
      };
      if (d.exam_id !== undefined) exam.exam_id = d.exam_id;
      await api.exam_save(exam);
      exams = (await api.course_settings_get(settings.course_id)).exams;
      examDraft = null;
      status = 'Exam saved.';
    } catch (caught) {
      examError = message(caught);
    } finally {
      busy = false;
    }
  }

  async function deleteExam(exam: Exam): Promise<void> {
    if (!settings) return;
    busy = true;
    examError = '';
    try {
      const { api } = await getPractice();
      await api.exam_delete(exam.exam_id);
      exams = exams.filter((e) => e.exam_id !== exam.exam_id);
      if (examDraft?.exam_id === exam.exam_id) examDraft = null;
      status = `${exam.name} deleted.`;
    } catch (caught) {
      examError = message(caught);
    } finally {
      busy = false;
    }
  }

  function examLine(exam: Exam): string {
    const covers = listText(exam.scope_decks.map((deck) => titles.get(deck) ?? deck));
    const size = [
      exam.minutes ? `${exam.minutes} minutes` : '',
      exam.problems ? `${exam.problems} problem${exam.problems === 1 ? '' : 's'}` : '',
    ].filter(Boolean);
    return `${formatDay(exam.day)}, on ${covers}${size.length ? `. ${size.join(', ')}` : ''}`;
  }
</script>

{#snippet option(name: string, value: string, checked: boolean, label: string, hint: string, onpick: () => void)}
  <label class="option" class:on={checked}>
    <input type="radio" {name} {value} {checked} data-testid={`${name}-${value}`} onchange={onpick} />
    <span class="label">{label}</span>
    {#if hint}<span class="hint">{hint}</span>{/if}
  </label>
{/snippet}

<section class="page" data-testid="page-course">
  <div class="title">
    <h1>Course setup</h1>
    {#if settings}<p class="course muted" data-testid="course-title">{settings.course_title}</p>{/if}
  </div>

  {#if !settings || !draft}
    {#if error}
      <p class="error" role="alert" data-testid="course-error">{error}</p>
    {:else}
      <p class="muted">Loading…</p>
    {/if}
  {:else}
    <form class="form" onsubmit={save} data-testid="course-form">
      <fieldset class="group">
        <legend>Schedule</legend>
        {#if !settings.has_pace}
          <p class="note" data-testid="no-pace">
            No pace data. This course's pack doesn't say how many class hours each section takes, so the app can't
            date its sections. Targets and exams still apply.
          </p>
        {:else}
          <div class="options" role="radiogroup" aria-label="How the schedule is set">
            {#each MODES as mode (mode.id)}
              {@render option('schedule', mode.id, draft.mode === mode.id, mode.label, mode.hint, () => draft && (draft.mode = mode.id))}
            {/each}
          </div>
          {#if draft.mode === 'date'}
            <label class="field">
              <span class="label">First class</span>
              <input type="date" bind:value={draft.start} data-testid="start" />
            </label>
          {:else if draft.mode === 'aligned'}
            <label class="field">
              <span class="label">Section your class is at today</span>
              <select value={draft.aligned_deck} data-testid="aligned" onchange={(e) => pickSection(e.currentTarget.value)}>
                <option value="" disabled>Choose a section</option>
                {#each settings.sections as section (section.deck)}
                  <option value={section.deck}>{section.title}</option>
                {/each}
              </select>
            </label>
            {#if draft.aligned_deck && draft.aligned_day !== today}
              <p class="hint" data-testid="aligned-day">You set this on {formatDay(draft.aligned_day)}.</p>
            {/if}
          {/if}
          <label class="field">
            <span class="label">Class pace <output class="tabular" data-testid="pace-value">{draft.pace.toFixed(2)}×</output></span>
            <input
              type="range"
              min="0.75"
              max="1.5"
              step="0.05"
              bind:value={draft.pace}
              aria-valuetext={`${draft.pace.toFixed(2)} times the standard pace`}
              data-testid="pace"
            />
            <span class="hint">How fast your class moves against the standard. Higher reaches each section sooner.</span>
          </label>
        {/if}
        <label class="field">
          <span class="label">Course end (optional)</span>
          <input type="date" bind:value={draft.end} data-testid="end" />
          <span class="hint">
            After it, skills only stay fresh: {Math.round(settings.keep_target * 100)}% at tier {settings.keep_tier}. Leave it
            empty for self-study.
          </span>
        </label>
      </fieldset>

      <fieldset class="group">
        <legend>Targets</legend>
        <label class="field">
          <span class="label">Accuracy target <output class="tabular" data-testid="accuracy-value">{draft.accuracy}%</output></span>
          <input
            type="range"
            min="80"
            max="95"
            step="1"
            bind:value={draft.accuracy}
            aria-valuetext={`${draft.accuracy} percent`}
            data-testid="accuracy"
          />
          <span class="hint">The chance of getting a problem you haven't seen right on the first try.</span>
        </label>
        <div class="field">
          <span class="label" id="tier-label">Target tier</span>
          <div class="options three" role="radiogroup" aria-labelledby="tier-label">
            {#each TIERS as tier (tier)}
              {@render option('tier', String(tier), draft.tier === tier, `${tier}: ${TIER_WORDS[tier]?.label ?? ''}`, TIER_WORDS[tier]?.hint ?? '', () => draft && (draft.tier = tier))}
            {/each}
          </div>
        </div>
        <div class="field">
          <span class="label" id="band-label">Practice difficulty</span>
          <div class="options" role="radiogroup" aria-labelledby="band-label">
            {#each BANDS as band (band.id)}
              {@render option('band', band.id, draft.band === band.id, band.label, band.hint, () => draft && (draft.band = band.id))}
            {/each}
          </div>
        </div>
      </fieldset>

      {#if error}<p class="error" role="alert" data-testid="course-error">{error}</p>{/if}
      <div class="row">
        <Button variant="primary" type="submit" disabled={busy} data-testid="save-course">Save changes</Button>
        <Button variant="quiet" data-testid="back-library" onclick={() => navigate('library')}>Back to the Library</Button>
        {#if status}<p class="status" role="status" data-testid="course-status">{status}</p>{/if}
      </div>
    </form>

    <section class="group" aria-labelledby="exams-title" data-testid="exams-setup">
      <h2 id="exams-title">Exams</h2>
      {#if exams.length === 0}
        <p class="muted" data-testid="no-exams">No exams yet. An exam moves the exam level of the sections it covers to two days before it.</p>
      {:else}
        <ul class="exams">
          {#each exams as exam (exam.exam_id)}
            <li data-testid="exam" data-id={exam.exam_id}>
              <span class="exam-text">
                <span class="name">{exam.name}</span>
                <span class="muted">{examLine(exam)}</span>
              </span>
              <span class="exam-actions">
                <Button variant="quiet" disabled={busy} data-testid="edit-exam" onclick={() => editExam(exam)}>Edit</Button>
                <Button variant="quiet" disabled={busy} data-testid="delete-exam" onclick={() => deleteExam(exam)}>Delete</Button>
              </span>
            </li>
          {/each}
        </ul>
      {/if}

      {#if examDraft}
        {@const d = examDraft}
        <form class="exam-form" onsubmit={saveExam} data-testid="exam-form">
          <label class="field">
            <span class="label">Name</span>
            <input type="text" bind:value={d.name} maxlength="80" autocomplete="off" data-testid="exam-name" />
          </label>
          <label class="field">
            <span class="label">Day</span>
            <input type="date" bind:value={d.day} data-testid="exam-day" />
          </label>
          <fieldset class="field scope">
            <legend class="label">Sections it covers</legend>
            {#each settings.sections as section (section.deck)}
              <label class="check">
                <input
                  type="checkbox"
                  checked={d.scope.includes(section.deck)}
                  data-testid="exam-section"
                  data-deck={section.deck}
                  onchange={(e) => toggleScope(section.deck, e.currentTarget.checked)}
                />
                {section.title}
              </label>
            {/each}
          </fieldset>
          <div class="pair">
            <label class="field">
              <span class="label">Length in minutes (optional)</span>
              <input type="number" min="1" step="1" value={d.minutes} oninput={(e) => (d.minutes = e.currentTarget.value)} data-testid="exam-minutes" />
            </label>
            <label class="field">
              <span class="label">Problems (optional)</span>
              <input type="number" min="1" step="1" value={d.problems} oninput={(e) => (d.problems = e.currentTarget.value)} data-testid="exam-problems" />
            </label>
          </div>
          {#if examError}<p class="error" role="alert" data-testid="exam-error">{examError}</p>{/if}
          <div class="row">
            <Button variant="primary" type="submit" disabled={busy} data-testid="save-exam">Save exam</Button>
            <Button variant="quiet" data-testid="cancel-exam" onclick={() => (examDraft = null)}>Cancel</Button>
          </div>
        </form>
      {:else}
        {#if examError}<p class="error" role="alert" data-testid="exam-error">{examError}</p>{/if}
        <div><Button variant="secondary" data-testid="add-exam" onclick={() => editExam(null)}>Add an exam</Button></div>
      {/if}
    </section>
  {/if}
</section>

<style>
  .page {
    display: grid;
    gap: var(--sp-4);
    max-width: 40rem;
    padding: var(--sp-6) var(--sp-5);
  }

  .title {
    display: grid;
    gap: var(--sp-0);
  }

  .course {
    font-size: var(--fs-title);
  }

  .form,
  .exam-form {
    display: grid;
    gap: var(--sp-4);
  }

  .exam-form {
    gap: var(--sp-2);
    padding: var(--sp-2) var(--sp-3);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--surface);
  }

  .group {
    display: grid;
    gap: var(--sp-2);
    margin: 0;
    padding: 0;
    border: 0;
  }

  legend,
  h2 {
    padding: 0;
    margin-bottom: var(--sp-1);
    font-size: 1.125rem;
    font-weight: 600;
  }

  .field {
    display: grid;
    gap: var(--sp-0);
    margin: 0;
    padding: 0;
    border: 0;
  }

  .label {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: var(--sp-1);
    font-weight: 600;
  }

  .hint {
    color: var(--text-muted);
    font-size: var(--fs-small);
  }

  .note {
    color: var(--text-muted);
  }

  input[type='date'],
  input[type='text'],
  input[type='number'],
  select {
    min-height: 40px;
    max-width: 22rem;
    padding: 0 var(--sp-1);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--surface);
    color: var(--text);
    font: inherit;
  }

  input[type='range'] {
    accent-color: var(--accent);
  }

  output {
    font-weight: 500;
  }

  .options {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr));
    gap: var(--sp-1);
  }

  .option {
    position: relative;
    display: grid;
    align-content: start;
    gap: 2px;
    padding: var(--sp-1) var(--sp-2);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--surface);
    cursor: pointer;
  }

  .option.on {
    border-color: var(--accent);
    background: var(--selection);
  }

  .option:has(input:focus-visible) {
    outline: var(--focus-width) solid var(--accent);
    outline-offset: 2px;
  }

  .option input {
    position: absolute;
    opacity: 0;
    pointer-events: none;
  }

  .row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--sp-1);
  }

  .status {
    color: var(--text-muted);
  }

  .error {
    color: var(--incorrect);
  }

  .exams {
    display: grid;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .exams li {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: var(--sp-1);
    padding: var(--sp-1) 0;
    border-top: 1px solid var(--border);
  }

  .exam-text {
    display: grid;
    flex: 1 1 18rem;
  }

  .exam-text .name {
    font-weight: 600;
  }

  .exam-actions {
    display: flex;
    gap: var(--sp-0);
    margin-inline-start: auto;
  }

  .scope {
    gap: var(--sp-0);
  }

  .check {
    display: flex;
    align-items: center;
    gap: var(--sp-1);
    min-height: 32px;
  }

  .check input {
    width: 1.125rem;
    height: 1.125rem;
    accent-color: var(--accent);
  }

  .pair {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
    gap: var(--sp-2);
  }
</style>
