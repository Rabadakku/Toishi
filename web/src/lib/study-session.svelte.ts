import { userMessage, type BridgeApi } from './bridge';
import { ActiveClock, idleThresholdMs, STILL_WORKING_GRACE_MS, WakeWatch } from './clock';
import type { ShortcutAction } from './shortcuts';
import type {
  AnswerPreview,
  AttemptResult,
  Confidence,
  Diagnosis,
  FlagKind,
  HintReveal,
  PartAnswer,
  PartVerdictView,
  PartView,
  ProblemView,
  Progress,
  SelfGrade,
  SolutionView,
  StartRequest,
  Summary,
  TimingReport,
  Turn,
  WentWrongChoice,
} from './types';

/**
 * answering   a problem (or a typed flashcard) is open for an answer
 * checking    a call is in flight
 * review      finished: verdict, solution, "What went wrong?" after a miss
 * self-grade  the student grades the answer against the solution
 * example     a worked example is shown; Space continues
 * front/back  a flashcard: Space shows the back, 1 to 4 rate it
 * summary     the session is over
 * empty       nothing to do (today's plan is done, vacation)
 */
export type Phase =
  | 'loading'
  | 'answering'
  | 'checking'
  | 'review'
  | 'self-grade'
  | 'example'
  | 'front'
  | 'back'
  | 'summary'
  | 'empty'
  | 'error';
export type EntryMode = 'math' | 'text';

/** One answer box: what is entered and what the bridge said about it. */
export interface PartState {
  mode: EntryMode;
  latex: string;
  text: string;
  /** Choice parts: the picked option ids ("1", "2" ... or "true" / "false"). */
  choices: string[];
  preview: AnswerPreview | null;
  verdict: PartVerdictView | null;
}

/** An option the page shows for a choice or true/false part. */
export interface ChoiceItem {
  id: string;
  text: string;
}

const PREVIEW_DEBOUNCE_MS = 160;
const INPUT_THROTTLE_MS = 1_000;
const TICK_MS = 15_000;
const DRAFT_VERSION = 1;

/** The fixed options of the "What went wrong?" picker, keyed 1 to 5 (steps are tapped). */
export const PICKER_OPTIONS: readonly { n: number; choice: WentWrongChoice; label: string; hint: string }[] = [
  { n: 1, choice: 'setup', label: 'Step 0: set up', hint: "Didn't know where to start or which method" },
  { n: 2, choice: 'slip', label: 'Careless slip', hint: 'My steps matched' },
  { n: 3, choice: 'misread', label: 'Misread the question', hint: '' },
  { n: 4, choice: 'other-method', label: 'A different valid method', hint: 'I solved it another way' },
  { n: 5, choice: 'cant-tell', label: "Can't tell", hint: '' },
];

export const SELF_GRADES: readonly { n: number; grade: SelfGrade; label: string }[] = [
  { n: 1, grade: 'matched', label: 'Matched the solution' },
  { n: 2, grade: 'minor-slip', label: 'Minor slip' },
  { n: 3, grade: 'missed', label: "Didn't get it" },
];

export const RATINGS: readonly { n: 1 | 2 | 3 | 4; label: string }[] = [
  { n: 1, label: 'Again' },
  { n: 2, label: 'Hard' },
  { n: 3, label: 'Good' },
  { n: 4, label: 'Easy' },
];

/** The id of a part in the page: its label, or 'main' for a single box. */
export function partId(part: PartView): string {
  return part.label ?? 'main';
}

export function isChoicePart(part: PartView): boolean {
  return part.answer_type === 'choice' || part.answer_type === 'truefalse';
}

export function choiceItems(part: PartView): ChoiceItem[] {
  if (part.answer_type === 'truefalse') {
    return [
      { id: 'true', text: 'True' },
      { id: 'false', text: 'False' },
    ];
  }
  return part.choices.map((c) => ({ id: String(c.index + 1), text: c.text_md }));
}

/** Answer boxes the student types into (self-graded parts have none). */
export function answerParts(problem: ProblemView): PartView[] {
  return problem.card.parts.filter((p) => p.answer_type !== 'self');
}

/** A flashcard that asks for a typed answer (graded automatically) instead of a rating. */
export function isTypedFlashcard(problem: ProblemView): boolean {
  return problem.kind === 'flashcard' && problem.card.type_answer && answerParts(problem).length > 0;
}

/** A find-the-error card with its shown work: pick the step, the reason, then type the fix. */
export function isFindError(problem: ProblemView | null): boolean {
  return !!problem && problem.card.kind === 'find-error' && problem.card.shown_work.length > 0;
}

function emptyPart(): PartState {
  return { mode: 'math', latex: '', text: '', choices: [], preview: null, verdict: null };
}

interface Draft {
  v: number;
  parts: Record<string, { mode: EntryMode; latex: string; text: string; choices: string[] }>;
}

/**
 * All the state and actions of the study screen, so the Svelte files only draw it.
 * Talks to the bridge (real or mock) and keeps the active-time clock (TIME-1 to TIME-6).
 */
export class StudySession {
  phase: Phase = $state('loading');
  errorMessage = $state('');
  turn: Turn | null = $state.raw(null);
  problem: ProblemView | null = $derived(this.turn?.type === 'problem' ? this.turn.problem : null);
  progress: Progress | null = $derived(this.turn?.type === 'problem' ? this.turn.progress : null);
  summary: Summary | null = $derived(this.turn?.type === 'summary' ? this.turn.summary : null);
  lighter = $derived(this.turn?.lighter ?? false);

  parts: Record<string, PartState> = $state({});
  hints: HintReveal[] = $state([]);
  result: AttemptResult | null = $state.raw(null);
  diagnosis: Diagnosis | null = $state(null);
  /** The picker choice made: an option, or a tapped step number. */
  picked: { choice: WentWrongChoice; step: number | null } | null = $state(null);
  flagMessage: string | null = $state(null);
  /** Find-the-error picks: the step (given when highlighted) and the reason's index. */
  findStep: number | null = $state(null);
  findReason: number | null = $state(null);
  /** Self-graded with a rubric: which steps the student's work matched. */
  ticks: boolean[] = $state([]);
  /** An inline note ("Type an answer first", "Undone. The problem is back."). */
  notice: string | null = $state(null);
  breakDue = $state(false);
  /** Counts changes that should move the keyboard focus (a new item, a retry ...). */
  focusToken = $state(0);
  activePartId: string | null = $state(null);

  paused = $state(false);
  pauseKind: 'manual' | 'idle' = $state('manual');
  stillWorking = $state(false);
  reasonOpen = $state(false);
  readonly clock = new ActiveClock();

  /** Set by the screen: copies what is in the answer boxes into the session before grading. */
  syncFields: (() => void) | null = null;

  private readonly api: BridgeApi;
  private firstKeyAtMs: number | null = null;
  private attemptStartMs = 0;
  /** The attempt began before a reload: its solve time is unknown. */
  private resumedAttempt = false;
  private afterWake = false;
  private previewTimers = new Map<string, number>();
  private previewSeq = new Map<string, number>();
  private idleTimer: number | undefined;
  private graceTimer: number | undefined;
  private tickTimer: number | undefined;
  private stillWorkingMark = 0;
  private lastInputAt = 0;
  private readonly wake = new WakeWatch(() => {
    this.afterWake = true;
  });

  constructor(api: BridgeApi) {
    this.api = api;
  }

  // --- derived views --------------------------------------------------------

  get answerParts(): PartView[] {
    return this.problem ? answerParts(this.problem) : [];
  }

  /** Parts still open for an answer (a settled part, right or out of tries, stays as it is). */
  get openParts(): PartView[] {
    return this.answerParts.filter((p) => !this.isSettled(partId(p)));
  }

  /** Right, or (multi-part, where each box has its own tries) out of tries. */
  isSettled(id: string): boolean {
    const verdict = this.parts[id]?.verdict;
    if (!verdict) return false;
    const multi = this.answerParts.length > 1;
    return verdict.status === 'correct' || (multi && verdict.status === 'incorrect' && verdict.final);
  }

  /** Find-the-error: both picks made (the step is given in the highlighted version). */
  get findReady(): boolean {
    return this.findStep !== null && this.findReason !== null;
  }

  get solution(): SolutionView | null {
    return this.result?.solution ?? null;
  }

  get isRetry(): boolean {
    return this.phase === 'answering' && this.result?.outcome === 'retry';
  }

  get mustDiagnose(): boolean {
    return this.phase === 'review' && !!this.solution?.needs_diagnosis && this.picked === null;
  }

  get itemKey(): string | null {
    return this.problem?.item_key ?? null;
  }

  private get timed(): boolean {
    return this.phase === 'answering' || this.phase === 'front' || this.phase === 'back' || this.phase === 'example';
  }

  // --- lifecycle -------------------------------------------------------------

  /** Resume today's open session (QUE-16) or start one; an explicit mode always starts. */
  async begin(request: StartRequest | null): Promise<void> {
    this.phase = 'loading';
    try {
      const resumed = request === null ? await this.api.study_resume() : null;
      this.applyTurn(resumed ?? (await this.api.study_start(request ?? { mode: 'daily' })));
    } catch (error) {
      this.fail(error);
    }
  }

  async startMore(mode: 'extra' | 'daily'): Promise<void> {
    await this.begin({ mode });
  }

  /** Listen for the window losing focus (TIME-2), input (TIME-3) and the Edit menu. */
  attach(): () => void {
    const onBlur = (): void => this.pauseFor('focus');
    const onFocus = (): void => this.clock.resume('focus');
    const onVisibility = (): void => {
      if (document.hidden) this.pauseFor('focus');
      else this.clock.resume('focus');
    };
    const onInput = (): void => this.noteInput();
    const onMenu = (event: Event): void => {
      if ((event as CustomEvent<string>).detail === 'undo-answer') void this.undo();
    };
    window.addEventListener('blur', onBlur);
    window.addEventListener('focus', onFocus);
    document.addEventListener('visibilitychange', onVisibility);
    window.addEventListener('keydown', onInput, true);
    window.addEventListener('pointerdown', onInput, true);
    window.addEventListener('pointermove', onInput, true);
    window.addEventListener('toishi:menu', onMenu);
    this.wake.start();
    this.tickTimer = window.setInterval(() => void this.saveProgress(), TICK_MS);
    return () => {
      window.removeEventListener('blur', onBlur);
      window.removeEventListener('focus', onFocus);
      document.removeEventListener('visibilitychange', onVisibility);
      window.removeEventListener('keydown', onInput, true);
      window.removeEventListener('pointerdown', onInput, true);
      window.removeEventListener('pointermove', onInput, true);
      window.removeEventListener('toishi:menu', onMenu);
      window.clearInterval(this.tickTimer);
      this.wake.stop();
      void this.saveProgress();
      this.clearTimers();
    };
  }

  private pauseFor(reason: 'focus'): void {
    const running = !this.clock.isPaused();
    this.clock.pause(reason);
    if (running) void this.saveProgress();
  }

  /** Mark a call in flight; returns the phase to go back to if it is refused. */
  private busy(): Phase {
    const before = this.phase;
    this.phase = 'checking';
    return before;
  }

  /** A refused call shows its message; anything else is an error screen. */
  private fail(error: unknown, before: Phase | null = null): void {
    const message = userMessage(error);
    if (message !== null) {
      this.notice = message;
      if (this.phase === 'checking') this.phase = before ?? (this.result?.solution ? 'review' : 'answering');
      if (this.phase === 'loading') {
        this.errorMessage = message;
        this.phase = 'error';
      }
      return;
    }
    this.errorMessage = error instanceof Error ? error.message : String(error);
    this.phase = 'error';
  }

  private clearTimers(): void {
    window.clearTimeout(this.idleTimer);
    window.clearTimeout(this.graceTimer);
    for (const timer of this.previewTimers.values()) window.clearTimeout(timer);
    this.previewTimers.clear();
  }

  private applyTurn(turn: Turn): void {
    const keep = turn.type === 'problem' && turn.problem?.item_key === this.itemKey && this.phase === 'answering';
    this.turn = turn;
    this.notice = turn.message || null;
    if (turn.break_due) this.breakDue = true;
    if (keep) return; // same item, still answering (a Lighter set switch): keep what is typed
    this.clearTimers();
    this.result = null;
    this.hints = [];
    this.diagnosis = null;
    this.picked = null;
    this.flagMessage = null;
    this.findStep = null;
    this.findReason = null;
    this.ticks = [];
    this.paused = false;
    this.stillWorking = false;
    this.reasonOpen = false;
    this.activePartId = null;
    this.afterWake = false;
    if (turn.type !== 'problem' || !turn.problem) {
      this.parts = {};
      this.clock.stop();
      this.phase = turn.type === 'summary' ? 'summary' : 'empty';
      return;
    }
    const problem = turn.problem;
    this.findStep = problem.card.error_step;
    const parts: Record<string, PartState> = {};
    for (const part of answerParts(problem)) parts[partId(part)] = emptyPart();
    this.restoreDraft(parts, problem.draft);
    this.parts = parts;
    this.hints = problem.hints_shown.map((text, i) => ({
      item_key: problem.item_key,
      index: i + 1,
      total: problem.card.hint_count,
      text,
      rating_effect: i + 1 === problem.card.hint_count ? 'again' : 'hard',
    }));
    this.clock.reset(problem.active_ms);
    this.resumedAttempt = problem.active_ms > 0;
    this.beginAttempt();
    if (turn.result) {
      this.clock.stop();
      this.applyResult(turn.result);
    } else if (problem.kind === 'example') {
      this.phase = 'example';
    } else if (problem.kind === 'flashcard' && !isTypedFlashcard(problem)) {
      this.phase = 'front';
    } else {
      this.phase = 'answering';
      this.scheduleIdle();
    }
    this.focusToken += 1;
  }

  private beginAttempt(): void {
    this.firstKeyAtMs = null;
    this.attemptStartMs = this.clock.elapsedMs();
  }

  // --- drafts (QUE-16) -------------------------------------------------------

  private draft(): string | null {
    if (this.phase !== 'answering') return null;
    this.syncFields?.();
    const parts: Draft['parts'] = {};
    let any = false;
    for (const [id, p] of Object.entries(this.parts)) {
      parts[id] = { mode: p.mode, latex: p.latex, text: p.text, choices: [...p.choices] };
      any ||= p.latex !== '' || p.text !== '' || p.choices.length > 0;
    }
    return any ? JSON.stringify({ v: DRAFT_VERSION, parts } satisfies Draft) : null;
  }

  private restoreDraft(parts: Record<string, PartState>, raw: string | null): void {
    if (!raw) return;
    try {
      const draft = JSON.parse(raw) as Draft;
      if (draft.v !== DRAFT_VERSION) return;
      for (const [id, saved] of Object.entries(draft.parts)) {
        const state = parts[id];
        if (!state) continue;
        state.mode = saved.mode === 'text' ? 'text' : 'math';
        state.latex = String(saved.latex ?? '');
        state.text = String(saved.text ?? '');
        state.choices = Array.isArray(saved.choices) ? saved.choices.map(String) : [];
      }
    } catch {
      // A draft saved with a submitted answer is plain text: put it in a single box.
      const ids = Object.keys(parts);
      const only = ids.length === 1 ? parts[ids[0]!] : undefined;
      if (only && !raw.includes(' | ')) {
        only.mode = 'text';
        only.text = raw;
      }
    }
  }

  /** Save the active time and the draft (every 15 s, on pause, on leaving). */
  async saveProgress(): Promise<void> {
    const key = this.itemKey;
    if (!key || !this.timed) return;
    try {
      const tick = await this.api.study_tick({
        item_key: key,
        active_ms: Math.round(this.clock.elapsedMs()),
        draft: this.draft(),
      });
      if (tick.break_due) this.breakDue = true;
    } catch {
      // Saving is best effort; the next tick or the answer itself carries the time.
    }
  }

  // --- answer entry ----------------------------------------------------------

  setValue(id: string, mode: EntryMode, value: string): void {
    const state = this.parts[id];
    if (!state) return;
    if (mode === 'math') state.latex = value;
    else state.text = value;
    this.noteKeystroke();
    this.schedulePreview(id);
  }

  setMode(id: string, mode: EntryMode): void {
    const state = this.parts[id];
    if (!state || state.mode === mode) return;
    state.mode = mode;
    state.preview = null;
    this.schedulePreview(id);
  }

  /** The ` key: flip the box the student is working in between math and plain text. */
  toggleMode(): boolean {
    const parts = this.openParts.filter((p) => !isChoicePart(p));
    const id = this.activePartId ?? (parts[0] ? partId(parts[0]) : undefined);
    const part = this.answerParts.find((p) => partId(p) === id);
    if (!id || !part || isChoicePart(part) || !this.parts[id]) return false;
    this.setMode(id, this.parts[id].mode === 'math' ? 'text' : 'math');
    this.focusToken += 1;
    return true;
  }

  toggleChoice(id: string, choiceId: string, multiple: boolean): void {
    const state = this.parts[id];
    if (!state) return;
    const has = state.choices.includes(choiceId);
    state.choices = multiple
      ? has
        ? state.choices.filter((c) => c !== choiceId)
        : [...state.choices, choiceId]
      : [choiceId];
    this.notice = null;
    this.noteKeystroke();
  }

  pickStep(step: number): void {
    if (this.problem?.card.error_step != null) return; // given in the highlighted version
    this.findStep = step;
    this.notice = null;
    this.noteKeystroke();
  }

  pickReason(index: number): void {
    this.findReason = index;
    this.notice = null;
    this.noteKeystroke();
    this.focusToken += 1;
  }

  toggleTick(index: number): void {
    if (index < 0 || index >= this.ticks.length) return;
    this.ticks[index] = !this.ticks[index];
  }

  private noteKeystroke(): void {
    if (this.firstKeyAtMs === null) this.firstKeyAtMs = this.clock.elapsedMs();
    this.notice = null;
  }

  private answerFor(part: PartView): PartAnswer {
    const state = this.parts[partId(part)];
    if (!state) return { part: part.label, value: '', source: 'text' };
    if (isChoicePart(part)) return { part: part.label, value: state.choices.join(', '), source: 'text' };
    return state.mode === 'math'
      ? { part: part.label, value: state.latex, source: 'mathlive' }
      : { part: part.label, value: state.text, source: 'text' };
  }

  private schedulePreview(id: string): void {
    const problem = this.problem;
    const part = this.answerParts.find((p) => partId(p) === id);
    if (!problem || !part || isChoicePart(part)) return;
    window.clearTimeout(this.previewTimers.get(id));
    const seq = (this.previewSeq.get(id) ?? 0) + 1;
    this.previewSeq.set(id, seq);
    const answer = this.answerFor(part);
    if (answer.value.trim() === '') {
      const state = this.parts[id];
      if (state) state.preview = null;
      return;
    }
    this.previewTimers.set(
      id,
      window.setTimeout(async () => {
        try {
          const preview = await this.api.study_read_answer({ item_key: problem.item_key, ...answer });
          const state = this.parts[id];
          if (state && this.previewSeq.get(id) === seq) state.preview = preview;
        } catch {
          // The preview is a convenience; submitting still reports any problem.
        }
      }, PREVIEW_DEBOUNCE_MS),
    );
  }

  // --- actions ---------------------------------------------------------------

  private timing(): TimingReport {
    const now = this.clock.elapsedMs();
    const firstKey = this.firstKeyAtMs ?? now;
    return {
      active_ms: Math.round(now),
      solve_ms: this.resumedAttempt ? null : Math.max(0, Math.round(firstKey - this.attemptStartMs)),
      entry_ms: Math.max(0, Math.round(now - firstKey)),
      paused_ms: Math.round(this.clock.pausedMs),
      pause_count: this.clock.pauseCount,
      longest_pause_ms: Math.round(this.clock.longestPauseMs),
      after_wake: this.afterWake,
      idle_trimmed: this.clock.idleTrimmed,
    };
  }

  async submit(confidence: Confidence): Promise<boolean> {
    const problem = this.problem;
    if (!problem || this.phase !== 'answering' || this.paused) return false;
    this.syncFields?.();
    const parts = this.answerParts;
    if (parts.length === 0) return false; // self-graded: the grade buttons submit
    const answers = parts.map((part) => this.answerFor(part));
    const findError = isFindError(problem);
    if (findError && !this.findReady) {
      this.notice = 'Pick the step that is wrong and the reason first.';
      return true;
    }
    const empty = parts.find((part, i) => !this.isSettled(partId(part)) && answers[i]?.value.trim() === '');
    if (empty) {
      this.notice = isChoicePart(empty) ? 'Choose an option first.' : 'Type an answer first.';
      return true;
    }
    const timing = this.timing();
    const before = this.busy();
    try {
      if (problem.kind === 'flashcard') {
        const first = answers[0];
        const result = await this.api.study_rate_flashcard({
          item_key: problem.item_key,
          answer: first?.value ?? '',
          source: first?.source ?? 'text',
          timing,
        });
        this.result = result;
        this.clock.stop();
        this.phase = 'back';
      } else {
        this.applyResult(
          await this.api.study_submit({
            item_key: problem.item_key,
            answers,
            confidence,
            timing,
            ...(findError ? { error_step: this.findStep, reason: this.findReason } : {}),
          }),
        );
      }
    } catch (error) {
      if (problem.kind === 'flashcard' && userMessage(error) !== null) {
        this.phase = 'back'; // the checker couldn't decide: the student rates it
        this.notice = userMessage(error);
        return true;
      }
      this.fail(error, before);
    }
    return true;
  }

  /** Self-graded problems: Show solution (nothing is graded yet). */
  async showSolution(): Promise<boolean> {
    const problem = this.problem;
    if (!problem || this.phase !== 'answering' || this.answerParts.length > 0 || this.paused) return false;
    const before = this.busy();
    try {
      this.applyResult(await this.api.study_show_solution({ item_key: problem.item_key }));
    } catch (error) {
      this.fail(error, before);
    }
    return true;
  }

  /** Grade against the solution: Matched / Minor slip / Didn't get it, or the rubric's ticks. */
  async selfGrade(grade: SelfGrade | 'rubric'): Promise<boolean> {
    const problem = this.problem;
    if (!problem || this.phase !== 'self-grade' || this.paused) return false;
    const timing = this.timing();
    const before = this.busy();
    const how =
      grade === 'rubric' ? { rubric_ticked: this.ticks.filter(Boolean).length } : { self_grade: grade };
    try {
      this.applyResult(
        await this.api.study_submit({ item_key: problem.item_key, answers: [], confidence: 'sure', timing, ...how }),
      );
    } catch (error) {
      this.fail(error, before);
    }
    return true;
  }

  async giveUp(): Promise<boolean> {
    const problem = this.problem;
    if (!problem || this.phase !== 'answering' || this.paused || problem.kind !== 'problem') return false;
    const timing = this.timing();
    const before = this.busy();
    try {
      this.applyResult(await this.api.study_give_up({ item_key: problem.item_key, timing }));
    } catch (error) {
      this.fail(error, before);
    }
    return true;
  }

  private applyResult(result: AttemptResult): void {
    this.result = result;
    if (result.break_due) this.breakDue = true;
    for (const verdict of result.verdicts) {
      const state = this.parts[verdict.part ?? 'main'];
      if (state) state.verdict = verdict;
    }
    if (result.outcome === 'invalid') {
      this.phase = 'answering';
      this.notice = result.message || null;
      this.focusToken += 1;
      return;
    }
    if (result.outcome === 'retry') {
      this.phase = 'answering';
      this.resumedAttempt = false;
      this.beginAttempt();
      this.focusToken += 1;
      this.scheduleIdle();
      return;
    }
    this.clock.stop();
    this.clearTimers();
    this.stillWorking = false;
    if (result.outcome === 'self-grade') {
      this.ticks = (result.solution?.rubric ?? []).map(() => false);
      this.phase = 'self-grade';
    } else if (result.outcome === 'recorded') {
      this.phase = this.problem?.kind === 'flashcard' ? 'back' : 'review';
      if (this.problem?.practice_test) void this.next();
    } else {
      this.phase = 'review';
    }
    this.focusToken += 1;
  }

  async hint(): Promise<boolean> {
    const problem = this.problem;
    if (!problem || this.phase !== 'answering' || this.paused) return false;
    if (this.hints.length >= problem.card.hint_count || problem.practice_test) return false;
    try {
      this.hints.push(await this.api.study_hint({ item_key: problem.item_key }));
    } catch (error) {
      this.fail(error);
    }
    return true;
  }

  async diagnose(choice: WentWrongChoice, step: number | null = null): Promise<boolean> {
    const problem = this.problem;
    if (!problem || !this.mustDiagnose) return false;
    this.picked = { choice, step };
    try {
      this.diagnosis = await this.api.study_diagnose({ item_key: problem.item_key, choice, step });
    } catch (error) {
      this.picked = null;
      this.fail(error);
    }
    return true;
  }

  async flag(kind: FlagKind): Promise<boolean> {
    const problem = this.problem;
    if (!problem || this.phase !== 'review') return false;
    if (kind === 'too_easy' && !this.solution?.can_mark_too_easy) return false;
    if (kind === 'dispute' && this.result?.outcome !== 'incorrect') return false;
    try {
      this.flagMessage = (await this.api.study_flag({ item_key: problem.item_key, kind })).message;
    } catch (error) {
      this.fail(error);
    }
    return true;
  }

  /** U or Edit > Undo Last Answer: until the next answer is submitted (QUE-15). */
  async undo(): Promise<boolean> {
    if (this.phase === 'loading' || this.phase === 'checking' || this.phase === 'summary' || this.paused) return false;
    const before = this.busy();
    try {
      this.applyTurn(await this.api.study_undo());
    } catch (error) {
      this.fail(error, before);
    }
    return true;
  }

  /** Space: on to the next item, once the picker (if any) has been answered. */
  async next(): Promise<boolean> {
    const key = this.itemKey;
    const ok = this.phase === 'review' || this.phase === 'example' || this.phase === 'back' || this.phase === 'self-grade';
    if (!key || !ok || this.mustDiagnose || this.paused) return false;
    if (this.phase === 'self-grade') return false;
    if (this.phase === 'back' && !this.result) return false; // rate it first
    const before = this.busy();
    try {
      this.applyTurn(await this.api.study_next({ item_key: key }));
    } catch (error) {
      this.fail(error, before);
    }
    return true;
  }

  /** Space on a flashcard's front. */
  showBack(): boolean {
    if (this.phase !== 'front' || this.paused) return false;
    this.phase = 'back';
    this.focusToken += 1;
    return true;
  }

  async rate(rating: 1 | 2 | 3 | 4): Promise<boolean> {
    const problem = this.problem;
    if (!problem || this.phase !== 'back' || this.result || this.paused) return false;
    const timing = this.timing();
    const before = this.busy();
    try {
      this.result = await this.api.study_rate_flashcard({ item_key: problem.item_key, rating, timing });
      this.applyTurn(await this.api.study_next({ item_key: problem.item_key }));
    } catch (error) {
      this.fail(error, before);
    }
    return true;
  }

  async end(): Promise<void> {
    if (this.phase === 'summary' || this.phase === 'loading' || this.phase === 'checking') return;
    await this.saveProgress();
    try {
      const summary = await this.api.study_end();
      this.applyTurn({
        type: 'summary',
        session_id: this.turn?.session_id ?? null,
        problem: null,
        progress: null,
        result: null,
        summary,
        message: '',
        break_due: false,
        lighter: false,
        mode: summary.mode,
      });
    } catch (error) {
      this.fail(error);
    }
  }

  async setLighter(on: boolean): Promise<void> {
    try {
      this.applyTurn(await this.api.study_set_lighter({ on }));
    } catch (error) {
      this.fail(error);
    }
  }

  // --- pause and idle --------------------------------------------------------

  togglePause(): boolean {
    if (!this.timed && !this.paused) return false;
    if (this.paused) {
      this.clock.resume(this.pauseKind === 'idle' ? 'idle' : 'manual');
      this.paused = false;
      this.focusToken += 1;
      this.scheduleIdle();
    } else {
      this.clock.pause('manual');
      this.pauseKind = 'manual';
      this.paused = true;
      this.stillWorking = false;
      this.reasonOpen = false;
      window.clearTimeout(this.idleTimer);
      window.clearTimeout(this.graceTimer);
      void this.saveProgress();
    }
    return true;
  }

  private noteInput(): void {
    const now = performance.now();
    if (this.stillWorking) {
      // Any input answers the note.
      this.stillWorking = false;
      window.clearTimeout(this.graceTimer);
    } else if (now - this.lastInputAt < INPUT_THROTTLE_MS) {
      return;
    }
    this.lastInputAt = now;
    this.scheduleIdle();
  }

  private scheduleIdle(): void {
    window.clearTimeout(this.idleTimer);
    if (this.phase !== 'answering' || this.paused || !this.problem) return;
    this.idleTimer = window.setTimeout(() => this.showStillWorking(), idleThresholdMs(this.problem.target_ms));
  }

  private showStillWorking(): void {
    if (this.phase !== 'answering' || this.paused) return;
    this.stillWorking = true;
    this.stillWorkingMark = this.clock.elapsedMs();
    window.clearTimeout(this.graceTimer);
    this.graceTimer = window.setTimeout(() => this.timeOutStillWorking(), STILL_WORKING_GRACE_MS);
  }

  private timeOutStillWorking(): void {
    if (!this.stillWorking) return;
    this.stillWorking = false;
    this.clock.trimBackTo(this.stillWorkingMark);
    this.pauseKind = 'idle';
    this.paused = true;
    void this.saveProgress();
  }

  confirmStillWorking(): void {
    this.stillWorking = false;
    window.clearTimeout(this.graceTimer);
    this.scheduleIdle();
  }

  // --- keyboard --------------------------------------------------------------

  /** Run a shortcut. Returns true when it did something (the caller then swallows the key). */
  perform(action: ShortcutAction): boolean {
    if (this.phase === 'loading' || this.phase === 'error' || this.phase === 'checking') return false;
    if (action.type === 'pause') {
      if (this.reasonOpen) {
        this.reasonOpen = false;
        return true;
      }
      return this.togglePause();
    }
    if (this.paused) return false;
    const answering = this.phase === 'answering';
    const reviewing = this.phase === 'review';
    switch (action.type) {
      case 'submit':
        if (this.phase === 'self-grade' && this.ticks.length > 0) {
          void this.selfGrade('rubric');
          return true;
        }
        if (!answering) return false;
        if (this.answerParts.length === 0) void this.showSolution();
        else void this.submit(action.unsure ? 'unsure' : 'sure');
        return true;
      case 'hint':
        if (!answering || (this.problem?.card.hint_count ?? 0) <= this.hints.length) return false;
        void this.hint();
        return true;
      case 'give_up':
        if (!answering || this.problem?.kind !== 'problem') return false;
        void this.giveUp();
        return true;
      case 'continue':
        if (this.phase === 'front') return this.showBack();
        if (answering && this.answerParts.length === 0) {
          void this.showSolution();
          return true;
        }
        if (this.mustDiagnose) return false;
        void this.next();
        return reviewing || this.phase === 'example' || this.phase === 'back';
      case 'too_easy':
        if (!reviewing || !this.solution?.can_mark_too_easy) return false;
        void this.flag('too_easy');
        return true;
      case 'dispute':
        if (!reviewing || this.result?.outcome !== 'incorrect') return false;
        void this.flag('dispute');
        return true;
      case 'report':
        if (!reviewing) return false;
        void this.flag('report');
        return true;
      case 'undo':
        if (this.phase === 'empty') return false;
        void this.undo();
        return true;
      case 'toggle_mode':
        return answering && this.toggleMode();
      case 'pick':
        return this.pick(action.n);
      case 'focus_mode':
        return false; // the screen handles this one
    }
  }

  /** Digits choose in whichever list is active. */
  private pick(n: number): boolean {
    if (this.phase === 'review') {
      const option = PICKER_OPTIONS.find((o) => o.n === n);
      if (!option || !this.mustDiagnose) return false;
      void this.diagnose(option.choice);
      return true;
    }
    if (this.phase === 'self-grade') {
      if (this.ticks.length > 0) {
        if (n > this.ticks.length) return false;
        this.toggleTick(n - 1);
        return true;
      }
      const option = SELF_GRADES.find((o) => o.n === n);
      if (!option) return false;
      void this.selfGrade(option.grade);
      return true;
    }
    if (this.phase === 'back' && !this.result) {
      const rating = RATINGS.find((r) => r.n === n);
      if (!rating) return false;
      void this.rate(rating.n);
      return true;
    }
    if (this.phase !== 'answering') return false;
    const problem = this.problem;
    if (problem && isFindError(problem) && !this.findReady) {
      if (this.findStep === null) {
        const step = problem.card.shown_work[n - 1];
        if (!step) return false;
        this.pickStep(step.number);
        return true;
      }
      if (n > problem.card.reasons.length) return false;
      this.pickReason(n - 1);
      return true;
    }
    const part = this.openParts.find(isChoicePart);
    const choice = part ? choiceItems(part)[n - 1] : undefined;
    if (!part || !choice) return false;
    this.toggleChoice(partId(part), choice.id, false);
    return true;
  }
}
