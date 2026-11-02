<script lang="ts">
  import { untrack } from 'svelte';
  import Button from '../components/Button.svelte';
  import Icon from '../components/Icon.svelte';
  import { userMessage } from '../lib/bridge';
  import { formatDay, formatPercent } from '../lib/format';
  import { MILESTONE_WORDS, stateWords, TRACK_WORDS } from '../lib/plan-words';
  import { getPractice } from '../lib/practice-api';
  import { navigate, router } from '../lib/router.svelte';
  import type { LibraryCourse, MilestoneView, SkillRow, SkillsView } from '../lib/types';

  let courses = $state<LibraryCourse[]>([]);
  let view = $state<SkillsView | null>(null);
  let courseTitle = $state('');
  /** Section titles in course order (from the course's settings). */
  let sections = $state<{ deck: string; title: string }[]>([]);
  let error = $state('');
  let onlyBehind = $state(false);

  $effect(() => {
    const course = router.params.course;
    onlyBehind = router.params.filter === 'behind';
    untrack(() => void load(course));
  });

  async function load(course: string | undefined): Promise<void> {
    error = '';
    try {
      const { api } = await getPractice();
      courses = (await api.library_get()).courses;
      const id = course ?? courses[0]?.id;
      if (!id) {
        view = null;
        error = 'There are no courses yet. Packs and imported cards appear in the Library.';
        return;
      }
      const [skills, settings] = await Promise.all([api.skills_get(id), api.course_settings_get(id)]);
      view = skills;
      courseTitle = settings.course_title;
      sections = settings.sections.map((s) => ({ deck: s.deck, title: s.title }));
    } catch (caught) {
      error = userMessage(caught) ?? (caught instanceof Error ? caught.message : String(caught));
    }
  }

  const behindCount = $derived((view?.skills ?? []).filter((s) => s.track === 'behind').length);

  /** The skills grouped by section, in course order; skills of a deck the course doesn't list come last. */
  const groups = $derived.by(() => {
    const shown = (view?.skills ?? []).filter((s) => !onlyBehind || s.track === 'behind');
    const order = new Map(sections.map((s, i) => [s.deck, i]));
    const byDeck = new Map<string, SkillRow[]>();
    for (const skill of shown) byDeck.set(skill.deck, [...(byDeck.get(skill.deck) ?? []), skill]);
    return [...byDeck.entries()]
      .sort(([a], [b]) => (order.get(a) ?? Infinity) - (order.get(b) ?? Infinity))
      .map(([deck, skills]) => ({
        deck,
        title: sections.find((s) => s.deck === deck)?.title ?? deck.split('::').at(-1) ?? deck,
        skills,
      }));
  });

  /** The filter changes on the page only: no reload (#/skills?filter=behind only sets where it starts). */
  function setFilter(on: boolean): void {
    onlyBehind = on;
  }

  function milestoneText(m: MilestoneView): string {
    const name = MILESTONE_WORDS[m.name] ?? m.name;
    return m.deadline ? `${name}, tier ${m.tier}, by ${formatDay(m.deadline)}` : `${name}, tier ${m.tier}`;
  }

  function paceText(ok: boolean | null): string {
    if (ok === null) return 'No timed first try yet';
    return ok ? 'At pace' : 'Slower than the standard time';
  }
</script>

<section class="page" data-testid="page-skills">
  <div class="head">
    <div class="title">
      <h1>Skills</h1>
      {#if view}
        <p class="muted" data-testid="skills-course">{courseTitle} on {formatDay(view.day)}</p>
      {/if}
    </div>
    <div class="controls">
      {#if courses.length > 1 && view}
        <label class="course-pick">
          <span class="sr-only">Course</span>
          <select value={view.course_id} data-testid="skills-course-pick" onchange={(e) => navigate('skills', { course: e.currentTarget.value })}>
            {#each courses as course (course.id)}
              <option value={course.id}>{course.title}</option>
            {/each}
          </select>
        </label>
      {/if}
      {#if view}
        <Button
          variant={onlyBehind ? 'primary' : 'secondary'}
          aria-pressed={onlyBehind}
          data-testid="filter-behind"
          onclick={() => setFilter(!onlyBehind)}>Only behind ({behindCount})</Button
        >
      {/if}
    </div>
  </div>

  {#if error}
    <p class="error" role="alert" data-testid="skills-error">{error}</p>
  {:else if !view}
    <p class="muted">Loading…</p>
  {:else if groups.length === 0}
    <p class="muted" data-testid="skills-empty">
      {onlyBehind ? 'No skill is behind its milestones.' : 'This course has no skills yet.'}
    </p>
  {:else}
    {#each groups as group (group.deck)}
      <section class="section" data-testid="skills-section" data-deck={group.deck}>
        <h2>{group.title}</h2>
        <ul class="skills">
          {#each group.skills as skill (skill.skill_id)}
            {@const state = stateWords(skill.state)}
            <li class="skill" data-testid="skill" data-id={skill.skill_id} data-track={skill.track} data-state={skill.state}>
              <div class="line">
                <span class="name">{skill.name}</span>
                <span class="status">
                  <span class="state" title={state.hint} data-testid="skill-state">{state.label}</span>
                  <span class={`track ${skill.track}`} data-testid="skill-track">
                    <Icon name={skill.track === 'behind' ? 'alert' : 'check-circle'} size={1} />
                    {TRACK_WORDS[skill.track] ?? skill.track}
                  </span>
                  {#if skill.set_aside}
                    <span class="aside" data-testid="skill-set-aside">Set aside today</span>
                  {/if}
                </span>
              </div>
              {#if skill.state === 'not-introduced' && skill.intro}
                <p class="detail muted">Starts {formatDay(skill.intro)}.</p>
              {/if}
              <ul class="milestones" aria-label={`Milestones of ${skill.name}`}>
                {#each skill.milestones as m (m.name)}
                  <li class:certified={m.certified} data-testid="milestone" data-name={m.name} data-certified={m.certified}>
                    {#if m.certified}<Icon name="check" size={1} />{/if}<span
                      >{milestoneText(m)}{#if m.certified}<span class="sr-only">, certified</span>{/if}</span
                    >
                  </li>
                {/each}
              </ul>
              <dl class="numbers">
                <div>
                  <dt>Level</dt>
                  <dd class="tabular" data-testid="skill-level">{skill.level === null ? 'None yet' : `Tier ${skill.level}`}</dd>
                </div>
                <div>
                  <dt>First-try chance</dt>
                  <dd class="tabular" data-testid="skill-readiness">{skill.readiness === null ? 'Not yet' : formatPercent(skill.readiness)}</dd>
                </div>
                <div>
                  <dt>Speed</dt>
                  <dd data-testid="skill-pace">{paceText(skill.pace_ok)}</dd>
                </div>
              </dl>
            </li>
          {/each}
        </ul>
      </section>
    {/each}
  {/if}
</section>

<style>
  .page {
    display: grid;
    gap: var(--sp-3);
    max-width: 56rem;
    padding: var(--sp-6) var(--sp-5);
  }

  .head {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    justify-content: space-between;
    gap: var(--sp-2);
  }

  .title {
    display: grid;
    gap: var(--sp-0);
  }

  .controls {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--sp-1);
  }

  select {
    min-height: 40px;
    padding: 0 var(--sp-1);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--surface);
    color: var(--text);
    font: inherit;
  }

  .section {
    display: grid;
    gap: var(--sp-1);
    padding: var(--sp-3);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--surface);
  }

  h2 {
    font-size: 1.125rem;
  }

  .skills {
    display: grid;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .skill {
    display: grid;
    gap: var(--sp-1);
    padding: var(--sp-2) 0;
    border-top: 1px solid var(--border);
  }

  .line {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: var(--sp-1);
  }

  .name {
    font-weight: 600;
  }

  .status {
    display: inline-flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--sp-1);
    font-size: var(--fs-small);
  }

  .state {
    color: var(--text-muted);
  }

  .track {
    display: inline-flex;
    align-items: center;
    gap: var(--sp-0);
    font-weight: 600;
  }

  .track.ahead,
  .track.on-track {
    color: var(--correct);
  }

  .track.behind {
    color: var(--incorrect);
  }

  .aside {
    padding: 0 var(--sp-1);
    border: 1px solid var(--border);
    border-radius: 999px;
    color: var(--text-muted);
  }

  .detail {
    font-size: var(--fs-small);
  }

  .milestones {
    display: flex;
    flex-wrap: wrap;
    gap: var(--sp-1);
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .milestones li {
    display: inline-flex;
    align-items: center;
    gap: var(--sp-0);
    padding: 2px var(--sp-1);
    border: 1px solid var(--border);
    border-radius: 999px;
    color: var(--text-muted);
    font-size: var(--fs-caption);
  }

  .milestones li.certified {
    border-color: var(--correct);
    color: var(--correct);
  }

  .numbers {
    display: flex;
    flex-wrap: wrap;
    gap: var(--sp-1) var(--sp-4);
    margin: 0;
    font-size: var(--fs-small);
  }

  .numbers div {
    display: flex;
    gap: var(--sp-1);
  }

  dt {
    color: var(--text-muted);
  }

  dd {
    margin: 0;
  }

  .error {
    color: var(--incorrect);
  }
</style>
