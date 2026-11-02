<script lang="ts">
  import { onMount, setContext, tick } from 'svelte';
  import Button from '../components/Button.svelte';
  import ChoiceList from '../components/ChoiceList.svelte';
  import HintLadder from '../components/HintLadder.svelte';
  import Icon from '../components/Icon.svelte';
  import Markdown from '../components/Markdown.svelte';
  import MathAnswer from '../components/MathAnswer.svelte';
  import PauseOverlay from '../components/PauseOverlay.svelte';
  import ProblemView from '../components/ProblemView.svelte';
  import SessionSummary from '../components/SessionSummary.svelte';
  import StepSolution from '../components/StepSolution.svelte';
  import StillWorking from '../components/StillWorking.svelte';
  import StudyHeader from '../components/StudyHeader.svelte';
  import VerdictBadge from '../components/VerdictBadge.svelte';
  import VerdictPanel from '../components/VerdictPanel.svelte';
  import WhatWentWrong from '../components/WhatWentWrong.svelte';
  import { CARD_CONTEXT, type CardContext } from '../lib/card-media';
  import { getPractice } from '../lib/practice-api';
  import { navigate, router } from '../lib/router.svelte';
  import { actionForKey, isTypingTarget, ownsActivationKeys } from '../lib/shortcuts';
  import {
    RATINGS,
    SELF_GRADES,
    StudySession,
    choiceItems,
    isChoicePart,
    isFindError,
    partId,
  } from '../lib/study-session.svelte';
  import { ui } from '../lib/ui.svelte';
  import type { StartRequest } from '../lib/types';

  let session: StudySession | undefined = $state();
  let mock = $state(false);
  let contentEl: HTMLElement | undefined = $state();
  let reviewEl: HTMLElement | undefined = $state();
  let answerRefs: Record<string, MathAnswer | undefined> = $state({});
  let pickerEl: HTMLElement | undefined = $state();

  // Text drawn below this page (prompt, back, solution) shows the open card's images (ADR-0017).
  setContext<CardContext>(CARD_CONTEXT, {
    get cardId() {
      return session?.problem?.card.id ?? null;
    },
  });

  const MODES = ['daily', 'lighter', 'focused', 'extra', 'practice-test'] as const;

  /** #/study resumes today's session or starts it; #/study?mode=extra starts that kind. */
  function startRequest(params: Record<string, string>): StartRequest | null {
    const mode = MODES.find((m) => m === params.mode);
    if (!mode) return null;
    const exam = Number(params.exam);
    return { mode, exam_id: Number.isInteger(exam) && params.exam ? exam : null, timed: params.timed === '1' };
  }

  function onKeydown(event: KeyboardEvent): void {
    const s = session;
    if (!s || event.defaultPrevented || event.isComposing) return;
    const action = actionForKey(event, isTypingTarget(event.target));
    if (!action) return;
    // A focused button or link owns Enter and Space.
    if ((event.key === 'Enter' || event.key === ' ') && ownsActivationKeys(event.target)) return;
    if (action.type === 'focus_mode') {
      ui.focusMode = !ui.focusMode;
      event.preventDefault();
      return;
    }
    const handled = s.perform(action);
    // Space would otherwise scroll the page.
    if (handled || action.type === 'continue') {
      event.preventDefault();
      event.stopPropagation();
    }
  }

  onMount(() => {
    ui.focusMode = true;
    let alive = true;
    let detach = (): void => {};
    window.addEventListener('keydown', onKeydown, true);
    void (async () => {
      const binding = await getPractice();
      if (!alive) return;
      mock = binding.mock;
      const created = new StudySession(binding.api);
      detach = created.attach();
      created.syncFields = () => {
        for (const part of created.openParts) {
          const id = partId(part);
          const state = created.parts[id];
          const value = answerRefs[id]?.read();
          if (!state || value === undefined) continue;
          if (state.mode === 'math') state.latex = value;
          else state.text = value;
        }
      };
      session = created;
      await created.begin(startRequest(router.params));
    })();
    return () => {
      alive = false;
      window.removeEventListener('keydown', onKeydown, true);
      detach();
    };
  });

  const PICKER_GAP = 16; // px of air between the picker and the action bar

  /** After a miss: the keyboard goes to the "What went wrong?" picker (the digits pick, Space
   * does not), and the picker is scrolled clear of the sticky action bar, so its options and
   * the "Pick one to continue" note are on screen instead of hiding below the fold. */
  function revealPicker(picker: HTMLElement): void {
    picker.focus({ preventScroll: true });
    const bar = contentEl?.querySelector<HTMLElement>('[data-testid="actions"]');
    const floor = (bar ? bar.getBoundingClientRect().top : window.innerHeight) - PICKER_GAP;
    const { top, bottom } = picker.getBoundingClientRect();
    let delta = 0;
    if (bottom > floor) delta = bottom - floor;
    else if (top < 0) delta = Math.max(top, bottom - floor);
    if (delta !== 0) window.scrollBy({ top: delta, behavior: 'auto' });
  }

  // Keep the keyboard where the student needs it: the answer box while answering, the
  // review region once the item is finished (so Space and the digits work).
  $effect(() => {
    const s = session;
    if (!s) return;
    void s.focusToken;
    const { phase, paused } = s;
    if (paused) return;
    // After the DOM update, and after any element that held focus (the pause overlay's
    // Resume button) has gone: a timeout, not just tick().
    void tick().then(() => window.setTimeout(() => {
      if (s.phase !== phase || s.paused) return;
      if (phase === 'answering') {
        const open = s.openParts.filter((p) => !isChoicePart(p));
        // Find-the-error: the digits pick the step and reason first, so no box has focus yet.
        const waiting = isFindError(s.problem) && !s.findReady;
        const target = waiting ? undefined : (open.find((p) => partId(p) === s.activePartId) ?? open[0]);
        const ref = target ? answerRefs[partId(target)] : undefined;
        if (ref) ref.focus();
        else contentEl?.focus();
      } else if (phase === 'review' && s.mustDiagnose && pickerEl) {
        revealPicker(pickerEl);
      } else if (phase === 'review' || phase === 'self-grade' || phase === 'back' || phase === 'front' || phase === 'example') {
        (reviewEl ?? contentEl)?.focus();
      } else if (phase === 'summary' || phase === 'empty') {
        contentEl?.querySelector<HTMLElement>('[data-testid="summary-home"]')?.focus();
      }
    }, 0));
  });

  /** Clicking Hint takes the keyboard off the answer box; the focus effect gives it back to
   * the box the student was in. */
  async function showHint(s: StudySession): Promise<void> {
    await s.hint();
    s.focusToken += 1;
  }

  function goHome(): void {
    navigate('home');
  }

  function itemLabel(s: StudySession): string | null {
    const kind = s.problem?.kind;
    if (kind === 'flashcard') return 'Flashcard';
    if (kind === 'example') return 'Worked example';
    return null;
  }
</script>

<div
  class="study"
  data-testid="study"
  data-phase={session?.phase ?? 'loading'}
  data-paused={session?.paused ?? false}
  data-kind={session?.problem?.kind ?? ''}
  data-card-kind={session?.problem?.card.kind ?? ''}
  data-item={session?.problem?.item_key ?? ''}
>
  {#if session}
    {@const s = session}
    <div class="frame">
      <StudyHeader
        progress={s.progress}
        reason={s.problem?.reason ?? null}
        itemLabel={itemLabel(s)}
        lighter={s.lighter}
        canLighter={!!s.problem && (s.turn?.mode === 'daily' || s.turn?.mode === 'lighter')}
        canEnd={!!s.problem && s.phase !== 'checking'}
        reasonOpen={s.reasonOpen}
        paused={s.paused}
        showPause={s.phase !== 'summary' && s.phase !== 'empty' && s.phase !== 'error'}
        canPause={s.phase === 'answering' || s.phase === 'front' || s.phase === 'back' || s.phase === 'example' || s.paused}
        focusMode={ui.focusMode}
        onreason={(open) => (s.reasonOpen = open)}
        onpause={() => s.togglePause()}
        onfocusmode={() => (ui.focusMode = !ui.focusMode)}
        onlighter={(on) => s.setLighter(on)}
        onend={() => s.end()}
      />

      {#if mock}
        <p class="sample" data-testid="sample-banner">Sample problems: no Python bridge, so this is not your library.</p>
      {/if}
      {#if s.breakDue}
        <p class="break" role="status" data-testid="break-note">
          <Icon name="info" size={1.125} /> You have been studying for a while. A short break helps.
          <button type="button" class="link" onclick={() => (s.breakDue = false)}>Dismiss</button>
        </p>
      {/if}
    </div>

    <div class="stage" class:paused={s.paused}>
      <div
        class="content"
        class:blurred={s.paused}
        bind:this={contentEl}
        tabindex="-1"
        inert={s.paused}
        data-testid="study-content"
      >
        {#if s.phase === 'summary' && s.summary}
          <SessionSummary summary={s.summary} onhome={goHome} onmore={() => s.startMore('extra')} />
        {:else if s.phase === 'empty'}
          <section class="empty" data-testid="study-empty">
            <p>{s.turn?.message || 'Nothing to study right now.'}</p>
            <div class="row">
              <Button variant="primary" data-testid="summary-home" onclick={goHome}>Back to Home</Button>
              {#if s.turn?.mode === 'daily' || s.turn?.mode === 'lighter'}
                <Button variant="quiet" data-testid="empty-extra" onclick={() => s.startMore('extra')}>Extra practice</Button>
              {/if}
            </div>
          </section>
        {:else if s.phase === 'error'}
          <p class="error" role="alert" data-testid="study-error">{s.errorMessage}</p>
          <div class="row"><Button variant="primary" data-testid="summary-home" onclick={goHome}>Back to Home</Button></div>
        {:else if s.problem}
          {@const problem = s.problem}
          {@const card = problem.card}
          {@const reviewing = s.phase === 'review' || s.phase === 'self-grade'}
          {@const flashcard = problem.kind === 'flashcard'}
          {@const findError = isFindError(problem)}
          <div class="card" class:wide={reviewing && findError}>
            <ProblemView prompt={card.prompt_md} calculator={card.calculator} degrees={card.angles === 'degrees'} />

            {#if problem.kind === 'example'}
              <div class="worked" tabindex="-1" bind:this={reviewEl} data-testid="example">
                <h3>Worked example</h3>
                <Markdown source={card.solution_md ?? card.back_md ?? ''} />
              </div>
            {:else if flashcard && (s.phase === 'front' || s.phase === 'back') && !s.answerParts.length}
              <div class="flash" tabindex="-1" bind:this={reviewEl} data-testid="flashcard">
                {#if s.phase === 'back'}
                  <div class="back" data-testid="flashcard-back"><Markdown source={card.back_md ?? ''} /></div>
                {/if}
              </div>
            {:else if !reviewing && s.phase !== 'back'}
              {#if findError}
                <!-- Find the error: pick the wrong step (given when highlighted), then why, then the fix. -->
                <div class="find" data-testid="find-error">
                  {#if card.error_step !== null}
                    <h3 data-testid="highlighted-step">Step {card.error_step} is wrong. Why?</h3>
                    <StepSolution steps={card.shown_work} flagged={card.error_step} label="Another student's work" showSkill={false} />
                  {:else}
                    <h3>Which step is wrong?</h3>
                    <StepSolution
                      steps={card.shown_work}
                      pickable
                      picked={s.findStep}
                      label="Another student's work"
                      showSkill={false}
                      keys={Object.fromEntries(card.shown_work.map((st, i) => [st.number, String(i + 1)]))}
                      onpick={(number) => s.pickStep(number)}
                    />
                  {/if}
                  {#if s.findStep !== null}
                    {#if card.error_step === null}<h3>Why is it wrong?</h3>{/if}
                    <div class="reasons" role="radiogroup" aria-label="Why the step is wrong">
                      {#each card.reasons as reason (reason.index)}
                        <button
                          type="button"
                          class="reason"
                          class:on={s.findReason === reason.index}
                          role="radio"
                          aria-checked={s.findReason === reason.index}
                          data-testid={`reason-${reason.index + 1}`}
                          onclick={() => s.pickReason(reason.index)}
                        >
                          <kbd aria-hidden="true">{reason.index + 1}</kbd>
                          <span><Markdown source={reason.text_md} inline /></span>
                          {#if s.findReason === reason.index}<Icon name="check" size={1.125} />{/if}
                        </button>
                      {/each}
                    </div>
                  {/if}
                  {#if s.findReady}<h3>Type the corrected answer</h3>{/if}
                </div>
              {/if}
              {#if s.answerParts.length > 0 && (!findError || s.findReady)}
                <div class="parts" data-testid="parts">
                  {#each s.answerParts as part (partId(part))}
                    {@const id = partId(part)}
                    {@const state = s.parts[id]}
                    {@const verdict = state?.verdict}
                    {#if state}
                      <div class="part" class:multi={s.answerParts.length > 1} data-testid={`part-${id}`}>
                        {#if part.label}<span class="plabel">({part.label})</span>{/if}
                        <div class="pbody">
                          {#if part.prompt_md}
                            <div class="pprompt"><Markdown source={part.prompt_md} /></div>
                          {/if}
                          {#if isChoicePart(part)}
                            <ChoiceList
                              choices={choiceItems(part)}
                              selected={state.choices}
                              disabled={s.isSettled(id)}
                              label={part.label ? `Choices for part ${part.label}` : 'Choices'}
                              onpick={(choice) => s.toggleChoice(id, choice, false)}
                            />
                          {:else}
                            <MathAnswer
                              bind:this={answerRefs[id]}
                              partId={id}
                              label={part.label ? `Answer for part ${part.label}` : 'Answer'}
                              answerType={part.answer_type}
                              mode={state.mode}
                              latex={state.latex}
                              text={state.text}
                              preview={state.preview}
                              readonly={s.isSettled(id)}
                              onvalue={(mode, value) => s.setValue(id, mode, value)}
                              onmode={(mode) => s.setMode(id, mode)}
                              onactive={() => (s.activePartId = id)}
                            />
                          {/if}
                          {#if verdict}
                            <div class="pverdict" data-testid={`verdict-${id}`} data-kind={verdict.status}>
                              {#if verdict.status === 'correct'}
                                <VerdictBadge kind="correct" compact />
                              {:else if verdict.status === 'invalid'}
                                <VerdictBadge kind="invalid" compact />
                                {#if verdict.message}
                                  <span class="vmsg"><Markdown source={verdict.message} inline /></span>
                                {/if}
                              {:else if verdict.status === 'incorrect' && s.isSettled(id)}
                                <VerdictBadge kind="incorrect" compact word="Out of tries" />
                              {:else if verdict.status === 'incorrect' && s.isRetry}
                                <VerdictBadge kind="retry" compact />
                                <span class="vmsg muted tabular"
                                  >Attempt {verdict.tries_used || s.result?.tries_used || 1} of {s.result?.attempts_allowed ?? 2}</span
                                >
                              {/if}
                            </div>
                          {/if}
                        </div>
                      </div>
                    {/if}
                  {/each}
                </div>
              {:else if problem.kind === 'problem' && !findError}
                <p class="self-note" data-testid="self-graded">
                  Work it on paper, then show the solution and grade yourself against it.
                </p>
              {/if}

              <HintLadder hints={s.hints} />

              {#if s.stillWorking}
                <StillWorking onconfirm={() => s.confirmStillWorking()} />
              {/if}
            {/if}

            {#if s.notice}
              <p class="notice" role="status" data-testid="notice"><Icon name="info" size={1.125} /> {s.notice}</p>
            {/if}

            {#if flashcard && s.phase === 'back' && s.result}
              <div class="flash" tabindex="-1" bind:this={reviewEl} data-testid="flashcard">
                <VerdictBadge kind={(s.result.rating ?? 1) >= 2 ? 'correct' : 'incorrect'} />
                {#if card.back_md}<div class="back" data-testid="flashcard-back"><Markdown source={card.back_md} /></div>{/if}
              </div>
            {/if}

            {#if reviewing && s.result}
              {@const solution = s.solution}
              <div class="review" tabindex="-1" bind:this={reviewEl} data-testid="review">
                {#if s.phase === 'self-grade'}
                  <p class="self-note" data-testid="self-grade-note">
                    {s.result.message || 'Compare your work with the solution and grade it yourself.'}
                  </p>
                  {#if s.ticks.length > 0 && solution}
                    <div class="rubric" role="group" aria-label="Steps your work matched" data-testid="rubric">
                      {#each solution.rubric as line, i (i)}
                        <button
                          type="button"
                          class="reason"
                          class:on={s.ticks[i]}
                          role="checkbox"
                          aria-checked={s.ticks[i]}
                          data-testid={`tick-${i + 1}`}
                          onclick={() => s.toggleTick(i)}
                        >
                          <kbd aria-hidden="true">{i + 1}</kbd>
                          <span><Markdown source={line} inline /></span>
                          {#if s.ticks[i]}<Icon name="check" size={1.125} />{/if}
                        </button>
                      {/each}
                    </div>
                  {/if}
                {:else}
                  <VerdictPanel {problem} result={s.result} />
                  {#if s.result.find_error}
                    {@const fe = s.result.find_error}
                    <ul class="picks" data-testid="find-error-outcome">
                      <li><VerdictBadge kind={fe.step_ok ? 'correct' : 'incorrect'} compact word={fe.step_ok ? 'Wrong step found' : 'Wrong step missed'} /></li>
                      <li><VerdictBadge kind={fe.reason_ok ? 'correct' : 'incorrect'} compact word={fe.reason_ok ? 'Reason right' : 'Reason missed'} /></li>
                      <li><VerdictBadge kind={fe.value_ok ? 'correct' : 'incorrect'} compact word={fe.value_ok ? 'Fix right' : 'Fix missed'} /></li>
                    </ul>
                  {/if}
                {/if}

                {#if s.flagMessage}
                  <p class="flag" role="status" data-testid="flag-message">{s.flagMessage}</p>
                {/if}

                {#if solution}
                  <div class="solution">
                    {#if solution.shown_work.length > 0}
                      <div class="side-by-side" data-testid="side-by-side">
                        <section>
                          <h3>Their work</h3>
                          <StepSolution
                            steps={solution.shown_work}
                            flagged={s.result.find_error?.error_step ?? null}
                            label="Another student's work"
                            showSkill={false}
                          />
                        </section>
                        <section>
                          <h3>The correct solution</h3>
                          <StepSolution steps={solution.steps} />
                        </section>
                      </div>
                    {:else if solution.needs_diagnosis && s.phase === 'review'}
                      <WhatWentWrong
                        steps={solution.steps}
                        picked={s.picked}
                        diagnosis={s.diagnosis}
                        bind:el={pickerEl}
                        onpick={(choice, step) => s.diagnose(choice, step)}
                      />
                      {#if solution.steps.length === 0 && solution.solution_md}
                        <h3>Worked solution</h3>
                        <Markdown source={solution.solution_md} />
                      {/if}
                    {:else}
                      <h3>Worked solution</h3>
                      {#if solution.steps.length > 0}
                        <StepSolution steps={solution.steps} />
                      {:else if solution.solution_md}
                        <Markdown source={solution.solution_md} />
                      {:else if solution.answer_md}
                        <p>Answer: <Markdown source={solution.answer_md} inline /></p>
                      {/if}
                    {/if}
                    {#if solution.alternative_md && s.picked?.choice === 'other-method'}
                      <h3>Another method</h3>
                      <div data-testid="alternative"><Markdown source={solution.alternative_md} /></div>
                    {/if}
                  </div>
                {/if}
              </div>
            {/if}
          </div>

          <footer class="actions" data-testid="actions">
            {#if s.phase === 'review'}
              <div class="group">
                <Button
                  variant="primary"
                  shortcut="Space"
                  disabled={s.mustDiagnose}
                  data-testid="continue"
                  onclick={() => s.next()}>Continue</Button
                >
              </div>
              <div class="group">
                {#if s.solution?.can_mark_too_easy}
                  <Button variant="quiet" shortcut="E" data-testid="too-easy" onclick={() => s.flag('too_easy')}>Too easy</Button>
                {/if}
                {#if s.result?.outcome === 'incorrect'}
                  <Button variant="quiet" shortcut="D" data-testid="dispute" onclick={() => s.flag('dispute')}>I was right</Button>
                {/if}
                <Button variant="quiet" shortcut="R" data-testid="report" onclick={() => s.flag('report')}>Report problem</Button>
                <Button variant="quiet" shortcut="U" data-testid="undo" onclick={() => s.undo()}>Undo</Button>
              </div>
            {:else if s.phase === 'answering' && s.answerParts.length === 0}
              <div class="group">
                <Button variant="primary" shortcut="Space" data-testid="show-solution" onclick={() => s.showSolution()}>Show solution</Button>
              </div>
            {:else if s.phase === 'self-grade' && s.ticks.length > 0}
              <div class="group">
                <Button variant="primary" shortcut="⏎" data-testid="rubric-done" onclick={() => s.selfGrade('rubric')}
                  >Done: {s.ticks.filter(Boolean).length} of {s.ticks.length} matched</Button
                >
              </div>
            {:else if s.phase === 'self-grade'}
              <div class="group" role="group" aria-label="Grade yourself">
                {#each SELF_GRADES as option (option.grade)}
                  <Button
                    variant={option.n === 1 ? 'primary' : 'secondary'}
                    shortcut={String(option.n)}
                    data-testid={`self-${option.grade}`}
                    onclick={() => s.selfGrade(option.grade)}>{option.label}</Button
                  >
                {/each}
              </div>
            {:else if s.phase === 'example' || (s.phase === 'back' && s.result)}
              <div class="group">
                <Button variant="primary" shortcut="Space" data-testid="continue" onclick={() => s.next()}>Continue</Button>
              </div>
            {:else if s.phase === 'front'}
              <div class="group">
                <Button variant="primary" shortcut="Space" data-testid="show-back" onclick={() => s.showBack()}>Show answer</Button>
              </div>
            {:else if s.phase === 'back'}
              <div class="group" role="group" aria-label="How well did you remember it?">
                {#each RATINGS as rating (rating.n)}
                  <Button
                    variant={rating.n === 3 ? 'primary' : 'secondary'}
                    shortcut={String(rating.n)}
                    data-testid={`rate-${rating.n}`}
                    onclick={() => s.rate(rating.n)}>{rating.label}</Button
                  >
                {/each}
              </div>
            {:else}
              <div class="group">
                <Button
                  variant="primary"
                  shortcut="⏎"
                  disabled={s.phase === 'checking'}
                  title="Submit (Enter)"
                  data-testid="submit"
                  onclick={() => s.submit('sure')}>Submit</Button
                >
                {#if !flashcard}
                  <Button
                    variant="quiet"
                    shortcut="⇧⏎"
                    disabled={s.phase === 'checking'}
                    title="Submit as unsure (Shift+Enter)"
                    data-testid="submit-unsure"
                    onclick={() => s.submit('unsure')}>Not sure</Button
                  >
                {/if}
              </div>
              <div class="group">
                {#if card.hint_count > 0 && !problem.practice_test}
                  <Button
                    variant="quiet"
                    icon="hint"
                    shortcut="H"
                    disabled={s.hints.length >= card.hint_count || s.phase === 'checking'}
                    title="Show the next hint (H)"
                    data-testid="hint-button"
                    onclick={() => showHint(s)}>Hint</Button
                  >
                {/if}
                {#if problem.kind === 'problem'}
                  <Button
                    variant="quiet"
                    shortcut="G"
                    disabled={s.phase === 'checking'}
                    title="Give up and see the solution (G)"
                    data-testid="give-up"
                    onclick={() => s.giveUp()}>Give up</Button
                  >
                {/if}
              </div>
            {/if}
          </footer>
        {:else}
          <p class="muted">Loading…</p>
        {/if}
      </div>

      {#if s.paused}
        <PauseOverlay kind={s.pauseKind} onresume={() => s.togglePause()} />
      {/if}
    </div>
  {:else}
    <p class="muted">Loading…</p>
  {/if}
</div>

<style>
  .study {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    padding: var(--sp-2) var(--sp-3) 0;
  }

  .frame {
    width: 100%;
    max-width: calc(var(--measure) + 2 * var(--sp-4) + 2 * var(--sp-3));
    margin-inline: auto;
  }

  .sample {
    margin: var(--sp-1) 0 0;
    color: var(--text-muted);
    font-size: var(--fs-caption);
    text-align: center;
  }

  .stage {
    position: relative;
    display: flex;
    flex: 1;
    flex-direction: column;
    width: 100%;
    max-width: calc(var(--measure) + 2 * var(--sp-4) + 2 * var(--sp-3));
    margin: var(--sp-2) auto 0;
  }

  .content {
    display: flex;
    flex: 1;
    flex-direction: column;
    outline: none;
    transition: filter var(--dur) ease-out;
  }

  .content.blurred {
    filter: blur(14px);
    user-select: none;
  }

  .card {
    flex: none;
    margin-bottom: var(--sp-3);
    padding: var(--sp-5) var(--sp-4);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--surface);
  }

  h3 {
    margin: var(--sp-3) 0 var(--sp-1);
    font-size: 1rem;
  }

  .parts {
    display: grid;
    gap: var(--sp-1);
    max-width: var(--measure);
    margin: var(--sp-4) auto 0;
  }

  .parts {
    gap: var(--sp-3);
  }

  .part.multi {
    display: grid;
    grid-template-columns: 2rem 1fr;
    gap: var(--sp-1);
  }

  .plabel {
    padding-top: var(--sp-0);
    color: var(--text-muted);
    font-weight: 600;
  }

  .pbody {
    display: grid;
    gap: var(--sp-1);
  }

  .pprompt {
    font-family: var(--font-text);
    font-size: var(--fs-problem);
    line-height: var(--lh-problem);
  }

  .pverdict {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--sp-1);
  }

  .vmsg {
    font-size: var(--fs-small);
  }

  .notice {
    display: flex;
    align-items: center;
    gap: var(--sp-1);
    max-width: var(--measure);
    margin: var(--sp-2) auto 0;
    color: var(--warning);
    font-size: var(--fs-small);
    font-weight: 500;
  }

  .review {
    outline: none;
  }

  .flag {
    max-width: var(--measure);
    margin: var(--sp-2) auto 0;
    color: var(--text-muted);
    font-size: var(--fs-small);
  }

  .solution {
    max-width: var(--measure);
    margin: var(--sp-4) auto 0;
  }

  .solution h3:first-child {
    margin-top: 0;
  }

  .actions {
    margin-top: auto;
    position: sticky;
    bottom: 0;
    z-index: 2;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: var(--sp-2);
    padding: var(--sp-2) 0;
    background: var(--background);
    box-shadow: 0 -12px 12px -4px var(--background);
  }

  .group {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--sp-1);
  }

  .error {
    color: var(--incorrect);
  }

  .break {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--sp-1);
    margin: var(--sp-1) 0 0;
    color: var(--text-muted);
    font-size: var(--fs-small);
  }

  .link {
    border: 0;
    background: none;
    color: var(--accent);
    font: inherit;
    text-decoration: underline;
  }

  .empty {
    display: grid;
    gap: var(--sp-2);
    max-width: 36rem;
    margin: var(--sp-6) auto 0;
  }

  .row {
    display: flex;
    flex-wrap: wrap;
    gap: var(--sp-1);
  }

  .worked,
  .flash {
    max-width: var(--measure);
    margin: var(--sp-4) auto 0;
    outline: none;
    font-family: var(--font-text);
  }

  .back {
    margin-top: var(--sp-2);
    padding-top: var(--sp-2);
    border-top: 1px solid var(--border);
    font-size: var(--fs-problem);
  }

  .find {
    display: grid;
    gap: var(--sp-1);
    max-width: var(--measure);
    margin: var(--sp-4) auto 0;
  }

  .find h3:first-child {
    margin-top: 0;
  }

  .reasons,
  .rubric {
    display: grid;
    gap: var(--sp-1);
  }

  .rubric {
    max-width: var(--measure);
    margin: var(--sp-2) auto 0;
  }

  .reason {
    display: flex;
    align-items: center;
    gap: var(--sp-2);
    min-height: 48px;
    padding: var(--sp-1) var(--sp-2);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--surface);
    color: var(--text);
    font-family: var(--font-text);
    text-align: start;
  }

  .reason span {
    flex: 1;
  }

  .reason:hover {
    border-color: var(--text-muted);
  }

  .reason.on {
    border-color: var(--accent);
    background: var(--selection);
  }

  .picks {
    display: flex;
    flex-wrap: wrap;
    gap: var(--sp-2);
    max-width: var(--measure);
    margin: var(--sp-2) auto 0;
    padding: 0;
    list-style: none;
  }

  .card.wide {
    margin-inline: calc(-1 * var(--sp-8));
  }

  .card.wide .solution {
    max-width: none;
  }

  .side-by-side {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--sp-3);
  }

  .side-by-side h3 {
    margin-top: 0;
  }

  @media (max-width: 960px) {
    .card.wide {
      margin-inline: 0;
    }

    .side-by-side {
      grid-template-columns: 1fr;
    }
  }

  .self-note {
    max-width: var(--measure);
    margin: var(--sp-3) auto 0;
    color: var(--text-muted);
  }

</style>
