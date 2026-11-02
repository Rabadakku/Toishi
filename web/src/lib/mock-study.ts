import type { BridgeApi } from './bridge';
import { addDays, localDay } from './format';
import { textbookLine } from './plan-words';
import {
  ladderSession,
  sampleItems,
  sittingSession,
  type LadderPlan,
  type PartKey,
  type SampleItem,
  type SampleSession,
} from './sample-problems';
import {
  TEXT_SIZE_DEFAULT,
  type AnswerPreview,
  type AttemptResult,
  type Bin,
  type CourseSettings,
  type Exam,
  type ExamIn,
  type HoursBasis,
  type Library,
  type MilestoneView,
  type ModelView,
  type PartAnswer,
  type PartVerdictView,
  type Preferences,
  type ProfileState,
  type RefitReport,
  type Role,
  type SectionState,
  type SkillRow,
  type SolutionView,
  type Summary,
  type TodayView,
  type Turn,
} from './types';

/**
 * In-page stand-in for the Python bridge (page tests, `npm run dev`, a plain browser).
 * It grades by comparing normalised text (the real checker is SymPy-based and lives in
 * core/), but it follows the same contract as app/api.py: item keys, unlimited retries of
 * which only the first try counts, give-up, invalid answers that cost nothing, answers held
 * on the verdict screen until Continue, undo, and a small stuck ladder and sitting.
 *
 * Mock-only URL switches (with `?bridge=mock`, never reachable in the app):
 *   scenario=ladder   three power-rule slots that the stuck ladder rewrites after misses
 *   scenario=sitting  a warm-up problem, then a closed-book sitting of two skill blocks
 *   hours=history|standard|none  where Home's hours-to-keep-pace figure comes from
 *   prompt=...        replaces the first problem's Markdown (hostile-input tests)
 */

// --- reading answers -------------------------------------------------------

const FUNCTION_NAMES = /(sin|cos|tan|sec|csc|cot|ln|log)([a-z])/;

/** Lower-case, spaceless, multiplication-free spelling used to compare answers. */
export function canonical(source: PartAnswer['source'], value: string): string {
  let s = value;
  if (source === 'mathlive') {
    s = s
      .replace(/\\left|\\right|\\,|\\!|\\;|\\ /g, '')
      .replace(/\\cdot|\\times/g, '')
      .replace(/\\infty/g, 'inf')
      .replace(/\\cup/g, 'u')
      .replace(/\\(?:operatorname|text|mathrm)\{([^{}]*)\}/g, '$1')
      .replace(/\\d?frac\{([^{}]*)\}\{([^{}]*)\}/g, '($1)/($2)')
      .replace(/\\/g, '');
  }
  return s
    .toLowerCase()
    .replace(/[\s{}*]/g, '')
    .replace(/∞/g, 'inf')
    .replace(/∪/g, 'u');
}

function explicitMultiplication(source: PartAnswer['source'], value: string): string {
  let s = value.trim();
  if (source === 'text') {
    s = s
      .replace(/\binf\b/g, '\\infty')
      .replace(/\s+U\s+/g, ' \\cup ')
      .replace(/\*/g, ' \\cdot ');
  }
  return s
    .replace(/\^(\d+)([a-zA-Z])/g, '^{$1} \\cdot $2')
    .replace(/(\d)([a-zA-Z(])/g, '$1 \\cdot $2')
    .replace(/\)\s*\(/g, ') \\cdot (');
}

function bracketsBalance(value: string): boolean {
  let depth = 0;
  for (const ch of value) {
    if (ch === '(' || ch === '[') depth += 1;
    if (ch === ')' || ch === ']') depth -= 1;
    if (depth < 0) return false;
  }
  return depth === 0;
}

function preview(answerType: string, source: PartAnswer['source'], raw: string): AnswerPreview {
  const fail = (message: string): AnswerPreview => ({ ok: false, read_as_latex: null, message, hints: [] });
  const value = raw.trim();
  if (value === '') return fail('Type an answer.');
  if (answerType === 'choice') return { ok: true, read_as_latex: null, message: '', hints: [] };
  const flat = value.replace(/\s+/g, '').toLowerCase();
  if (!bracketsBalance(flat)) return fail('The brackets do not match.');
  const missing = FUNCTION_NAMES.exec(flat.replace(/\\/g, ''));
  if (source === 'text' && missing) return fail(`Did you mean ${missing[1]}(${missing[2]})?`);
  if (source === 'text' && /(^|[^a-z])[a-z]{2}($|[^a-z(])/.test(flat) && !/inf|pi|dne|none/.test(flat)) {
    return fail('Two letters never multiply. Write `x*y`.');
  }
  if (answerType === 'interval' && !/[([].*,.*[)\]]/.test(flat) && !/^(none|dne)$/.test(flat)) {
    return fail('Expected an interval, like `(-inf, 0) U (2, inf)`.');
  }
  if (answerType === 'point' && !/^\(.*,.*\)$/.test(flat)) return fail('Expected a point, like `(2, -4)`.');
  return { ok: true, read_as_latex: explicitMultiplication(source, value), message: '', hints: [] };
}

function grade(key: PartKey, answerType: string, answer: PartAnswer): { correct: boolean; feedback: string | null } {
  if (answerType === 'choice') {
    const chosen = answer.value.split(/[,\s]+/).filter(Boolean).sort().join(',');
    return { correct: chosen === [...key.accept].sort().join(','), feedback: null };
  }
  const given = canonical(answer.source, answer.value);
  const accepted = key.accept.map((a) => canonical('text', a));
  if (accepted.includes(given)) return { correct: true, feedback: null };
  if (key.tolerance !== undefined) {
    const x = Number(given);
    const target = Number(accepted[0]);
    if (Number.isFinite(x) && Math.abs(x - target) <= key.tolerance * Math.max(1, Math.abs(target))) {
      return { correct: true, feedback: null };
    }
  }
  const wrong = key.wrong?.find((w) => canonical('text', w.answer) === given);
  return { correct: false, feedback: wrong?.feedback ?? null };
}

/**
 * A wrong try is "Not quite" and nothing else: a retry result carries no matched wrong-answer
 * feedback and no wrong_step. Only a result with the solution (a give-up) has them.
 */
function withoutFeedback(verdict: PartVerdictView): PartVerdictView {
  return { ...verdict, feedback: null, wrong_step: null, message: verdict.status === 'invalid' ? verdict.message : '' };
}

// --- the session -----------------------------------------------------------

type Scenario = 'daily' | 'ladder' | 'sitting';

interface MockOptions {
  scenario: Scenario;
  prompt: string | null;
  hours: HoursBasis;
}

/** The mock-only URL switches; nothing but `?bridge=mock` turns them on. */
function mockOptions(): MockOptions {
  const params = new URLSearchParams(window.location.search);
  const mock = params.get('bridge') === 'mock';
  const scenario = params.get('scenario');
  const hours = params.get('hours');
  return {
    scenario: mock && (scenario === 'ladder' || scenario === 'sitting') ? scenario : 'daily',
    prompt: mock ? params.get('prompt') : null,
    hours: mock && (hours === 'history' || hours === 'none') ? hours : 'standard',
  };
}

function sessionFor(scenario: Scenario): SampleSession {
  if (scenario === 'ladder') return ladderSession();
  if (scenario === 'sitting') return sittingSession();
  return { items: sampleItems(), ladder: null };
}

interface Held {
  result: AttemptResult;
}

interface Logged {
  index: number;
  item: SampleItem;
  /** The first try was right (what counts); false after a miss or a give-up. */
  correct: boolean;
  /** The first try's verdict; null for items with none (examples). */
  first: boolean | null;
  rating: number | null;
  active_ms: number;
}

/** Problems allow any number of tries; this says "no limit" in attempts_allowed. */
const NO_LIMIT = 0;

/** One try only: which-method and find-the-error items (graded on the whole pick). */
function oneTry(item: SampleItem): boolean {
  return item.kind !== 'problem' || item.card.kind === 'method' || item.card.kind === 'find-error';
}

class MockSession {
  items: SampleItem[];
  readonly ladder: LadderPlan | null;
  index = 0;
  tries = 0;
  /** The first try's verdict, once there is one. */
  first: boolean | null = null;
  /** The last wrong try's verdicts (with their feedback): "Your answer" after a give-up. */
  lastVerdicts: PartVerdictView[] = [];
  held: Held | null = null;
  log: Logged[] = [];
  /** The last answer can be undone until the next one is submitted. */
  undoable = false;
  /** The plan before the last Continue (the ladder may have rewritten it), for undo. */
  undoPlan: { items: SampleItem[]; setAside: string[]; note: MockSession['note'] } | null = null;
  ended = false;
  activeMs = 0;
  draft: string | null = null;
  /** Skills set aside for today by the ladder. */
  setAside: string[] = [];
  /** A one-line note for the item at `index` (a skill set aside). */
  note: { index: number; text: string } | null = null;

  constructor(plan: SampleSession) {
    this.items = plan.items;
    this.ladder = plan.ladder;
  }

  get item(): SampleItem | undefined {
    return this.items[this.index];
  }

  key(index = this.index): string {
    const item = this.items[index];
    return item ? `${item.kind}:${item.card.id}` : 'end';
  }

  problems(): SampleItem[] {
    return this.items.filter((i) => i.kind === 'problem');
  }

  /** Active time already spent on the earlier problems of this item's sitting block. */
  blockElapsed(item: SampleItem): number {
    const sitting = item.sitting;
    if (!sitting) return 0;
    return this.log
      .filter((l) => l.item.sitting?.id === sitting.id && l.item.skill.id === item.skill.id)
      .reduce((sum, l) => sum + l.active_ms, 0);
  }

  turn(message = ''): Turn {
    const item = this.item;
    const base = { session_id: 1, break_due: false, lighter: false, mode: 'daily' };
    if (!item || this.ended) {
      return { ...base, message, type: 'summary', problem: null, progress: null, result: null, summary: this.summary() };
    }
    const done = this.log.filter((l) => l.item.kind === 'problem');
    const note = this.note?.index === this.index ? this.note.text : '';
    return {
      ...base,
      message: message || note,
      type: 'problem',
      problem: {
        item_key: this.key(),
        kind: item.kind,
        card: item.card,
        reason: item.reason,
        attempts_allowed: oneTry(item) ? 1 : NO_LIMIT,
        tries_used: this.tries,
        draft: this.draft,
        active_ms: this.activeMs,
        target_ms: null,
        untimed: false,
        practice_test: false,
        role: item.role,
        plan_reason: item.plan_reason,
        textbook: item.textbook,
        sitting: item.sitting ? { ...item.sitting, block_elapsed_ms: this.blockElapsed(item) } : null,
      },
      progress: {
        position: done.length + (item.kind === 'problem' && !this.held ? 1 : 0),
        total: this.problems().length,
        answered: done.length,
        correct: done.filter((l) => l.correct).length,
      },
      result: this.held?.result ?? null,
      summary: null,
    };
  }

  summary(): Summary {
    const problems = this.log.filter((l) => l.item.kind === 'problem');
    const correct = problems.filter((l) => l.correct).length;
    return {
      mode: 'daily',
      problems: problems.length,
      correct,
      missed: problems.length - correct,
      active_ms: this.log.reduce((sum, l) => sum + l.active_ms, 0),
      misses: problems
        .filter((l) => !l.correct)
        .map((l) => ({
          item_key: `problem:${l.item.card.id}`,
          card_id: l.item.card.id,
          skill_id: l.item.skill.id,
          skill_name: l.item.skill.name,
          tag: l.item.reason.tag,
          label: l.item.reason.label,
        })),
      learned: [],
      flashcards: this.log.filter((l) => l.item.kind === 'flashcard').length,
      forecast: { day: 'tomorrow', problems: 18, minutes: 50, courses: [] },
      extra_practice_available: true,
      practice_tests: [],
      test: null,
      ready_today: 0,
    };
  }

  solution(item: SampleItem, correct: boolean, unsure: boolean, activeMs: number): SolutionView {
    const target = item.target_ms;
    const clock = (ms: number): string => {
      const s = Math.round(ms / 1000);
      return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
    };
    return {
      skill_id: item.skill.id,
      skill_name: item.skill.name,
      answer_md: item.answer_md,
      solution_md: null,
      steps: item.steps,
      alternative_md: item.alternative_md ?? null,
      active_ms: activeMs,
      target_ms: target,
      time_text: clock(activeMs) + (target ? ` · target ${clock(target)}` : ''),
      // Like the app: only the graded answer's recorded effect, so never before grading.
      confident_error: false,
      can_mark_too_easy: correct && this.tries <= 1 && !unsure,
      textbook_ref: null,
      rubric: [],
      shown_work: item.card.shown_work,
    };
  }

  hold(
    item: SampleItem,
    correct: boolean,
    verdicts: PartVerdictView[],
    unsure: boolean,
    activeMs: number,
    firstTry: boolean,
    findError: AttemptResult['find_error'] = null,
  ): AttemptResult {
    const result: AttemptResult = {
      find_error: findError,
      item_key: this.key(),
      outcome: correct ? 'correct' : 'incorrect',
      verdicts,
      message: correct ? '' : 'Here is the full solution.',
      solution: this.solution(item, correct, unsure, activeMs),
      tries_used: this.tries,
      attempts_allowed: oneTry(item) ? 1 : NO_LIMIT,
      rating: null,
      break_due: false,
      can_retry: false,
      first_try_counted: firstTry,
    };
    this.held = { result };
    this.undoable = true;
    return result;
  }

  /** Continue: log the held answer, let the ladder re-plan, move on. */
  advance(): void {
    const item = this.item;
    this.undoPlan = { items: [...this.items], setAside: [...this.setAside], note: this.note };
    if (item && this.held) {
      const first = this.first ?? false;
      this.log.push({ index: this.index, item, correct: first, first, rating: null, active_ms: this.held.result.solution?.active_ms ?? 0 });
      this.climbLadder(item);
    } else if (item && item.kind === 'example') {
      this.log.push({ index: this.index, item, correct: true, first: null, rating: null, active_ms: 0 });
    }
    this.index += 1;
    this.reset();
  }

  reset(): void {
    this.tries = 0;
    this.first = null;
    this.lastVerdicts = [];
    this.held = null;
    this.activeMs = 0;
    this.draft = null;
  }

  /**
   * The stuck ladder (wave2-planner.md section 1), for the ladder session's skill: a first-try
   * miss swaps its next slot for a smaller problem, a second for a prerequisite, and a third
   * sets the skill aside for today with its textbook pointer. A ladder item replaces a slot,
   * never adds one.
   */
  private climbLadder(item: SampleItem): void {
    const ladder = this.ladder;
    if (!ladder || item.slot !== ladder.skill.id) return;
    let streak = 0;
    for (const entry of [...this.log].reverse()) {
      if (entry.item.slot !== ladder.skill.id || entry.first === null) continue;
      if (entry.first) break;
      streak += 1;
    }
    if (streak === 0) return;
    const later = (it: SampleItem, i: number): boolean => i > this.index && it.slot === ladder.skill.id;
    if (streak >= 3) {
      this.items = this.items.filter((it, i) => !later(it, i));
      this.setAside = [...this.setAside, ladder.skill.name];
      this.note = {
        index: this.index + 1,
        text: `${ladder.skill.name} is set aside for today. See ${textbookLine(ladder.textbook)}.`,
      };
      return;
    }
    const next = this.items.findIndex(later);
    if (next < 0) return;
    const rung = streak === 1 ? ladder.smaller : ladder.prerequisite;
    this.items[next] = { ...rung, card: { ...rung.card }, slot: ladder.skill.id };
  }
}

function userMessage(text: string): Error {
  const error = new Error(text);
  error.name = 'UserMessage';
  return error;
}

// --- courses, skills and the model ----------------------------------------------

interface MockSection {
  id: string;
  title: string;
  unit: string;
  course: string;
  /** Class hours; null in a pack without pace data. */
  hours: number | null;
}

const CALCULUS = 'Sample Calculus';
const STATISTICS = 'Sample Statistics';

const SECTIONS: MockSection[] = [
  { id: 'Sample Calculus::Derivatives::Power rule', title: 'Power rule', unit: 'Sample Calculus::Derivatives', course: CALCULUS, hours: 3 },
  { id: 'Sample Calculus::Derivatives::Chain rule', title: 'Chain rule', unit: 'Sample Calculus::Derivatives', course: CALCULUS, hours: 3 },
  { id: 'Sample Calculus::Applications::Shape of a graph', title: 'Shape of a graph', unit: 'Sample Calculus::Applications', course: CALCULUS, hours: 4 },
  { id: 'Sample Statistics::Describing data::Mean and median', title: 'Mean and median', unit: 'Sample Statistics::Describing data', course: STATISTICS, hours: null },
];

const COURSES = [CALCULUS, STATISTICS];

type StoredSettings = Omit<CourseSettings, 'course_title' | 'exams' | 'sections' | 'has_pace'>;

function initialSettings(today: string): Map<string, StoredSettings> {
  const base = {
    aligned: null,
    pace_factor: 1,
    accuracy_target: 0.9,
    target_tier: 4,
    keep_target: 0.8,
    keep_tier: 3,
    growth_band: 'standard' as const,
  };
  return new Map([
    [CALCULUS, { ...base, course_id: CALCULUS, start: addDays(today, -30), end: addDays(today, 60) }],
    [STATISTICS, { ...base, course_id: STATISTICS, start: null, end: null }],
  ]);
}

function milestones(intro: string | null, certified: number, targetTier = 4): MilestoneView[] {
  const due = (days: number): string | null => (intro ? addDays(intro, days) : null);
  return [
    { name: 'M1', tier: 2, deadline: due(5), certified: certified >= 1 },
    { name: 'M2', tier: 3, deadline: due(14), certified: certified >= 2 },
    { name: 'M3', tier: targetTier, deadline: due(28), certified: certified >= 3 },
    { name: 'keep', tier: 3, deadline: null, certified: false },
  ];
}

function sampleSkills(course: string, today: string, setAside: readonly string[]): SkillRow[] {
  const [power, chain, shape] = SECTIONS.map((s) => s.id);
  const row = (r: Omit<SkillRow, 'set_aside'>): SkillRow => ({ ...r, set_aside: setAside.includes(r.name) });
  if (course === STATISTICS) {
    return [
      row({
        skill_id: 'stat.center.mean-median',
        name: 'Mean and median',
        deck: SECTIONS[3]!.id,
        state: 'not-introduced',
        track: 'on-track',
        intro: null,
        milestones: milestones(null, 0),
        level: null,
        readiness: null,
        pace_ok: null,
      }),
    ];
  }
  const ago = (days: number): string => addDays(today, -days);
  return [
    row({ skill_id: 'calc1.deriv.power-rule', name: 'Power rule', deck: power!, state: 'maintenance', track: 'ahead', intro: ago(20), milestones: milestones(ago(20), 2), level: 3, readiness: 0.93, pace_ok: true }),
    row({ skill_id: 'calc1.deriv.sum-rule', name: 'Sum and difference rules', deck: power!, state: 'growth', track: 'on-track', intro: ago(6), milestones: milestones(ago(6), 1), level: 2, readiness: 0.84, pace_ok: true }),
    row({ skill_id: 'calc1.deriv.chain-rule', name: 'Chain rule', deck: chain!, state: 'growth', track: 'behind', intro: ago(16), milestones: milestones(ago(16), 1), level: 2, readiness: 0.71, pace_ok: false }),
    row({ skill_id: 'calc1.deriv.implicit', name: 'Implicit differentiation', deck: chain!, state: 'not-introduced', track: 'on-track', intro: addDays(today, 3), milestones: milestones(addDays(today, 3), 0), level: null, readiness: null, pace_ok: null }),
    row({ skill_id: 'calc1.shape.first-derivative-test', name: 'First derivative test', deck: shape!, state: 'new', track: 'on-track', intro: today, milestones: milestones(today, 0), level: null, readiness: 0.62, pace_ok: null }),
    row({ skill_id: 'calc1.shape.concavity', name: 'Concavity', deck: shape!, state: 'slip-limited', track: 'behind', intro: ago(10), milestones: milestones(ago(10), 0), level: 1, readiness: 0.81, pace_ok: true }),
  ];
}

/** The model's starting values (core.learner SharedParams, without the version). */
const PRIOR_PARAMS: Record<string, number | number[]> = {
  slip: 0.02,
  delta4: 0.3,
  delta5: 0.7,
  calib_a: [0, 0, 0, 0, 0],
  calib_b: 1,
  phi: 0.05,
  tau: 0.6931471805599453,
  sigma_t: 0.45,
  gamma: 0.37,
  rho: 0,
  alpha: 0.05,
  q_drift: 0.01,
  kappa: 0.95,
  same_day_weight: 0.25,
  prior_new_mean: 0.6190392084062235,
  prior_new_var: 2,
  prior_background_mean: 3.4760986898352733,
  prior_background_var: 1,
  fsrs_weights: [],
};

function bins(rows: [string, number, number, number][]): Bin[] {
  return rows.map(([label, n, predicted, observed]) => ({ label, n, predicted, observed }));
}

const CALIBRATION: ModelView['calibration'] = {
  by_tier: bins([
    ['Tier 1', 48, 0.92, 0.94],
    ['Tier 2', 96, 0.84, 0.82],
    ['Tier 3', 52, 0.71, 0.69],
    ['Tier 4', 16, 0.58, 0.5],
    ['Tier 5', 0, 0, 0],
  ]),
  by_gap: bins([
    ['First practice', 30, 0.64, 0.6],
    ['Under 1 day', 70, 0.86, 0.88],
    ['1 to 7 days', 72, 0.8, 0.78],
    ['8 to 30 days', 34, 0.74, 0.68],
    ['Over 30 days', 6, 0.7, 0.67],
  ]),
  by_components: bins([
    ['1 skill', 90, 0.86, 0.87],
    ['2 skills', 80, 0.78, 0.76],
    ['3 or more', 42, 0.66, 0.6],
  ]),
};

const DAY_MS = 86_400_000;

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

const mocks = new WeakSet<object>();

/** True for an api made by createMockApi (the page then says it shows sample problems). */
export function isMockApi(api: object): boolean {
  return mocks.has(api);
}

/** The whole bridge, in memory, with sample problems. */
export function createMockApi(): BridgeApi {
  const options = mockOptions();
  const today = localDay();
  let session: MockSession | null = null;
  let preferences: Preferences = { theme: 'auto', text_size: TEXT_SIZE_DEFAULT };
  const states = new Map<string, SectionState>(SECTIONS.map((s, i) => [s.id, i === 0 ? 'learning' : 'off']));
  const profile: ProfileState = { profile: { id: 'sample', name: 'Sample' }, error: null, warnings: [] };
  const settings = initialSettings(today);
  let exams: Exam[] = [
    {
      exam_id: 1,
      course_id: CALCULUS,
      name: 'Midterm',
      day: addDays(today, 9),
      scope_decks: [SECTIONS[0]!.id, SECTIONS[1]!.id],
      target: null,
      minutes: 50,
      problems: 10,
    },
  ];
  let nextExamId = 2;
  let model: ModelView = {
    version: 'prior',
    source: 'prior',
    created_at: Date.now() - 20 * DAY_MS,
    params: { ...PRIOR_PARAMS },
    last_refit: null,
    calibration: CALIBRATION,
    attempts: 212,
  };
  let versions = 0;

  function open(): MockSession {
    if (!session) {
      session = new MockSession(sessionFor(options.scenario));
      const first = session.items[0];
      if (options.prompt !== null && first) first.card = { ...first.card, prompt_md: options.prompt };
    }
    return session;
  }

  function current(itemKey?: string): { s: MockSession; item: SampleItem } {
    const s = session;
    const item = s?.item;
    if (!s || !item || s.ended) throw userMessage('No study session is open. Press Start.');
    if (itemKey !== undefined && itemKey !== s.key()) throw userMessage('That problem is no longer on screen.');
    return { s, item };
  }

  function merged<T extends string>(values: T[]): T | 'mixed' {
    const set = new Set(values);
    return set.size === 1 ? [...set][0]! : 'mixed';
  }

  function library(): Library {
    return {
      courses: COURSES.map((course) => {
        const units = [...new Set(SECTIONS.filter((s) => s.course === course).map((s) => s.unit))].map((unit) => {
          const sections = SECTIONS.filter((s) => s.unit === unit).map((s) => ({
            id: s.id,
            title: s.title,
            state: states.get(s.id) ?? 'off',
            skills: course === CALCULUS ? 2 : 1,
            textbook_ref: null,
            // A one-problem skill, as imported or user-made decks often have (ENG-2).
            small_pool_skills: s.title === 'Shape of a graph' ? ['Concavity'] : [],
          }));
          return { id: unit, title: unit.split('::')[1] ?? unit, state: merged(sections.map((s) => s.state)), sections };
        });
        return { id: course, title: course, state: merged(units.map((u) => u.state)) as SectionState | 'mixed', units };
      }),
    };
  }

  function courseSettings(courseId: string): CourseSettings {
    const stored = settings.get(courseId);
    if (!stored) throw userMessage('There is no course with that name.');
    const sections = SECTIONS.filter((s) => s.course === courseId);
    return {
      ...stored,
      course_title: courseId,
      exams: exams.filter((e) => e.course_id === courseId).sort((a, b) => a.day.localeCompare(b.day)),
      sections: sections.map((s) => ({ deck: s.id, title: s.title, hours: s.hours })),
      has_pace: sections.every((s) => s.hours !== null),
    };
  }

  function daysUntil(day: string): number {
    return Math.round((Date.parse(`${day}T12:00:00`) - Date.parse(`${today}T12:00:00`)) / DAY_MS);
  }

  function todayView(): TodayView {
    const s = session;
    const plan = s?.items ?? sessionFor(options.scenario).items;
    const problems = plan.filter((i) => i.kind === 'problem');
    const minutes = Math.max(1, Math.round(problems.reduce((sum, i) => sum + (i.target_ms ?? 0), 0) / 60_000));
    const byRole: Partial<Record<Role, number>> = {};
    for (const item of problems) if (item.role) byRole[item.role] = (byRole[item.role] ?? 0) + 1;
    const sittingSkills = [...new Set(problems.filter((i) => i.sitting).map((i) => i.skill.name))];
    const sittingId = problems.find((i) => i.sitting)?.sitting?.id;
    const hours = {
      history: { hours_to_keep_pace: 7.8, standard_hours: 6.5 },
      standard: { hours_to_keep_pace: 6.5, standard_hours: 6.5 },
      none: { hours_to_keep_pace: null, standard_hours: null },
    }[options.hours];
    return {
      day: today,
      problems: problems.length,
      minutes,
      flashcards: plan.filter((i) => i.kind === 'flashcard').length,
      courses: [{ course_id: CALCULUS, title: CALCULUS, problems: problems.length, minutes }],
      exams: exams.map((e) => {
        const days = daysUntil(e.day);
        return { exam_id: e.exam_id, name: e.name, course_id: e.course_id, days_left: days, practice_test: days <= 21 };
      }),
      session_open: !!s && !s.ended,
      done_today: !!s && s.ended,
      extra_practice_available: true,
      by_role: byRole,
      ...hours,
      hours_basis: options.hours,
      behind: ['Chain rule', 'Concavity'],
      set_aside: s?.setAside ?? [],
      sittings: sittingId ? [{ id: sittingId, skills: sittingSkills }] : [],
      notes: ['Concavity: careless errors are holding it back. Check your work before you submit.'],
    };
  }

  function checkExam(exam: ExamIn): void {
    if (!exam.name.trim()) throw userMessage('Give the exam a name.');
    if (!/^\d{4}-\d{2}-\d{2}$/.test(exam.day)) throw userMessage('Choose the day of the exam.');
    const decks = new Set(SECTIONS.filter((s) => s.course === exam.course_id).map((s) => s.id));
    if (exam.scope_decks.length === 0) throw userMessage('Choose at least one section the exam covers.');
    if (exam.scope_decks.some((d) => !decks.has(d))) throw userMessage('That section is not in this course.');
  }

  const api: BridgeApi = {
    ping: async (message) => `pong: ${message}`,
    version: async () => '0.0.0-mock',
    app_info: async () => ({ name: 'Toishi', version: '0.0.0-mock', python: 'mock', self_test: false }),
    report_self_test: async () => null,

    profile_get: async () => ({ ...profile }),
    profile_create: async () => ({ ...profile }),
    restore_list: async () => ({ profile: { id: 'sample', name: 'Sample' }, backups: [] }),
    restore_backup: async () => ({ ...profile }),
    restore_recheck: async () => ({ ...profile }),
    prefs_get: async () => ({ ...preferences }),
    prefs_set: async (next) => {
      preferences = { ...next };
      return null;
    },

    library_get: async () => library(),
    library_set_state: async ({ id, state }) => {
      for (const s of SECTIONS) if (s.id === id || s.unit === id || s.course === id) states.set(s.id, state);
      return library();
    },

    library_card_media: async () => ({ files: {} }),

    study_today: async () => todayView(),
    study_forecast: async () => ({ day: 'tomorrow', problems: 18, minutes: 50, courses: [] }),
    study_start: async () => {
      if (session?.ended) session = null;
      return open().turn();
    },
    study_resume: async () => (session && !session.ended ? session.turn() : null),
    study_current: async () => current().s.turn(),
    study_read_answer: async (request) => {
      const { item } = current(request.item_key);
      const part = item.card.parts.find((p) => p.label === request.part) ?? item.card.parts[0];
      return preview(part?.answer_type ?? 'expression', request.source, request.value);
    },
    study_submit: async (request) => {
      const { s, item } = current(request.item_key);
      if (s.held) throw userMessage('This problem is already answered; continue.');
      s.activeMs = request.timing.active_ms;
      const single = oneTry(item);
      const verdicts: PartVerdictView[] = item.card.parts.map((part) => {
        const label = part.label ?? 'main';
        const answer = request.answers.find((a) => (a.part ?? 'main') === label) ?? { part: part.label, value: '', source: 'text' as const };
        const read = preview(part.answer_type, answer.source, answer.value);
        if (!read.ok) {
          return { part: part.label, status: 'invalid', read_as: null, message: read.message, feedback: null, final: false, tries_used: s.tries };
        }
        const key = item.keys[label];
        const graded = key ? grade(key, part.answer_type, answer) : { correct: false, feedback: null };
        return {
          part: part.label,
          status: graded.correct ? 'correct' : 'incorrect',
          read_as: read.read_as_latex,
          message: graded.feedback ?? '',
          feedback: graded.feedback,
          final: graded.correct || single,
          tries_used: s.tries + 1,
        };
      });
      if (verdicts.some((v) => v.status === 'invalid')) {
        return {
          item_key: s.key(),
          outcome: 'invalid',
          verdicts,
          message: "Not counted: fix the answer's form and submit again.",
          solution: null,
          tries_used: s.tries,
          attempts_allowed: single ? 1 : NO_LIMIT,
          rating: null,
          break_due: false,
          find_error: null,
          can_retry: false,
          first_try_counted: false,
        };
      }
      const firstTry = s.tries === 0;
      s.tries += 1;
      if (item.card.kind === 'find-error' && item.card.shown_work.length > 0) {
        // One try: graded on the step, the reason and the corrected value together.
        const wrongStep = 2;
        const fe = {
          error_step: wrongStep,
          right_reason: item.right_reason ?? null,
          step_ok: request.error_step === wrongStep,
          reason_ok: request.reason === item.right_reason,
          value_ok: verdicts.every((v) => v.status === 'correct'),
        };
        const ok = fe.step_ok && fe.reason_ok && fe.value_ok;
        if (firstTry) s.first = ok;
        return s.hold(item, ok, verdicts, request.confidence === 'unsure', request.timing.active_ms, firstTry, fe);
      }
      const correct = verdicts.every((v) => v.status === 'correct');
      if (firstTry) s.first = correct;
      if (!correct && !single) {
        s.undoable = false;
        s.lastVerdicts = verdicts;
        return {
          item_key: s.key(),
          outcome: 'retry',
          verdicts: verdicts.map(withoutFeedback),
          message: 'Not quite.',
          solution: null,
          tries_used: s.tries,
          attempts_allowed: NO_LIMIT,
          rating: null,
          break_due: false,
          find_error: null,
          can_retry: true,
          first_try_counted: firstTry,
        };
      }
      return s.hold(item, correct, verdicts, request.confidence === 'unsure', request.timing.active_ms, firstTry);
    },
    study_give_up: async (request) => {
      const { s, item } = current(request.item_key);
      if (s.held) throw userMessage('This problem is already answered; continue.');
      const firstTry = s.tries === 0;
      if (firstTry) s.first = false; // a give-up before any answer is an aided first try: a miss
      s.tries += 1;
      return s.hold(item, false, s.lastVerdicts, true, request.timing.active_ms, firstTry);
    },
    study_tick: async (request) => {
      const { s } = current(request.item_key);
      s.activeMs = Math.max(s.activeMs, request.active_ms);
      if (request.draft !== null) s.draft = request.draft;
      return { saved: true, active_ms: s.activeMs, break_due: false };
    },
    study_next: async (request) => {
      const { s } = current(request.item_key);
      s.advance();
      return s.turn();
    },
    study_flag: async (request) => {
      current(request.item_key);
      if (request.kind === 'too_easy') {
        return { ok: true, message: 'Marked too easy. This skill will come up a little less often.', attempt_counts: true };
      }
      if (request.kind === 'dispute') {
        return { ok: true, message: 'Logged for review with your exact answer. This attempt will not count.', attempt_counts: false };
      }
      return { ok: true, message: 'Reported. This problem is hidden from every future session.', attempt_counts: false };
    },
    study_undo: async () => {
      const s = session;
      if (!s || s.ended) throw userMessage('No study session is open. Press Start.');
      if (s.held) {
        s.held = null;
        s.tries = 0;
        s.first = null;
        s.lastVerdicts = [];
        s.undoable = false;
        return s.turn('Undone. The problem is back.');
      }
      const last = s.log.at(-1);
      if (!s.undoable || !last) return s.turn('Undo is only available until the next answer is submitted.');
      s.log.pop();
      if (s.undoPlan) {
        s.items = s.undoPlan.items;
        s.setAside = s.undoPlan.setAside;
        s.note = s.undoPlan.note;
        s.undoPlan = null;
      }
      s.index = last.index;
      s.reset();
      s.undoable = false;
      return s.turn('Undone. The problem is back.');
    },
    study_rate_flashcard: async (request) => {
      const { s, item } = current(request.item_key);
      if (item.kind !== 'flashcard') throw userMessage('The item on screen is not a flashcard.');
      const rating = request.rating ?? 3;
      s.log.push({ index: s.index, item, correct: rating >= 2, first: null, rating, active_ms: 0 });
      s.undoable = true;
      return {
        item_key: s.key(),
        outcome: 'recorded',
        verdicts: [],
        message: '',
        solution: null,
        tries_used: 1,
        attempts_allowed: 1,
        rating,
        break_due: false,
        find_error: null,
        can_retry: false,
        first_try_counted: true,
      };
    },
    study_show_solution: async () => {
      throw userMessage('This problem is graded automatically.');
    },
    study_end: async () => {
      const { s } = current();
      if (s.held) s.advance();
      s.ended = true;
      return s.summary();
    },

    course_settings_get: async (courseId) => courseSettings(courseId),
    course_settings_set: async (next) => {
      const stored = settings.get(next.course_id);
      if (!stored) throw userMessage('There is no course with that name.');
      if (!(next.pace_factor >= 0.75 && next.pace_factor <= 1.5)) throw userMessage('The pace must be between 0.75 and 1.5.');
      if (!(next.accuracy_target >= 0.8 && next.accuracy_target <= 0.95)) {
        throw userMessage('The accuracy target must be between 80% and 95%.');
      }
      if (![3, 4, 5].includes(next.target_tier)) throw userMessage('The target tier must be 3, 4 or 5.');
      if (next.growth_band !== 'standard' && next.growth_band !== 'hard') throw userMessage('Choose standard or hard practice.');
      if (next.start && next.end && next.end < next.start) throw userMessage('The end date is before the start date.');
      if (next.aligned && !SECTIONS.some((s) => s.course === next.course_id && s.id === next.aligned?.deck)) {
        throw userMessage('That section is not in this course.');
      }
      settings.set(next.course_id, { ...stored, ...next });
      return courseSettings(next.course_id);
    },
    exam_save: async (exam) => {
      checkExam(exam);
      const saved: Exam = {
        exam_id: exam.exam_id ?? nextExamId,
        course_id: exam.course_id,
        name: exam.name.trim(),
        day: exam.day,
        scope_decks: [...exam.scope_decks],
        target: exam.target ?? null,
        minutes: exam.minutes ?? null,
        problems: exam.problems ?? null,
      };
      if (exam.exam_id === undefined) {
        nextExamId += 1;
        exams = [...exams, saved];
      } else {
        if (!exams.some((e) => e.exam_id === exam.exam_id)) throw userMessage('That exam is no longer there.');
        exams = exams.map((e) => (e.exam_id === exam.exam_id ? saved : e));
      }
      return { ...saved };
    },
    exam_delete: async (examId) => {
      if (!exams.some((e) => e.exam_id === examId)) throw userMessage('That exam is no longer there.');
      exams = exams.filter((e) => e.exam_id !== examId);
    },

    skills_get: async (courseId) => {
      if (!settings.has(courseId)) throw userMessage('There is no course with that name.');
      return { course_id: courseId, day: today, skills: sampleSkills(courseId, today, session?.setAside ?? []) };
    },

    model_get: async () => clone(model),
    model_refit: async () => {
      versions += 1;
      const first = model.last_refit === null;
      const report: RefitReport = {
        at: Date.now(),
        attempts: model.attempts,
        adopted: first,
        p_value: first ? 0.03 : 0.41,
        blocks: [
          { name: 'accuracy', current: 0.512, candidate: first ? 0.497 : 0.511, p_value: first ? 0.03 : 0.41, adopted: first },
          { name: 'time', current: 0.94, candidate: 0.951, p_value: 0.62, adopted: false },
        ],
      };
      model = {
        ...model,
        last_refit: report,
        ...(first
          ? {
              version: `refit-${versions}`,
              source: 'refit' as const,
              created_at: report.at,
              params: { ...model.params, slip: 0.031, calib_a: [0.12, 0.05, 0, -0.08, -0.15], calib_b: 1.08 },
            }
          : {}),
      };
      return clone(report);
    },
    model_reset: async () => {
      versions += 1;
      model = { ...model, version: `reset-${versions}`, source: 'reset', created_at: Date.now(), params: { ...PRIOR_PARAMS } };
      return clone(model);
    },
  };
  // A flashcard rated with study_rate_flashcard is logged at once; study_next must not log it again.
  const next = api.study_next;
  api.study_next = async (request) => {
    const s = session;
    if (s?.item?.kind === 'flashcard') {
      current(request.item_key);
      s.index += 1;
      s.reset();
      return s.turn();
    }
    return next(request);
  };
  mocks.add(api);
  return api;
}
