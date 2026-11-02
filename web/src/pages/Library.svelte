<script lang="ts">
  import { onMount } from 'svelte';
  import Button from '../components/Button.svelte';
  import { userMessage } from '../lib/bridge';
  import { getPractice } from '../lib/practice-api';
  import { navigate } from '../lib/router.svelte';
  import type { Library, SectionState } from '../lib/types';

  /** The four section states (spec: Library, scope and onboarding). */
  const STATES: readonly { id: SectionState; label: string; hint: string }[] = [
    { id: 'off', label: 'Off', hint: 'Not being studied' },
    { id: 'learning', label: 'Learning now', hint: 'Taught in class now: new skills come a few a day' },
    { id: 'covered', label: 'Covered', hint: 'Taught before, partly known' },
    { id: 'solid', label: 'Solid', hint: 'Known well' },
  ];

  let library = $state<Library | null>(null);
  let error = $state('');
  let busy = $state(false);

  onMount(() => {
    void load();
  });

  async function load(): Promise<void> {
    try {
      const { api } = await getPractice();
      library = await api.library_get();
    } catch (caught) {
      error = userMessage(caught) ?? (caught instanceof Error ? caught.message : String(caught));
    }
  }

  /** A course or unit sets all its sections (LIB-1); switching off keeps progress (LIB-6). */
  async function setState(id: string, state: SectionState): Promise<void> {
    busy = true;
    try {
      const { api } = await getPractice();
      library = await api.library_set_state({ id, state });
      error = '';
    } catch (caught) {
      error = userMessage(caught) ?? (caught instanceof Error ? caught.message : String(caught));
    } finally {
      busy = false;
    }
  }
</script>

{#snippet states(id: string, current: string, title: string)}
  <div class="states" role="group" aria-label={`State of ${title}`}>
    {#each STATES as option (option.id)}
      <button
        type="button"
        class="state"
        class:on={current === option.id}
        aria-pressed={current === option.id}
        title={option.hint}
        disabled={busy}
        data-testid={`state-${option.id}`}
        onclick={() => setState(id, option.id)}>{option.label}</button
      >
    {/each}
    {#if current === 'mixed'}<span class="mixed muted" data-testid="state-mixed">Mixed</span>{/if}
  </div>
{/snippet}

<section class="page" data-testid="page-library">
  <h1>Library</h1>
  <p class="lead muted">
    Choose what is in play. Mark a section <strong>Learning now</strong> while it is taught in class; mark what you
    already know <strong>Covered</strong> or <strong>Solid</strong>. Switching a section off never deletes progress.
  </p>
  {#if error}
    <p class="error" role="alert" data-testid="library-error">{error}</p>
  {/if}
  {#if library}
    {#if library.courses.length === 0}
      <p class="muted" data-testid="library-empty">No courses yet. Packs and imported cards appear here.</p>
    {/if}
    {#each library.courses as course (course.id)}
      <section class="course" data-testid="course" data-id={course.id}>
        <div class="row head">
          <h2>{course.title}</h2>
          {@render states(course.id, course.state, course.title)}
        </div>
        <div class="links">
          <Button variant="secondary" data-testid="course-setup" onclick={() => navigate('course', { course: course.id })}
            >Course setup</Button
          >
          <Button variant="quiet" data-testid="course-skills" onclick={() => navigate('skills', { course: course.id })}
            >Skills</Button
          >
        </div>
        {#each course.units as unit (unit.id)}
          <div class="unit" data-testid="unit" data-id={unit.id}>
            <div class="row">
              <h3>{unit.title}</h3>
              {@render states(unit.id, unit.state, unit.title)}
            </div>
            <ul class="sections">
              {#each unit.sections as section (section.id)}
                <li class="row" data-testid="section" data-id={section.id} data-state={section.state}>
                  <span class="title">
                    {section.title}
                    <span class="muted small">
                      {section.skills} skill{section.skills === 1 ? '' : 's'}{section.textbook_ref ? ` · ${section.textbook_ref}` : ''}
                    </span>
                    {#if section.small_pool_skills.length > 0}
                      <span class="muted small" data-testid="small-pool">
                        Few problems for {section.small_pool_skills.join(', ')}: learned after all of them in a row.
                      </span>
                    {/if}
                  </span>
                  {@render states(section.id, section.state, section.title)}
                </li>
              {/each}
            </ul>
          </div>
        {/each}
      </section>
    {/each}
  {:else if !error}
    <p class="muted">Loading…</p>
  {/if}
</section>

<style>
  .page {
    display: grid;
    gap: var(--sp-3);
    max-width: 56rem;
    padding: var(--sp-6) var(--sp-5);
  }

  .lead {
    max-width: 40rem;
  }

  h2,
  h3 {
    margin: 0;
  }

  h3 {
    font-size: 1rem;
  }

  .course {
    display: grid;
    gap: var(--sp-2);
    padding: var(--sp-3);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--surface);
  }

  .unit {
    display: grid;
    gap: var(--sp-1);
  }

  .links {
    display: flex;
    flex-wrap: wrap;
    gap: var(--sp-1);
  }

  .row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: var(--sp-1);
  }

  .sections {
    display: grid;
    gap: var(--sp-0);
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .sections li {
    padding: var(--sp-1) 0;
    border-top: 1px solid var(--border);
  }

  .title {
    display: grid;
  }

  .small {
    font-size: var(--fs-caption);
  }

  .states {
    display: inline-flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 2px;
  }

  .state {
    min-height: 32px;
    padding: 0 var(--sp-1);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: transparent;
    color: var(--text-muted);
    font: inherit;
    font-size: var(--fs-small);
  }

  .state.on {
    border-color: var(--accent);
    background: var(--selection);
    color: var(--text);
    font-weight: 600;
  }

  .mixed {
    margin-inline-start: var(--sp-1);
    font-size: var(--fs-caption);
  }

  .error {
    color: var(--incorrect);
  }
</style>
