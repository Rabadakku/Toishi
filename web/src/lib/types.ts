/**
 * Payload types of the Python bridge (app/api.py), the contract between this page and
 * Python. The study payloads mirror core/queue/views.py field for field: app/api.py returns
 * `core.queue.to_dict` of the StudyService views unchanged.
 *
 * Rules both sides follow:
 * - JSON only; field names are snake_case (they are Python dict keys).
 * - Every time is milliseconds (`*_ms`); the page formats them.
 * - The item on screen is named by its `item_key` (a plan item), never by a card id.
 * - Text fields ending in `_md` use the card format's Markdown with `\( \)` and `\[ \]`
 *   math, images and tables. The page renders them through KaTeX, never as raw HTML.
 * - Nothing shown before an answer names the problem's section or skill (Study screen 7):
 *   skill names appear only in the solution, the summary and the library.
 */

// ---------------------------------------------------------------------------
// The item on screen (core.queue.views.ProblemView)
// ---------------------------------------------------------------------------

/** How an answer is entered and checked (card-format: Answer types). */
export type AnswerType =
  | 'number'
  | 'expression'
  | 'equation'
  | 'antiderivative'
  | 'set'
  | 'list'
  | 'interval'
  | 'point'
  | 'vector'
  | 'matrix'
  | 'choice'
  | 'truefalse'
  | 'text'
  | 'quantity'
  | 'self';

/** What the card is. */
export type CardKind = 'problem' | 'example' | 'flashcard' | 'cloze' | 'find-error' | 'method';

/** What the session item is: problems are graded; examples are read; flashcards are rated. */
export type ItemKind = 'problem' | 'example' | 'flashcard';

/** Why the item is here (spec: Reason tags). Flashcards use 'review' with label "Flashcard". */
export type ReasonTag = 'review' | 'relearn' | 'new-skill' | 'check' | 'exam-prep' | 'redo' | 'stretch';

/** The small tag at the top of the study screen and the text behind "Why is this here?". */
export interface Reason {
  tag: ReasonTag;
  /** "Review", "Check", "New skill": a word or two, no section names. */
  label: string;
  /** The "Why is this here?" sentence (plain text). */
  why: string;
}

/** One option of a choice answer; it is answered by its 1-based number. */
export interface ChoiceView {
  /** 0-based position. */
  index: number;
  text_md: string;
}

/** One answer box. A single-box card has one part with `label` null. */
export interface PartView {
  label: string | null;
  prompt_md: string | null;
  answer_type: AnswerType;
  choices: ChoiceView[];
  /** A choice box with several right options: select all that apply. */
  multiple?: boolean;
}

/** The card behind the item. */
export interface CardView {
  id: string;
  rev: number;
  kind: CardKind;
  /** The question (or a flashcard's front, a cloze card's text). */
  prompt_md: string;
  parts: PartView[];
  hint_count: number;
  calculator: boolean;
  /** 'radians' unless the card says 'degrees'. */
  angles: string;
  plot: string | null;
  /** The student grades it against the solution (answer-type self). */
  self_graded: boolean;
  /** A flashcard's back. */
  back_md: string | null;
  /** A worked example's solution (examples show it at once). */
  solution_md: string | null;
  /** Find-the-error: another student's numbered steps (no skill names). */
  shown_work: StepView[];
  /** Find-the-error: why the step is wrong, three or four options, one right. */
  reasons: ChoiceView[];
  /** Find-the-error, highlighted version: the wrong step is given ("Step 3 is wrong. Why?"). */
  error_step: number | null;
  /** Cloze: the blank asked (c1 is 1). The front and back come rendered. */
  cloze: number | null;
  /** A flashcard with an answer: the student types it and it is graded automatically. */
  type_answer: boolean;
}

/** The item on screen (Turn.problem). */
export interface ProblemView {
  item_key: string;
  kind: ItemKind;
  card: CardView;
  reason: Reason;
  attempts_allowed: number;
  tries_used: number;
  /** Hints already revealed (a resumed problem shows them again). */
  hints_shown: string[];
  /** What was typed before a quit or reload (study_tick), opaque to Python. */
  draft: string | null;
  /** Active time already counted for this item (a resumed problem continues from it). */
  active_ms: number;
  /** Null while answering: the target shows only after submitting. */
  target_ms: number | null;
  untimed: boolean;
  practice_test: boolean;
}

/** "7 of 20" and the running tally. */
export interface Progress {
  position: number;
  total: number;
  answered: number;
  correct: number;
}

// ---------------------------------------------------------------------------
// Answering (requests)
// ---------------------------------------------------------------------------

/** 'mathlive' for LaTeX from the math field, 'text' for plain-text mode and choices. */
export type AnswerSource = 'text' | 'mathlive';

/** What the student entered in one box. Choices are their 1-based numbers ("1, 3"). */
export interface PartAnswer {
  part: string | null;
  value: string;
  source: AnswerSource;
}

/** What the page measured (TIME-1 to TIME-5). Python bounds it by the wall clock. */
export interface TimingReport {
  /** All active time on this item so far (pauses excluded), including a resumed part. */
  active_ms: number;
  /** This attempt: shown (or retried) until the first keystroke in an answer box. */
  solve_ms: number | null;
  /** This attempt: first keystroke until submit. */
  entry_ms: number | null;
  paused_ms: number;
  pause_count: number;
  longest_pause_ms: number;
  /** The Mac slept during the attempt (left out of speed baselines, TIME-5). */
  after_wake: boolean;
  /** The "Still working?" note timed out and the time was trimmed back (TIME-3). */
  idle_trimmed: boolean;
}

/** Enter submits "sure"; Shift+Enter submits "unsure". */
export type Confidence = 'sure' | 'unsure';

/** Self-grading: matched the solution, a minor slip, or didn't get it. */
export type SelfGrade = 'matched' | 'minor-slip' | 'missed';

/** study_submit. `item_key` guards against a stale page. */
export interface SubmitRequest {
  item_key: string;
  answers: PartAnswer[];
  confidence: Confidence;
  guessed?: boolean;
  self_grade?: SelfGrade | null;
  /** Self-graded with a rubric: how many of its steps the student's work matched. */
  rubric_ticked?: number | null;
  /** Find-the-error: the step picked as wrong (not needed when it is highlighted). */
  error_step?: number | null;
  /** Find-the-error: the index of the reason picked. */
  reason?: number | null;
  timing: TimingReport;
}

/** study_give_up. */
export interface GiveUpRequest {
  item_key: string;
  timing: TimingReport;
}

/** study_read_answer: the live preview of one box. */
export interface ReadAnswerRequest {
  item_key: string;
  part: string | null;
  value: string;
  source: AnswerSource;
}

/** The "We read your answer as ..." preview (core.grader.Preview). */
export interface AnswerPreview {
  /** Parsed and the right shape. False with a message: a syntax or shape error. */
  ok: boolean;
  /** The parsed answer as LaTeX with multiplication made explicit. */
  read_as_latex: string | null;
  message: string;
  /** Reading notes ("Read sinx as sin(x)"). */
  hints: string[];
}

/** A request about the item on screen (hint, next, flag ...). */
export interface ItemRequest {
  item_key: string;
}

/** The "What went wrong?" choices. 'step' needs `step` (0 is "set up"). */
export type WentWrongChoice = 'step' | 'setup' | 'slip' | 'misread' | 'other-method' | 'cant-tell';

/** study_diagnose. */
export interface DiagnoseRequest {
  item_key: string;
  choice: WentWrongChoice;
  step?: number | null;
}

/** Buttons after grading: E too easy, D dispute ("I was right"), R report. */
export type FlagKind = 'too_easy' | 'dispute' | 'report' | 'flag' | 'suspend';

/** study_flag. */
export interface FlagRequest {
  item_key: string;
  kind: FlagKind;
  note?: string | null;
}

/** study_rate_flashcard: a rating 1-4 (Again, Hard, Good, Easy) or a typed answer. */
export interface FlashcardRequest {
  item_key: string;
  rating?: 1 | 2 | 3 | 4 | null;
  answer?: string | null;
  source?: AnswerSource;
  timing?: TimingReport;
}

/** study_tick: the active time so far and the typed draft, saved for a resume (QUE-16). */
export interface TickRequest {
  item_key: string;
  active_ms: number;
  draft: string | null;
}

/** study_start: begin today's session (or resume it), or another kind of session. */
export interface StartRequest {
  mode?: 'daily' | 'lighter' | 'focused' | 'extra' | 'practice-test';
  /** An Untimed session (TIME-6); null: the profile's default. */
  untimed?: boolean | null;
  count?: number | null;
  section_id?: string | null;
  skill_id?: string | null;
  weak_spots?: boolean;
  exam_id?: number | null;
  timed?: boolean;
}

// ---------------------------------------------------------------------------
// Results
// ---------------------------------------------------------------------------

/** One box's verdict. 'invalid' (syntax or shape) never counts as an attempt. */
export type VerdictStatus = 'correct' | 'incorrect' | 'invalid' | 'undecidable' | 'unsupported';

/** The verdict for one box. */
export interface PartVerdictView {
  part: string | null;
  status: VerdictStatus;
  /** LaTeX: the answer as read. */
  read_as: string | null;
  /** The checker's message (an invalid answer's reason). */
  message: string;
  /** A known wrong answer matched: its feedback (Markdown). */
  feedback: string | null;
  /** ... and the solution step it comes from (@step). */
  wrong_step?: number | null;
  /** This box is settled (right, or out of tries); it is not checked again. */
  final: boolean;
  tries_used: number;
}

/** One numbered, skill-tagged step of a worked solution (Step 0 is set-up). */
export interface StepView {
  number: number;
  skill_id: string | null;
  skill_name: string | null;
  label: string;
  body_md: string;
}

/** Everything shown once an item is finished. */
export interface SolutionView {
  skill_id: string | null;
  skill_name: string | null;
  /** The correct answer. */
  answer_md: string | null;
  /** A solution without numbered steps. */
  solution_md: string | null;
  steps: StepView[];
  alternative_md: string | null;
  active_ms: number | null;
  target_ms: number | null;
  /** "3:40 · target 4:00"; null in Untimed sessions. */
  time_text: string | null;
  /** Show "What went wrong?" (after a miss). */
  needs_diagnosis: boolean;
  /** Missed while marked "sure". */
  confident_error: boolean;
  /** Offer "Too easy" (a clean first-try success). */
  can_mark_too_easy: boolean;
  textbook_ref: string | null;
  /** Self-graded: the checklist to tick. */
  rubric: string[];
  /** Find-the-error: the shown work, set beside the correct solution. */
  shown_work: StepView[];
  /** "What went wrong?": the step to preselect (a matched known wrong answer's @step). */
  preselect_step?: number | null;
}

/** How a find-the-error answer went: the step, the reason and the corrected value. */
export interface FindErrorView {
  error_step: number | null;
  /** Index of the right reason. */
  right_reason: number | null;
  step_ok: boolean;
  reason_ok: boolean;
  value_ok: boolean;
}

/**
 * retry: "Not quite", try again. invalid: fix the form (not an attempt). correct /
 * incorrect: finished, `solution` set. self-grade: the checker can't decide; the student
 * grades against `solution`. recorded: a flashcard or practice-test answer was saved.
 */
export type Outcome = 'retry' | 'correct' | 'incorrect' | 'invalid' | 'self-grade' | 'recorded';

/** The result of study_submit, study_give_up and study_rate_flashcard. */
export interface AttemptResult {
  item_key: string;
  outcome: Outcome;
  verdicts: PartVerdictView[];
  message: string;
  solution: SolutionView | null;
  tries_used: number;
  attempts_allowed: number;
  /** Flashcards: the rating recorded (1-4). */
  rating: number | null;
  /** A break reminder is due (50 minutes of active time by default). */
  break_due: boolean;
  find_error: FindErrorView | null;
}

/** One rung of the hint ladder. Any hint caps the rating at Hard; the last counts as Again. */
export interface HintReveal {
  item_key: string;
  /** 1-based. */
  index: number;
  total: number;
  text: string;
  rating_effect: 'hard' | 'again';
}

/** What the app did with a "What went wrong?" pick. */
export interface Diagnosis {
  item_key: string;
  choice: string;
  /** One quiet line about what comes next. */
  follow_up: string;
  rating: number | null;
  slip_accepted: boolean;
  /** Skills a quick check was planned on. */
  checks: string[];
}

/** The outcome of a flag. */
export interface FlagResult {
  ok: boolean;
  message: string;
  /** False when the attempt no longer counts (dispute, report). */
  attempt_counts: boolean;
}

/** study_tick's answer. */
export interface Tick {
  saved: boolean;
  active_ms: number;
  break_due: boolean;
}

// ---------------------------------------------------------------------------
// Home, forecast and the summary
// ---------------------------------------------------------------------------

/** One course's share of a day. */
export interface CourseLine {
  course_id: string;
  title: string;
  problems: number;
  minutes: number;
}

/** A day's problems and minutes (tomorrow on the summary). */
export interface Forecast {
  day: string;
  problems: number;
  minutes: number;
  courses: CourseLine[];
}

/** An exam countdown; `practice_test` once it is within 21 days. */
export interface ExamLine {
  exam_id: number | null;
  name: string;
  course_id: string | null;
  days_left: number;
  practice_test: boolean;
}

/** A suggestion the app makes instead of acting silently (QUE-8, QUE-13). */
export interface Proposal {
  kind: 'overload' | 'backlog';
  message: string;
  options: string[];
}

/** Home: "Today: 20 problems, about 55 minutes". Never an overdue count (QUE-7). */
export interface TodayView {
  day: string;
  problems: number;
  minutes: number;
  flashcards: number;
  courses: CourseLine[];
  exams: ExamLine[];
  proposals: Proposal[];
  session_open: boolean;
  done_today: boolean;
  vacation: boolean;
  extra_practice_available: boolean;
  /** Leech flashcards, not shown until rewritten. */
  flashcards_to_rewrite?: number;
}

/** A miss listed on the summary, with its tag. */
export interface MissLine {
  item_key: string;
  card_id: string | null;
  skill_id: string | null;
  skill_name: string;
  tag: string;
  label: string;
}

/** One practice-test problem's result. */
export interface TestLine {
  item_key: string;
  card_id: string | null;
  skill_name: string;
  answered: boolean;
  correct: boolean;
  your_answer: string | null;
  /** The review it counted as (null: not graded). */
  rating: number | null;
}

/** A practice test's result, given at the end like a real exam. */
export interface TestResult {
  exam_id: number | null;
  answered: number;
  correct: number;
  total: number;
  timed: boolean;
  time_up: boolean;
  lines: TestLine[];
  /** How unanswered problems counted: as misses (again) or not at all (skip). */
  unanswered: 'again' | 'skip';
  /** The time allowed when timed. */
  limit_ms: number | null;
}

/** The card shown when a session ends. */
export interface Summary {
  mode: string;
  problems: number;
  correct: number;
  missed: number;
  active_ms: number;
  misses: MissLine[];
  /** Skills learned in this session. */
  learned: string[];
  flashcards: number;
  forecast: Forecast;
  extra_practice_available: boolean;
  practice_tests: ExamLine[];
  test: TestResult | null;
  /** Learning-phase problems ready later today (a new skill's block goes on). */
  ready_today: number;
}

/** What the study screen shows next: an item (maybe already answered, after a resume), the summary, or nothing to do. */
export interface Turn {
  type: 'problem' | 'summary' | 'empty';
  session_id: number | null;
  problem: ProblemView | null;
  progress: Progress | null;
  /** The verdict screen, when resuming after an answer that was not continued from. */
  result: AttemptResult | null;
  summary: Summary | null;
  /** A one-line note ("Undone. The problem is back."). */
  message: string;
  break_due: boolean;
  lighter: boolean;
  mode: string;
}

// ---------------------------------------------------------------------------
// Profile, library, preferences
// ---------------------------------------------------------------------------

/** The open profile. */
export interface Profile {
  id: string;
  name: string;
}

/** profile_get: the open profile, or null on first run (the page asks for a name). */
export interface ProfileState {
  profile: Profile | null;
  /** Why no profile could be opened (in use elsewhere, damaged). */
  error: string | null;
  /** Startup warnings, such as a data folder inside a cloud-synced folder. */
  warnings: string[];
}

/** One verified backup, as the restore screen previews it (BAK-3). */
export interface BackupEntry {
  /** The backup's file name; pass it to restore_backup. */
  id: string;
  /** When it was taken (epoch ms). */
  created_at: number;
  /** periodic, close, manual, pre-migration, pre-import, pre-pack-update, pre-restore. */
  reason: string;
  attempts: number;
  last_attempt_at: number | null;
}

/**
 * restore_list: the profile to restore and its verified backups, newest first. While no
 * profile is open, `profile` is one that could not be opened (show the restore screen).
 */
export interface BackupList {
  profile: Profile | null;
  backups: BackupEntry[];
}

/** A section's state (spec: Library). 'mixed' only on a course or unit (LIB-1). */
export type SectionState = 'off' | 'learning' | 'covered' | 'solid';

/** A section of the course tree. */
export interface LibrarySection {
  id: string;
  title: string;
  state: SectionState;
  skills: number;
  textbook_ref: string | null;
  /** Skills with too few problems for the learning phase's run of correct answers (ENG-2):
   * each is learned after all its problems in a row ("pool too small"). */
  small_pool_skills: string[];
}

/** A unit of the course tree. */
export interface LibraryUnit {
  id: string;
  title: string;
  state: SectionState | 'mixed';
  sections: LibrarySection[];
}

/** A course of the course tree. */
export interface LibraryCourse {
  id: string;
  title: string;
  state: SectionState | 'mixed';
  units: LibraryUnit[];
}

/** library_get: the course tree. */
export interface Library {
  courses: LibraryCourse[];
}

/** library_set_state: a course or unit sets all its sections. */
export interface LibraryStateRequest {
  id: string;
  state: SectionState;
}

/** library_card_media: the media of one card. */
export interface CardMediaRequest {
  card_id: string;
}

/**
 * The media a card's text refers to (ADR-0017): each reference as the card writes it
 * (`pic.png`, `media/graph.svg`, `_anki-nt-....css`) to a URL on this page's own origin
 * (`/media/user/<sha256>.png`, `/media/pack/<pack>/<name>`). References without a stored
 * file are absent.
 */
export interface CardMedia {
  files: Record<string, string>;
}

/** Automatic follows the operating system's light or dark setting. */
export type ThemeChoice = 'auto' | 'day' | 'night';

/** Appearance preferences (prefs_get / prefs_set), kept in the profile. */
export interface Preferences {
  theme: ThemeChoice;
  /** Problem text size in px, 14 to 28; the interface and math scale with it. */
  text_size: number;
}

export const TEXT_SIZE_MIN = 14;
export const TEXT_SIZE_MAX = 28;
export const TEXT_SIZE_DEFAULT = 18;
