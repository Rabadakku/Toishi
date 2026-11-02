import type { BridgeApi } from './bridge';
import { sampleItems, type PartKey, type SampleItem } from './sample-problems';
import {
  TEXT_SIZE_DEFAULT,
  type AnswerPreview,
  type AttemptResult,
  type Library,
  type PartAnswer,
  type PartVerdictView,
  type Preferences,
  type ProfileState,
  type SectionState,
  type SolutionView,
  type Summary,
  type Turn,
} from './types';

/**
 * In-page stand-in for the Python bridge (page tests, `npm run dev`, a plain browser).
 * It grades by comparing normalised text (the real checker is SymPy-based and lives in
 * core/), but it follows the same contract as app/api.py: item keys, attempts, invalid
 * answers that cost nothing, answers held on the verdict screen until Continue, undo.
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

// --- the session -----------------------------------------------------------

interface Held {
  result: AttemptResult;
  correct: boolean;
  /** A miss submitted sure (not a give-up or the last hint): a confident error once graded. */
  sure: boolean;
}

interface Logged {
  index: number;
  item: SampleItem;
  correct: boolean;
  rating: number | null;
  active_ms: number;
}

const ATTEMPTS = 2;
const SECTIONS: { id: string; title: string; unit: string }[] = [
  { id: 'Sample Calculus::Derivatives::Power rule', title: 'Power rule', unit: 'Sample Calculus::Derivatives' },
  { id: 'Sample Calculus::Derivatives::Chain rule', title: 'Chain rule', unit: 'Sample Calculus::Derivatives' },
  { id: 'Sample Calculus::Applications::Shape of a graph', title: 'Shape of a graph', unit: 'Sample Calculus::Applications' },
];

class MockSession {
  items = sampleItems();
  index = 0;
  tries = 0;
  hints = 0;
  /** The last wrong try's verdicts: still "Your answer" after a give-up. */
  lastVerdicts: PartVerdictView[] = [];
  held: Held | null = null;
  log: Logged[] = [];
  /** The last answer can be undone until the next one is submitted. */
  undoable = false;
  ended = false;
  activeMs = 0;
  draft: string | null = null;

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

  turn(message = ''): Turn {
    const item = this.item;
    const base = { session_id: 1, message, break_due: false, lighter: false, mode: 'daily' };
    if (!item || this.ended) {
      return { ...base, type: 'summary', problem: null, progress: null, result: null, summary: this.summary() };
    }
    const done = this.log.filter((l) => l.item.kind === 'problem');
    return {
      ...base,
      type: 'problem',
      problem: {
        item_key: this.key(),
        kind: item.kind,
        card: item.card,
        reason: item.reason,
        attempts_allowed: item.kind === 'problem' ? ATTEMPTS : 1,
        tries_used: this.tries,
        hints_shown: item.hints.slice(0, this.hints),
        draft: this.draft,
        active_ms: this.activeMs,
        target_ms: null,
        untimed: false,
        practice_test: false,
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
      needs_diagnosis: !correct && item.kind === 'problem',
      // Like the app: only the graded answer's recorded effect, so never before grading.
      confident_error: false,
      can_mark_too_easy: correct && this.tries <= 1 && this.hints === 0 && !unsure,
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
    findError: AttemptResult['find_error'] = null,
  ): AttemptResult {
    const result: AttemptResult = {
      find_error: findError,
      item_key: this.key(),
      outcome: correct ? 'correct' : 'incorrect',
      verdicts,
      message: correct ? '' : 'Here is the full solution.',
      solution: { ...this.solution(item, correct, unsure, activeMs), needs_diagnosis: !correct && item.kind === 'problem' && !findError },
      tries_used: this.tries,
      attempts_allowed: ATTEMPTS,
      rating: null,
      break_due: false,
    };
    this.held = { result, correct, sure: !correct && !unsure && this.hints < item.hints.length };
    this.undoable = true;
    return result;
  }

  /** Continue: log the held answer, move on. */
  advance(): void {
    const item = this.item;
    if (item && this.held) {
      this.log.push({ index: this.index, item, correct: this.held.correct, rating: null, active_ms: this.held.result.solution?.active_ms ?? 0 });
    } else if (item && item.kind === 'example') {
      this.log.push({ index: this.index, item, correct: true, rating: null, active_ms: 0 });
    }
    this.index += 1;
    this.tries = 0;
    this.hints = 0;
    this.lastVerdicts = [];
    this.held = null;
    this.activeMs = 0;
    this.draft = null;
  }
}

function userMessage(text: string): Error {
  const error = new Error(text);
  error.name = 'UserMessage';
  return error;
}

/**
 * Test hook, mock bridge only: `?bridge=mock&prompt=...` replaces the first problem's
 * Markdown, so tests can feed the renderer hostile input. Never reachable in the real app.
 */
function promptOverride(): string | null {
  const params = new URLSearchParams(window.location.search);
  return params.get('bridge') === 'mock' ? params.get('prompt') : null;
}

const mocks = new WeakSet<object>();

/** True for an api made by createMockApi (the page then says it shows sample problems). */
export function isMockApi(api: object): boolean {
  return mocks.has(api);
}

/** The whole bridge, in memory, with sample problems. */
export function createMockApi(): BridgeApi {
  const override = promptOverride();
  let session: MockSession | null = null;
  let preferences: Preferences = { theme: 'auto', text_size: TEXT_SIZE_DEFAULT };
  const states = new Map<string, SectionState>(SECTIONS.map((s, i) => [s.id, i === 0 ? 'learning' : 'off']));
  const profile: ProfileState = { profile: { id: 'sample', name: 'Sample' }, error: null, warnings: [] };

  function open(): MockSession {
    if (!session) {
      session = new MockSession();
      const first = session.items[0];
      if (override !== null && first) first.card = { ...first.card, prompt_md: override };
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

  function library(): Library {
    const units = [...new Set(SECTIONS.map((s) => s.unit))].map((unit) => {
      const sections = SECTIONS.filter((s) => s.unit === unit).map((s) => ({
        id: s.id,
        title: s.title,
        state: states.get(s.id) ?? 'off',
        skills: 3,
        textbook_ref: null,
        // A one-problem skill, as imported or user-made decks often have (ENG-2).
        small_pool_skills: s.title === 'Shape of a graph' ? ['Concavity'] : [],
      }));
      const set = new Set(sections.map((s) => s.state));
      return { id: unit, title: unit.split('::')[1] ?? unit, state: set.size === 1 ? [...set][0]! : ('mixed' as const), sections };
    });
    const set = new Set(units.map((u) => u.state));
    return {
      courses: [{ id: 'Sample Calculus', title: 'Sample Calculus', state: set.size === 1 ? [...set][0]! : 'mixed', units }],
    };
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
      for (const s of SECTIONS) if (s.id === id || s.unit === id || id === 'Sample Calculus') states.set(s.id, state);
      return library();
    },

    library_card_media: async () => ({ files: {} }),

    study_today: async () => {
      const s = session;
      const open = !!s && !s.ended;
      return {
        day: 'today',
        problems: 6,
        minutes: 15,
        flashcards: 1,
        courses: [{ course_id: 'Sample Calculus', title: 'Sample Calculus', problems: 6, minutes: 15 }],
        exams: [{ exam_id: 1, name: 'Midterm', course_id: 'Sample Calculus', days_left: 9, practice_test: true }],
        proposals: [],
        session_open: open,
        done_today: !!s && s.ended,
        vacation: false,
        extra_practice_available: true,
      };
    },
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
          final: graded.correct || s.tries + 1 >= ATTEMPTS,
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
          attempts_allowed: ATTEMPTS,
          rating: null,
          break_due: false,
          find_error: null,
        };
      }
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
        return s.hold(item, ok, verdicts, request.confidence === 'unsure', request.timing.active_ms, fe);
      }
      const correct = verdicts.every((v) => v.status === 'correct');
      if (!correct && s.tries < ATTEMPTS) {
        s.undoable = false;
        s.lastVerdicts = verdicts;
        return {
          item_key: s.key(),
          outcome: 'retry',
          verdicts,
          message: 'Not quite.',
          solution: null,
          tries_used: s.tries,
          attempts_allowed: ATTEMPTS,
          rating: null,
          break_due: false,
          find_error: null,
        };
      }
      return s.hold(item, correct, verdicts, request.confidence === 'unsure', request.timing.active_ms);
    },
    study_give_up: async (request) => {
      const { s, item } = current(request.item_key);
      if (s.held) throw userMessage('This problem is already answered; continue.');
      s.tries += 1;
      return s.hold(item, false, s.lastVerdicts, true, request.timing.active_ms);
    },
    study_hint: async (request) => {
      const { s, item } = current(request.item_key);
      const text = item.hints[s.hints];
      if (text === undefined) throw userMessage('No more hints for this problem.');
      s.hints += 1;
      const last = s.hints === item.hints.length;
      return { item_key: s.key(), index: s.hints, total: item.hints.length, text, rating_effect: last ? 'again' : 'hard' };
    },
    study_tick: async (request) => {
      const { s } = current(request.item_key);
      s.activeMs = Math.max(s.activeMs, request.active_ms);
      if (request.draft !== null) s.draft = request.draft;
      return { saved: true, active_ms: s.activeMs, break_due: false };
    },
    study_diagnose: async (request) => {
      const { s, item } = current(request.item_key);
      if (!s.held || s.held.correct) throw userMessage('There is no missed answer to diagnose.');
      const skill = item.steps.find((st) => request.choice === 'step' && st.number === request.step)?.skill_name;
      const follow_up =
        request.choice === 'step' && request.step !== 0
          ? `A quick check on ${skill ?? 'that step'} comes in a few problems.`
          : request.choice === 'step' || request.choice === 'setup'
            ? "A worked example comes before this skill's next problem."
            : request.choice === 'slip' || request.choice === 'misread'
              ? 'Counted as a slip: the review is recorded as Hard.'
              : 'A fresh problem on this skill comes later.';
      const sure = s.held.sure && request.choice !== 'setup' && !(request.choice === 'step' && request.step === 0);
      return {
        item_key: s.key(),
        choice: request.choice,
        follow_up: sure ? `${follow_up} You submitted it as sure, so it comes back tomorrow for a second look.` : follow_up,
        rating: 1,
        slip_accepted: false,
        checks: [],
      };
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
        s.hints = 0;
        s.lastVerdicts = [];
        s.undoable = false;
        return s.turn('Undone. The problem is back.');
      }
      const last = s.log.at(-1);
      if (!s.undoable || !last) return s.turn('Undo is only available until the next answer is submitted.');
      s.log.pop();
      s.index = last.index;
      s.tries = 0;
      s.hints = 0;
      s.undoable = false;
      return s.turn('Undone. The problem is back.');
    },
    study_set_lighter: async () => current().s.turn(),
    study_rate_flashcard: async (request) => {
      const { s, item } = current(request.item_key);
      if (item.kind !== 'flashcard') throw userMessage('The item on screen is not a flashcard.');
      const rating = request.rating ?? 3;
      s.log.push({ index: s.index, item, correct: rating >= 2, rating, active_ms: 0 });
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
  };
  // A flashcard rated with study_rate_flashcard is logged at once; study_next must not log it again.
  const next = api.study_next;
  api.study_next = async (request) => {
    const s = session;
    if (s?.item?.kind === 'flashcard') {
      current(request.item_key);
      s.index += 1;
      s.tries = 0;
      s.hints = 0;
      s.activeMs = 0;
      s.draft = null;
      return s.turn();
    }
    return next(request);
  };
  mocks.add(api);
  return api;
}
